#!/usr/bin/env python3
"""
TPMS Subscriber
---------------
Listens to MQTT topic for TPMS sensor messages published by tpms_publisher.py.
For each message it:

  1. Ensures the location exists in idapp_location.
  2. Looks up the sensor ID in idapp_carid to find car_label and known status.
  3. Upserts a row in idapp_timer:
       - New car  -> insert with first_seen = last_seen = now, is_known = False/True
       - Returning sensor from same session -> update last_seen only
  4. If sensor is in idapp_carid (known/authorized):
       - Sets is_known = TRUE on the timer row.
       - If the known car's registered location differs from the current location,
         logs a warning (cross-location detection — handled downstream by Django).

Config is read from /opt/tpms_subscriber/config.env
"""

import json
import os
import sys
import time
import psycopg2
import psycopg2.extras
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

MQTT_BROKER = cfg.get("MQTT_BROKER", "localhost")
MQTT_PORT   = int(cfg.get("MQTT_PORT", 1883))
MQTT_TOPIC  = cfg.get("MQTT_TOPIC", "tpms/data")

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
    """Block until DB is reachable."""
    while True:
        try:
            get_conn()
            return
        except psycopg2.OperationalError as e:
            print(f"[DB] Not available: {e} — retrying in 5s", file=sys.stderr)
            time.sleep(5)

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def ensure_location(cursor, location_id: str):
    """Insert location if it does not exist yet."""
    cursor.execute(
        """
        INSERT INTO idapp_location (location_id)
        VALUES (%s)
        ON CONFLICT (location_id) DO NOTHING
        """,
        (location_id,)
    )

def lookup_sensor(cursor, tpms_id: str):
    """
    Return (car_label, registered_location_id) if sensor is known, else None.
    """
    cursor.execute(
        "SELECT car_label, location_id FROM idapp_carid WHERE tpms_id = %s",
        (tpms_id,)
    )
    return cursor.fetchone()

def upsert_timer(cursor, car_label: str, location_id: str, is_known: bool):
    """
    Upsert idapp_timer:
      - New car: full insert
      - Existing car: update last_seen (and is_known if it became known)
    """
    cursor.execute(
        """
        INSERT INTO idapp_timer (car_label, location_id, first_seen, last_seen, is_known, overtime)
        VALUES (%s, %s, NOW(), NOW(), %s, FALSE)
        ON CONFLICT (car_label) DO UPDATE SET
            last_seen   = NOW(),
            location_id = EXCLUDED.location_id,
            is_known    = idapp_timer.is_known OR EXCLUDED.is_known
        """,
        (car_label, location_id, is_known)
    )

def process_message(payload: dict):
    """Handle one decoded MQTT message."""
    tpms_id     = payload.get("tpms_id")
    location_id = payload.get("location_id")

    if not tpms_id or not location_id:
        print(f"[SUB] Skipping incomplete message: {payload}", file=sys.stderr)
        return

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 1. Ensure location row exists
            ensure_location(cur, location_id)

            # 2. Check if sensor is registered
            known_row = lookup_sensor(cur, tpms_id)

            if known_row:
                car_label, registered_location = known_row
                is_known = True
                if registered_location and registered_location != location_id:
                    print(
                        f"[WARN] Known car '{car_label}' seen at location "
                        f"'{location_id}' but registered at '{registered_location}'"
                    )
            else:
                # Unknown sensor — use the tpms_id itself as a temporary car_label
                # so it gets tracked. An operator can later promote it in idapp_carid.
                car_label = tpms_id
                is_known  = False

            # 3. Upsert timer
            upsert_timer(cur, car_label, location_id, is_known)

        conn.commit()
        status = "known" if is_known else "unknown"
        print(f"[SUB] sensor={tpms_id}  car={car_label}  loc={location_id}  [{status}]")

    except Exception as e:
        print(f"[DB] Error processing message: {e}", file=sys.stderr)
        conn.rollback()
        # Force reconnect on next message
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
    print(f"[MQTT] Disconnected rc={rc} — will auto-reconnect", file=sys.stderr)

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
            print(f"[MQTT] Cannot connect: {e} — retrying in 5s", file=sys.stderr)
            time.sleep(5)

    client.loop_forever()

if __name__ == "__main__":
    main()
