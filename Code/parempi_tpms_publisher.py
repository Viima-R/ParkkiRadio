#!/usr/bin/env python3
"""
TPMS Publisher
--------------
Reads live TPMS data from rtl_433 (via subprocess, JSON output mode),
filters to TPMS messages only, and publishes relevant fields to MQTT.

Config is read from /opt/tpms_publisher/config.env
"""

import json
import os
import subprocess
import sys
import time
import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Load config from environment file
# ---------------------------------------------------------------------------
CONFIG_FILE = "/opt/tpms_publisher/config.env"

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

MQTT_BROKER  = cfg.get("MQTT_BROKER")
MQTT_PORT    = int(cfg.get("MQTT_PORT"))
MQTT_TOPIC   = cfg.get("MQTT_TOPIC")
LOCATION_ID  = cfg.get("LOCATION_ID")

# ---------------------------------------------------------------------------
# MQTT setup
# ---------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected to broker {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"[MQTT] Connection failed, rc={rc}", file=sys.stderr)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect

def connect_mqtt():
    while True:
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            mqtt_client.loop_start()
            return
        except Exception as e:
            print(f"[MQTT] Could not connect: {e} — retrying in 5s", file=sys.stderr)
            time.sleep(5)

# ---------------------------------------------------------------------------
# rtl_433 subprocess
# ---------------------------------------------------------------------------
RTL_433_CMD = [
    "rtl_433",
    "-F", "json",       # JSON output
    "-R", "0",          # disable all default decoders
    "-R", "59",         # enable TPMS decoder (protocol 59 = generic TPMS)
    "-M", "time:iso",   # ISO timestamps
]

def start_rtl433():
    """Start rtl_433 as a subprocess, return the process."""
    print(f"[rtl_433] Starting: {' '.join(RTL_433_CMD)}")
    return subprocess.Popen(
        RTL_433_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

# ---------------------------------------------------------------------------
# Message filtering and publishing
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = {"id"}

def process_line(line: str):
    """Parse one JSON line from rtl_433 and publish if it is a TPMS message."""
    line = line.strip()
    if not line:
        return
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return

    # Must have a sensor id to be useful
    if not REQUIRED_FIELDS.issubset(data.keys()):
        return

    # Build the payload — include what is present, skip what is not
    payload = {
        "tpms_id"    : str(data["id"]),
        "location_id": LOCATION_ID,
    }

    msg = json.dumps(payload)
    result = mqtt_client.publish(MQTT_TOPIC, msg)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"[PUB] {msg}")
    else:
        print(f"[PUB] Publish failed rc={result.rc}: {msg}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    connect_mqtt()
    while True:
        proc = start_rtl433()
        try:
            for line in proc.stdout:
                process_line(line)
        except Exception as e:
            print(f"[rtl_433] Stream error: {e}", file=sys.stderr)
        finally:
            proc.terminate()
            proc.wait()

        print("[rtl_433] Process ended — restarting in 3s", file=sys.stderr)
        time.sleep(3)

if __name__ == "__main__":
    main()
