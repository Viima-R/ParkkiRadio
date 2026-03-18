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

## For the "publisher"

import paho.mqtt.client as mqtt
import json
import time

BROKER = "your.server.ip"
LOCATION_ID = "SITE_01"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)

def publish_tpms(sensor_id, pressure):
    topic = f"tpms/{LOCATION_ID}/{sensor_id}"
    
    payload = {
        "sensor_id": sensor_id,
        "location_id": LOCATION_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    client.publish(topic, json.dumps(payload))

# Example loop
while True:
    publish_tpms("ABC123", 32.5)
    time.sleep(5)

## For the "listener":

import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    
    sensor_id = data["sensor_id"]
    location_id = data["location_id"]

    # Insert into DB
    print(f"{location_id} | {sensor_id}")

client = mqtt.Client()
client.connect("localhost", 1883, 60)

client.subscribe("tpms/#")  # wildcard for all locations

client.on_message = on_message
client.loop_forever()
