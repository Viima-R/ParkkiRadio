# Notes for MQTT and Mosquitto

## A Broker 

- Mosquitto, https://mosquitto.org, https://mosquitto.org/download/

### Codes for transmitting/receiving

- https://test.mosquitto.org

Server:  
1883 : MQTT, unencrypted, unauthenticated  
1884 : MQTT, unencrypted, authenticated  

This is a Mosquitto configuration file that creates a listener on port 1883 that allows unauthenticated access:

listener 1883
allow_anonymous true



Sources:

https://github.com/malinjade/plantproject

# In practice

## Setup

### Linux (Debian 12) 
To install a Mosquitto Broker:  
- sudo apt install mosquitto mosquitto-clients
- sudo systemctl start mosquitto
- sudo systemctl status mosquitto

To test:

Listener (computer1):
- mosquitto_sub -h localhost -t test/topic

Publisher (computer2):
- mosquitto_pub -h localhost -t test/topic -m "Hello MQTT"

Should show the message on computer1.  

Mosquitto listens port TCP 1883.  
To test:  
- sudo ss -tulpn | grep 1883


### iOS
To install a Mosquitto Broker:
- brew install mosquitto
- brew services restart mosquitto

If a problem occurs, the conf -file might be missing.  
Go to:  
- cd /opt/homebrew/etc/mosquitto  
Then:  
- cp mosquitto.conf.example mosquitto.conf  
Then restart Mosquitto:  
- brew services restart mosquitto  
And it should be up and running.

To test:

Listener (terminal1):
- mosquitto_sub -h localhost -t test/topic

Publisher (terminal2):
- mosquitto_pub -h localhost -t test/topic -m "Hello MQTT"

Should show the message on terminal1.  

## To use

To establish a listen configure mosquitto.conf -file for example with the next information:  
- listener 1883
- allow_anonymous false
- password_file /etc/mosquitto/passwd  // Hashed built-in utility
- persistence true  // Ensures saving the data in case of a crash
- persistence_location /var/lib/mosquitto/

To set up a username and a password the first time:  
- sudo mosquitto_passwd -c /etc/mosquitto/passwd your_username

Other users without the "-c":  
- sudo mosquitto_passwd /etc/mosquitto/passwd your_username  

Usernames and hashed passwords are save in /etc/mosquitto/passwd

To allow the Mosquitto to be the autheticator, change the permissions and the owner:  
- sudo chmod 600 /etc/mosquitto/passwd  
- sudo chown mosquitto:mosquitto /etc/mosquitto/passwd  

In the end the listening/sending messages change to be like this:
- mosquitto_sub -h localhost -t "test/topic" -u tpms_user -P your_password
- mosquitto_pub -h localhost -t "test/topic" -m "hello world" -u tpms_user -P your_password

# Using to transmit

## Publish directly to Mosquitto

rtl_433 -f 433.92M -F json \
| jq -r '.id' \
| mosquitto_pub -h YOUR_SERVER_IP -p 1883 -u USERNAME -P PASSWORD -t tpms/id -l

## For the listener

### !!Check in practise!!

import sqlite3
import paho.mqtt.client as mqtt
from datetime import datetime

# --- Database setup ---
conn = sqlite3.connect("tpms.db")  
cursor = conn.cursor()

cursor.execute("""  
CREATE TABLE IF NOT EXISTS sensors (  
    id TEXT PRIMARY KEY,  
    first_seen TEXT,  
    last_seen TEXT  
)  
""")

conn.commit()

# --- MQTT callback ---  
def on_message(client, userdata, msg):  
    sensor_id = msg.payload.decode().strip()  
    now = datetime.utcnow().isoformat()  

    if not sensor_id:
        return

    try:
        # Try inserting new sensor
        cursor.execute("""
            INSERT INTO sensors (id, first_seen, last_seen)
            VALUES (?, ?, ?)
        """, (sensor_id, now, now))

        print(f"New sensor stored: {sensor_id}")

    except sqlite3.IntegrityError:
        # Already exists → update last_seen
        cursor.execute("""
            UPDATE sensors
            SET last_seen = ?
            WHERE id = ?
        """, (now, sensor_id))

        print(f"Updated sensor: {sensor_id}")

    conn.commit()

# --- MQTT setup ---
client = mqtt.Client()
client.username_pw_set("USERNAME", "PASSWORD")
client.connect("YOUR_SERVER_IP", 1883)

client.subscribe("tpms/id")
client.on_message = on_message

print("Listening for TPMS IDs...")
client.loop_forever()


