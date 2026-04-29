import paho.mqtt.client as mqtt


# LOAD CONFIG FROM TEXT FILE

config = {}

with open("mqtt.cfg", "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue  # skip empty lines and comments
        key, value = line.split("=", 1)
        config[key.strip()] = value.strip()

BROKER = config.get("broker")
PORT = int(config.get("port", 8883))
TOPIC = config.get("topic")
USER = config.get("username")
PASSWORD = config.get("password")
LOCATION = config.get("location")


# INPUT ID


SENSOR_ID = input("Enter sensor ID: ").strip()


# MQTT SETUP


client = mqtt.Client()

if USER:
    client.username_pw_set(USER, PASSWORD)

client.tls_set()
client.connect(BROKER, PORT, 60)



# SEND MESSAGE


payload = f'{{"id": "{SENSOR_ID}", "location": "{LOCATION}"}}'

client.publish(TOPIC, payload)

print("Sent:", payload)

client.disconnect()
