#!/bin/bash
# =============================================================================
# TPMS Publisher - Install Script
# Raspberry Pi / Debian 12 side
# Installs: rtl_433, paho-mqtt, mosquitto, configures and registers systemd service
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================="
echo " TPMS Publisher - Installation"
echo "============================================="
echo ""

# --- Collect configuration interactively ---
read -p "MQTT Broker IP address        : " MQTT_BROKER
read -p "MQTT Port              [8883] : " MQTT_PORT
MQTT_PORT=${MQTT_PORT:-1883}
read -p "MQTT Topic        [tpms/data] : " MQTT_TOPIC
MQTT_TOPIC=${MQTT_TOPIC:-tpms/data}
read -p "Location (this device's location): " LOCATION

echo ""
echo "--- Configuration summary ---"
echo "  MQTT Broker  : $MQTT_BROKER"
echo "  MQTT Port    : $MQTT_PORT"
echo "  MQTT Topic   : $MQTT_TOPIC"
echo "  Location  : $LOCATION"
echo ""
read -p "Proceed with installation? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# --- System packages ---
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

# --- Mosquitto config ---
echo ""
echo "[2/6] Configuring Mosquitto..."
cp "$SCRIPT_DIR/../mosquitto/mosquitto.conf" /etc/mosquitto/mosquitto.conf
systemctl enable mosquitto
systemctl restart mosquitto

# --- Python virtual environment ---
echo ""
echo "[3/6] Setting up Python virtual environment..."
VENV_DIR="/opt/tpms_publisher/venv"
mkdir -p /opt/tpms_publisher
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install paho-mqtt -q

# --- Write config file ---
echo ""
echo "[4/6] Writing configuration..."
cat > /opt/tpms_publisher/config.env <<EOF
MQTT_BROKER=$MQTT_BROKER
MQTT_PORT=$MQTT_PORT
MQTT_TOPIC=$MQTT_TOPIC
LOCATION=$LOCATION
EOF
chmod 600 /opt/tpms_publisher/config.env

# --- Deploy publisher script ---
echo ""
echo "[5/6] Deploying publisher script..."
cp "$SCRIPT_DIR/scripts/tpms_publisher.py" /opt/tpms_publisher/tpms_publisher.py
chmod 755 /opt/tpms_publisher/tpms_publisher.py

# --- Systemd service ---
echo ""
echo "[6/6] Installing systemd service..."
cp "$SCRIPT_DIR/systemd/tpms-publisher.service" /etc/systemd/system/tpms-publisher.service
systemctl daemon-reload
systemctl enable tpms-publisher.service
systemctl restart tpms-publisher.service

echo ""
echo "============================================="
echo " Installation complete!"
echo " Service status:"
systemctl status tpms-publisher.service --no-pager
echo ""
echo " Useful commands:"
echo "   systemctl status tpms-publisher"
echo "   journalctl -u tpms-publisher -f"
echo "   systemctl status mosquitto"
echo "   journalctl -u mosquitto -f"
echo "============================================="
