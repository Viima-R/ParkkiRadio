#!/bin/bash
# =============================================================================
# TPMS Subscriber - Install Script
# Database server side (Debian 12)
# Installs: paho-mqtt, psycopg2, mosquitto, applies DB schema,
#           registers systemd service
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================="
echo " TPMS Subscriber - Installation"
echo "============================================="
echo ""

# --- Collect configuration interactively ---
read -p "MQTT Broker IP address        : " MQTT_BROKER
read -p "MQTT Port              [1883] : " MQTT_PORT
MQTT_PORT=${MQTT_PORT:-1883}
read -p "MQTT Topic        [tpms/data] : " MQTT_TOPIC
MQTT_TOPIC=${MQTT_TOPIC:-tpms/data}
echo ""
read -p "PostgreSQL host      [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}
read -p "PostgreSQL port          [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}
read -p "PostgreSQL database [parkkiradio]: " DB_NAME
DB_NAME=${DB_NAME:-parkkiradio}
read -p "PostgreSQL user      [tpms_user]: " DB_USER
DB_USER=${DB_USER:-tpms_user}
read -s -p "PostgreSQL password           : " DB_PASSWORD
echo ""
echo ""

echo "--- Configuration summary ---"
echo "  MQTT Broker  : $MQTT_BROKER"
echo "  MQTT Port    : $MQTT_PORT"
echo "  MQTT Topic   : $MQTT_TOPIC"
echo "  DB Host      : $DB_HOST:$DB_PORT"
echo "  DB Name      : $DB_NAME"
echo "  DB User      : $DB_USER"
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
    mosquitto \
    mosquitto-clients \
    python3 \
    python3-pip \
    python3-venv \
    libpq-dev \
    postgresql-client

# --- Mosquitto config ---
echo ""
echo "[2/6] Configuring Mosquitto..."
cp "$SCRIPT_DIR/../mosquitto/mosquitto.conf" /etc/mosquitto/mosquitto.conf
systemctl enable mosquitto
systemctl restart mosquitto

# --- Python virtual environment ---
echo ""
echo "[3/6] Setting up Python virtual environment..."
VENV_DIR="/opt/tpms_subscriber/venv"
mkdir -p /opt/tpms_subscriber
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install paho-mqtt psycopg2-binary -q

# --- Write config file ---
echo ""
echo "[4/6] Writing configuration..."
cat > /opt/tpms_subscriber/config.env <<EOF
MQTT_BROKER=$MQTT_BROKER
MQTT_PORT=$MQTT_PORT
MQTT_TOPIC=$MQTT_TOPIC
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF
chmod 600 /opt/tpms_subscriber/config.env

# --- Apply database schema ---
echo ""
echo "[5/6] Applying database schema..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -f "$SCRIPT_DIR/schema.sql" \
    && echo "    Schema applied OK." \
    || echo "    WARNING: schema apply failed — check DB connection and try manually."

# --- Deploy subscriber script and systemd service ---
echo ""
echo "[6/6] Deploying subscriber and systemd service..."
cp "$SCRIPT_DIR/tpms_subscriber.py" /opt/tpms_subscriber/tpms_subscriber.py
chmod 755 /opt/tpms_subscriber/tpms_subscriber.py

cp "$SCRIPT_DIR/../systemd/tpms-subscriber.service" /etc/systemd/system/tpms-subscriber.service
systemctl daemon-reload
systemctl enable tpms-subscriber.service
systemctl restart tpms-subscriber.service

echo ""
echo "============================================="
echo " Installation complete!"
echo " Service status:"
systemctl status tpms-subscriber.service --no-pager
echo ""
echo " Useful commands:"
echo "   systemctl status tpms-subscriber"
echo "   journalctl -u tpms-subscriber -f"
echo "   systemctl status mosquitto"
echo "============================================="
