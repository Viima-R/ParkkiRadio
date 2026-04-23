#!/usr/bin/env python3
"""
TPMS Subscriber
---------------
Listens to MQTT topic for TPMS sensor messages published by tpms_publisher.py.
For each message it:

  1. Validates that the location_id exists in idapp_location.
  2. Looks up the sensor ID in idapp_carid to determine if the car is known.
  3. Known car  -> upsert idapp_timer on every signal (permit holders stay tracked)
     Unknown car -> first signal = arriving, insert into idapp_timer
                    second signal = leaving, delete from idapp_timer
  4. If a known car is seen at a different location than registered, logs a warning.

Config: /opt/tpms_subscriber/config.env
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
MQTT_PORT   = int(cfg.get("MQTT_PORT", 1883))
MQTT_TOPIC  = cfg.get("MQTT_TOPIC")

DB_HOST     = cfg.get("DB_HOST", "localhost")
DB_PORT     = int(cfg.get("DB_PORT", 5432))
DB_NAME     = cfg.get("DB_NAME", "parkkiradio")
DB_USER     = cfg.get("DB_USER", "tpms_user")
DB_PASSWORD = cfg.get("DB_PASSWORD", "")

# ---------------------------------------------------------------------------
# Database connection (with reconnect)
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
            print(f"[DB] Not available: {e} \u2014 retrying in 5s", file=sys.stderr)
            time.sleep(5)

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def validate_location(cursor, location_id: int) -> bool:
    """Return True if locationID exists in idapp_location."""
    cursor.execute(
        'SELECT 1 FROM idapp_location WHERE "locationID" = %s',
        (location_id,)
    )
    return cursor.fetchone() is not None

def lookup_car(cursor, tpms_id: str):
    """
    Look up tpms_id in idapp_carid.
    Returns (car_id, location) if found, else None.
    car_id is the registered identifier for this sensor.
    location is the varchar description of its registered location (may be None).
    """
    cursor.execute(
        "SELECT car_id, location FROM idapp_carid WHERE car_id = %s",
        (tpms_id,)
    )
    return cursor.fetchone()

def upsert_known_timer(cursor, car_id: str, location_id: int):
    """
    Known car: insert or update timestamp and location on every signal.
    Permit holders stay in idapp_timer as long as they are present.
    car_id truncated to 15 chars to match column type.
    """
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
    """
    Unknown car departure logic:
      - First signal  -> car is arriving, insert into idapp_timer.
      - Second signal -> car is leaving, delete from idapp_timer.
    Returns 'arrived' or 'departed' for logging.
    car_id truncated to 15 chars to match column type.
    """
    car_id = car_id[:15]

    # Check if already present in idapp_timer
    cursor.execute(
        'SELECT 1 FROM idapp_timer WHERE "carID" = %s',
        (car_id,)
    )
    already_present = cursor.fetchone() is not None

    if already_present:
        # Second sighting \u2014 car is leaving, remove it
        cursor.execute(
            'DELETE FROM idapp_timer WHERE "carID" = %s',
            (car_id,)
        )
        return "departed"
    else:
        # First sighting \u2014 car is arriving, record it
        cursor.execute(
            """
            INSERT INTO idapp_timer ("carID", timestamp, overtime, location_id)
            VALUES (%s, NOW(), FALSE, %s)
            """,
            (car_id, location_id)
        )
        return "arrived"

def process_message(payload: dict):
    """Handle one decoded MQTT message."""
    tpms_id     = payload.get("tpms_id")
    location_id = payload.get("location_id")

    if not tpms_id or location_id is None:
        print(f"[SUB] Skipping incomplete message: {payload}", file=sys.stderr)
        return

    # location_id must be an integer (bigint FK to idapp_location)
    try:
        location_id = int(location_id)
    except (ValueError, TypeError):
        print(f"[SUB] Invalid location_id '{location_id}' \u2014 must be integer", file=sys.stderr)
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:

            # 1. Validate location exists
            if not validate_location(cur, location_id):
                print(
                    f"[SUB] location_id {location_id} not found in idapp_location "
                    f"\u2014 skipping sensor {tpms_id}",
                    file=sys.stderr
                )
                return

            # 2. Check if car is known in idapp_carid
            known_row = lookup_car(cur, tpms_id)

            if known_row:
                car_id, registered_location = known_row
                status = "known"
                if registered_location:
                    print(
                        f"[SUB] Known car '{car_id}' registered at "
                        f"'{registered_location}' \u2014 seen at location_id {location_id}"
                    )
            else:
                # Unknown sensor \u2014 use tpms_id as the car_id in idapp_timer
                car_id = tpms_id
                status = "unknown"

            # 3. Write to idapp_timer based on known/unknown status
            if known_row:
                upsert_known_timer(cur, car_id, location_id)
                event = "seen"
            else:
                event = handle_unknown_timer(cur, car_id, location_id)

        conn.commit()
        print(f"[SUB] sensor={tpms_id}  car={car_id}  loc={location_id}  [{status}] [{event}]")

    except Exception as e:
        print(f"[DB] Error processing message: {e}", file=sys.stderr)
        conn.rollback()
        global _conn
        _conn = None

# ---------------------------------------------------------------------------
# MQTT callbacks
# ---------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected to {MQTT_BROKER}:{MQTT_PORT}, subscribing to '{MQTT_TOPIC}'")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[MQTT] Connection failed rc={rc}", file=sys.stderr)

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnected rc={rc} \u2014 will auto-reconnect", file=sys.stderr)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        process_message(payload)
    except json.JSONDecodeError as e:
        print(f"[MQTT] Bad JSON: {e}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("[TPMS Subscriber] Starting...")
    ensure_db()

    client = mqtt.Client()
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            break
        except Exception as e:
            print(f"[MQTT] Cannot connect: {e} \u2014 retrying in 5s", file=sys.stderr)
            time.sleep(5)

    client.loop_forever()

if __name__ == "__main__":
    main()

