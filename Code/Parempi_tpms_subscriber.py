#!/usr/bin/env python3
"""
TPMS Subscriber
---------------
Listens to MQTT topic for TPMS sensor messages published by tpms_publisher.py.
"""

import json
import sys
import time
import psycopg2
import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------
CONFIG_FILE = "/opt/tpms_subscriber/config.env"

def load_config(path):
    cfg = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    cfg[key.strip()] = val.strip()
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return cfg

cfg = load_config(CONFIG_FILE)

MQTT_BROKER = cfg.get("MQTT_BROKER")
MQTT_PORT   = int(cfg.get("MQTT_PORT"))
MQTT_TOPIC  = cfg.get("MQTT_TOPIC")
MQTT_USER   = cfg.get("MQTT_USER")
MQTT_PASSWORD = cfg.get("MQTT_PASSWORD")

DB_HOST     = cfg.get("DB_HOST", "localhost")
DB_PORT     = int(cfg.get("DB_PORT", 5432))
DB_NAME     = cfg.get("DB_NAME", "parkkiradio")
DB_USER     = cfg.get("DB_USER", "tpms_user")
DB_PASSWORD = cfg.get("DB_PASSWORD", "")

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------
_conn = None

def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        _conn.autocommit = False
        print(f"[DB] Connected to {DB_HOST}:{DB_PORT}/{DB_NAME}")
    return _conn

def ensure_db():
    while True:
        try:
            get_conn()
            return
        except psycopg2.OperationalError as e:
            print(f"[DB] Not available: {e} — retrying in 5s", file=sys.stderr)
            time.sleep(5)

# ---------------------------------------------------------------------------
# Location lookup (FIX)
# ---------------------------------------------------------------------------
def get_location_id(cursor, location_name: str):
    cursor.execute(
        'SELECT "locationID" FROM idapp_location WHERE name = %s',
        (location_name,)
    )
    row = cursor.fetchone()
    return row[0] if row else None

# ---------------------------------------------------------------------------
# Existing DB logic
# ---------------------------------------------------------------------------
def validate_location(cursor, location_id: int) -> bool:
    cursor.execute(
        'SELECT 1 FROM idapp_location WHERE "locationID" = %s',
        (location_id,)
    )
    return cursor.fetchone() is not None

def lookup_car(cursor, tpms_id: str):
    cursor.execute(
        "SELECT car_id, location FROM idapp_carid WHERE car_id = %s",
        (tpms_id,)
    )
    return cursor.fetchone()

def upsert_known_timer(cursor, car_id: str, location_id: int):
    car_id = car_id[:15]
    cursor.execute(
        """
        INSERT INTO idapp_timer ("carID", timestamp, overtime, location_id)
        VALUES (%s, NOW(), FALSE, %s)
        ON CONFLICT ("carID") DO UPDATE SET
            timestamp   = NOW(),
            location_id = EXCLUDED.location_id
        """,
        (car_id, location_id)
    )

def handle_unknown_timer(cursor, car_id: str, location_id: int) -> str:
    car_id = car_id[:15]

    cursor.execute(
        'SELECT 1 FROM idapp_timer WHERE "carID" = %s',
        (car_id,)
    )
    already_present = cursor.fetchone() is not None

    if already_present:
        cursor.execute(
            'DELETE FROM idapp_timer WHERE "carID" = %s',
            (car_id,)
        )
        return "departed"
    else:
        cursor.execute(
            """
            INSERT INTO idapp_timer ("carID", timestamp, overtime, location_id)
            VALUES (%s, NOW(), FALSE, %s)
            """,
            (car_id, location_id)
        )
        return "arrived"

# ---------------------------------------------------------------------------
# MAIN PROCESSING (FIXED)
# ---------------------------------------------------------------------------
def process_message(payload: dict):
    tpms_id = payload.get("id")           # FIXED
    location_name = payload.get("location")  # FIXED

    if not tpms_id or not location_name:
        print(f"[SUB] Skipping incomplete message: {payload}", file=sys.stderr)
        return

    conn = get_conn()

    try:
        with conn.cursor() as cur:

            # Convert location name → location_id
            location_id = get_location_id(cur, location_name)

            if not location_id:
                print(
                    f"[SUB] Unknown location '{location_name}' — skipping sensor {tpms_id}",
                    file=sys.stderr
                )
                return

            # Check known car
            known_row = lookup_car(cur, tpms_id)

            if known_row:
                car_id, registered_location = known_row
                status = "known"

                if registered_location:
                    print(
                        f"[SUB] Known car '{car_id}' registered at "
                        f"'{registered_location}' — seen at {location_name}"
                    )
            else:
                car_id = tpms_id
                status = "unknown"

            # Write logic
            if known_row:
                upsert_known_timer(cur, car_id, location_id)
                event = "seen"
            else:
                event = handle_unknown_timer(cur, car_id, location_id)

        conn.commit()
        print(f"[SUB] sensor={tpms_id} car={car_id} loc={location_name} [{status}] [{event}]")

    except Exception as e:
        print(f"[DB] Error: {e}", file=sys.stderr)
        conn.rollback()
        global _conn
        _conn = None

# ---------------------------------------------------------------------------
# MQTT
# ---------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected to {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[MQTT] Failed rc={rc}", file=sys.stderr)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        process_message(payload)
    except json.JSONDecodeError as e:
        print(f"[MQTT] Bad JSON: {e}", file=sys.stderr)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("[TPMS Subscriber] Starting...")
    ensure_db()

    client = mqtt.Client()

    # AUTH (FIX)
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            print(f"[MQTT] Retry connect: {e}", file=sys.stderr)
            time.sleep(5)

    client.loop_forever()

if __name__ == "__main__":
    main()