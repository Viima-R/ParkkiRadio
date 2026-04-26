#!/bin/bash
# =============================================================================
# TPMS Publisher - Self-Contained Install Script
# Raspberry Pi / Debian 12
# Installs: rtl_433, paho-mqtt, mosquitto, configures and registers systemd service
# All required files are embedded in this script — no external dependencies.
# =============================================================================
set -e

# Must run as root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (use sudo)."
    exit 1
fi

echo "============================================="
echo " TPMS Publisher - Installation"
echo "============================================="
echo ""

# --- Collect configuration interactively ---
read -p "MQTT Broker IP address         : " MQTT_BROKER
read -p "MQTT Port               [8883] : " MQTT_PORT
MQTT_PORT=${MQTT_PORT:-8883}
read -p "MQTT Topic         [tpms/data] : " MQTT_TOPIC
MQTT_TOPIC=${MQTT_TOPIC:-tpms/data}
read -p "Location (this device's name)  : " LOCATION
read -p "MQTT User                      : " MQTT_USER
read -s -p "MQTT Password                  : " MQTT_PASSWORD
echo ""

echo ""
echo "--- Configuration summary ---"
echo "  MQTT Broker   : $MQTT_BROKER"
echo "  MQTT Port     : $MQTT_PORT"
echo "  MQTT Topic    : $MQTT_TOPIC"
echo "  Location      : $LOCATION"
echo "  MQTT User     : $MQTT_USER"
echo "  MQTT Password : *********"
echo ""
read -p "Proceed with installation? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

INSTALL_DIR="/opt/tpms_publisher"
VENV_DIR="$INSTALL_DIR/venv"

# =============================================================================
# [1/6] System packages
# =============================================================================
echo ""
echo "[1/6] Installing system packages..."
apt-get update -qq
apt-get install -y \
    rtl-sdr \
    rtl-433 \
    mosquitto \
    mosquitto-clients \
    python3 \
    python3-pip \
    python3-venv

# =============================================================================
# [2/6] Mosquitto configuration
# =============================================================================
echo ""
echo "[2/6] Configuring Mosquitto..."

# Ensure required directories exist
mkdir -p /etc/mosquitto/conf.d
mkdir -p /var/lib/mosquitto
mkdir -p /var/log/mosquitto
chown mosquitto:mosquitto /var/lib/mosquitto /var/log/mosquitto 2>/dev/null || true

# --- Step 1: create the password file BEFORE writing the config that needs it ---
echo "  Creating MQTT credentials..."
mosquitto_passwd -b -c /etc/mosquitto/passwd "$MQTT_USER" "$MQTT_PASSWORD"
chmod 600 /etc/mosquitto/passwd
chown mosquitto:mosquitto /etc/mosquitto/passwd 2>/dev/null || true

# --- Step 2: write main mosquitto.conf ---
cat > /etc/mosquitto/mosquitto.conf <<'MOSQUITTO_CONF'
# Mosquitto configuration for TPMS Publisher
pid_file /run/mosquitto/mosquitto.pid

persistence true
persistence_location /var/lib/mosquitto/

log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

include_dir /etc/mosquitto/conf.d
MOSQUITTO_CONF

# --- Step 3: write the TPMS listener config (note: no single-quotes on heredoc
#     delimiter so $MQTT_PORT is expanded by bash as intended) ---
cat > /etc/mosquitto/conf.d/tpms.conf <<MQTT_CONF
# TPMS listener — local anonymous (used by publisher internally)
listener 1883 127.0.0.1
allow_anonymous true

# TPMS listener — external authenticated
listener ${MQTT_PORT}
allow_anonymous false
password_file /etc/mosquitto/passwd
MQTT_CONF

systemctl enable mosquitto
systemctl restart mosquitto

# Give Mosquitto a moment and confirm it actually came up
sleep 2
if ! systemctl is-active --quiet mosquitto; then
    echo ""
    echo "ERROR: Mosquitto failed to start. Showing journal:"
    journalctl -u mosquitto --no-pager -n 30
    exit 1
fi
echo "  Mosquitto is running."

# =============================================================================
# [3/6] Python virtual environment
# =============================================================================
echo ""
echo "[3/6] Setting up Python virtual environment..."

mkdir -p "$INSTALL_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install paho-mqtt -q

# =============================================================================
# [4/6] Configuration file
# =============================================================================
echo ""
echo "[4/6] Writing configuration..."

cat > "$INSTALL_DIR/config.env" <<CONFIG_ENV
MQTT_BROKER=${MQTT_BROKER}
MQTT_PORT=${MQTT_PORT}
MQTT_TOPIC=${MQTT_TOPIC}
MQTT_USER=${MQTT_USER}
MQTT_PASSWORD=${MQTT_PASSWORD}
LOCATION=${LOCATION}
CONFIG_ENV

chmod 600 "$INSTALL_DIR/config.env"

# =============================================================================
# [5/6] Publisher Python script
# =============================================================================
echo ""
echo "[5/6] Deploying publisher script..."

cat > "$INSTALL_DIR/tpms_publisher.py" <<'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
TPMS Publisher
Listens to rtl_433 output and publishes TPMS sensor data via MQTT.
"""

import os
import json
import subprocess
import sys
import time
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/var/log/tpms_publisher.log"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (loaded from config.env via systemd EnvironmentFile)
# ---------------------------------------------------------------------------
MQTT_BROKER   = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT     = int(os.environ.get("MQTT_PORT", 8883))
MQTT_TOPIC    = os.environ.get("MQTT_TOPIC", "tpms/data")
MQTT_USER     = os.environ.get("MQTT_USER", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
LOCATION      = os.environ.get("LOCATION", "unknown")

# ---------------------------------------------------------------------------
# MQTT helpers
# ---------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to MQTT broker %s:%d", MQTT_BROKER, MQTT_PORT)
    else:
        log.error("MQTT connection failed (rc=%d)", rc)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        log.warning("Unexpected MQTT disconnect (rc=%d); will reconnect...", rc)

def build_mqtt_client() -> mqtt.Client:
    client = mqtt.Client()
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    return client

def connect_with_retry(client: mqtt.Client, retries: int = 10, delay: int = 5):
    for attempt in range(1, retries + 1):
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_start()
            return
        except Exception as exc:
            log.warning("MQTT connect attempt %d/%d failed: %s", attempt, retries, exc)
            time.sleep(delay)
    log.error("Could not connect to MQTT broker after %d attempts. Exiting.", retries)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    log.info("TPMS Publisher starting (location=%s, broker=%s:%d, topic=%s)",
             LOCATION, MQTT_BROKER, MQTT_PORT, MQTT_TOPIC)

    client = build_mqtt_client()
    connect_with_retry(client)

    rtl_cmd = [
        "rtl_433",
        "-F", "json",       # JSON output
        "-R", "161",        # TPMS protocol (adjust if needed)
        "-M", "utc",
    ]

    log.info("Starting rtl_433: %s", " ".join(rtl_cmd))

    while True:
        try:
            proc = subprocess.Popen(
                rtl_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Enrich with metadata
                payload["location"]  = LOCATION
                payload["publisher_ts"] = datetime.utcnow().isoformat() + "Z"

                topic = f"{MQTT_TOPIC}/{LOCATION}"
                client.publish(topic, json.dumps(payload), qos=1)
                log.info("Published: %s", json.dumps(payload))

            proc.wait()
            log.warning("rtl_433 exited (rc=%d); restarting in 5 s...", proc.returncode)
            time.sleep(5)

        except Exception as exc:
            log.error("Unexpected error: %s; restarting in 10 s...", exc)
            time.sleep(10)

if __name__ == "__main__":
    main()
PYTHON_SCRIPT

chmod 755 "$INSTALL_DIR/tpms_publisher.py"

# =============================================================================
# [6/6] Systemd service
# =============================================================================
echo ""
echo "[6/6] Installing systemd service..."

cat > /etc/systemd/system/tpms-publisher.service <<SERVICE_UNIT
[Unit]
Description=TPMS Publisher (rtl_433 -> MQTT)
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=root
EnvironmentFile=${INSTALL_DIR}/config.env
ExecStart=${VENV_DIR}/bin/python3 ${INSTALL_DIR}/tpms_publisher.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_UNIT

systemctl daemon-reload
systemctl enable tpms-publisher.service
systemctl restart tpms-publisher.service

# =============================================================================
# Done
# =============================================================================
echo ""
echo "============================================="
echo " Installation complete!"
echo ""
echo " Service status:"
systemctl status tpms-publisher.service --no-pager
echo ""
echo " Useful commands:"
echo "   systemctl status tpms-publisher"
echo "   journalctl -u tpms-publisher -f"
echo "   systemctl status mosquitto"
echo "   journalctl -u mosquitto -f"
echo "   tail -f /var/log/tpms_publisher.log"
echo "============================================="
