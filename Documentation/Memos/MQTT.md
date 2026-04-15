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

Both the server and the database have now Mosquitto, and the database is running as a broker and a listener. For now they are inactive, but to put them up:

sudo systemctl start mosquitto

Publish:  
mosquitto_pub -h <BROKER_IP> -t test/topic -m "message" -u tpms_user -P your_password

Listen:  
mosquitto_sub -h localhost -t test/topic -u tpms_user -P your_password

## Publish directly to Mosquitto

rtl_433 -f 433.92M -F json \
| jq -r '.id' \
| mosquitto_pub -h YOUR_SERVER_IP -p 1883 -u USERNAME -P PASSWORD -t tpms/id -l

# EMULATION

First install *pip install paho-mqtt* or *sudo apt install python3-pip* on both machines (server, database).

Create python programming nano files on both. Broker is going to be the database server.

## For the Publisher (the correct indentations in edit mode):

nano tpms_publisher.py

import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "192.168.1.252"
PORT = 1883
TOPIC = "tpms/data"

LOCATION_ID = "rpi_001"

PREFIXES = ["2E8F", "D4C0", "A1B2", "9F3D"]

def generate_data():
    prefix = random.choice(PREFIXES)

    suffix = f"{random.randint(0, 0xFFFF):04X}".lstrip("0") or "0"

    tpms_id = f"{prefix}{suffix}"

    return {
        "tpms_id": tpms_id,
        "location_id": LOCATION_ID
    }

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

while True:
    data = generate_data()
    payload = json.dumps(data)

    client.publish(TOPIC, payload)
    print(f"Sent: {payload}")

    time.sleep(3) 

## For the Subscriber (the correct indentations in edit mode):

nano tpms_subscriber.py

import paho.mqtt.client as mqtt
import json
import psycopg2

# ----- MQTT settings -----
BROKER = "192.168.1.252"
PORT = 1883
TOPIC = "tpms/data"

# ----- PostgreSQL settings -----
DB_HOST = "192.168.1.252"
DB_NAME = "parkkiradio"
DB_USER = "tpms_user"
DB_PASSWORD = "strongpassword"

# ----- Connect to PostgreSQL -----
conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# ----- MQTT callbacks -----
def on_connect(client, userdata, flags, rc):
    print("Connected to broker", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        tpms_id = data.get("tpms_id")
        location_id = data.get("location_id")

# Extract car_id (first 4 chars)
        car_id = tpms_id[:4]

# Insert car
        cursor.execute(
             """
             INSERT INTO timers (car_id, location, start_time)
             VALUES (%s, %s, NOW())
             ON CONFLICT (car_id)
             DO UPDATE SET
                 location = EXCLUDED.location,
                 start_time = NOW()
             """,
            (car_id, location_id)
        )

# Insert tpms_id into permitted
        cursor.execute(
            "INSERT INTO permitted (tpms_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (tpms_id,)
        )

# Insert raspberry_id into location
        cursor.execute(
            "INSERT INTO location (location_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (location_id,)
        )
        conn.commit()
        print(f"Saved: {tpms_id}, car: {car_id}, location: {location_id}")

    except Exception as e:
        print("Error:", e)
        conn.rollback()

# ----- MQTT client setup -----
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()


## tpms_checker.py

import psycopg2
import time

DB_HOST = "192.168.1.252"
DB_NAME = "parkkiradio"
DB_USER = "tpms_user"
DB_PASSWORD = "strongpassword"


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def process_cars():
    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Get all current cars from timers
        cursor.execute("SELECT car_id, location FROM timers")
        cars = cursor.fetchall()

        for car_id, location in cars:

            # 1. Check if car is known
            cursor.execute(
                "SELECT location FROM idapp_carID WHERE car_id = %s",
                (car_id,)
            )
            known = cursor.fetchone()

            if known:
                known_location = known[0]

                if known_location == location:
                    # Known and correct location -> do nothing
                    continue
                else:
                    # Known but wrong location (optional handling)
                    print(f"Car {car_id} in wrong location!")
                    continue

            # 2. Unknown car -> handle idapp_timer
            cursor.execute(
                """
                INSERT INTO idapp_timer ("carID", timestamp, overtime, location_id)
                VALUES (%s, NOW(), FALSE, %s)
                ON CONFLICT ("carID")
                DO UPDATE SET
                    timestamp = NOW(),
                    location_id = EXCLUDED.location_id,
                    overtime = FALSE
                """,
                (car_id, location)
            )

        conn.commit()
        print("Check cycle complete")

    except Exception as e:
        print("Error:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    while True:
        process_cars()
        time.sleep(5)  # adjust frequency


# SQL

## permitted

- tpms_id    *text*    not null    PK
- lot_number    *int*
- location    *text*    FK(location(location_id))

## location

- location_id     *text*    not null    PK
- name            *text*
- address         *text*
- time_limit      *int*

## timers

- car_id      *text*    not null
- location    *text*    FK(location(location_id))
- start_time  *timestamp without time zone*
- overtime    *boolean*

## idapp_carID

- id    *bigint*
- car_id    *varchar*    PK
- location    *varchar*
- created_at    *timestamp with time zone*

## idapp_timer

- carID        *varchar*    PK
- timestamp    *timestamp with time zone*
- overtime     *boolean*
- location_id  *text*

