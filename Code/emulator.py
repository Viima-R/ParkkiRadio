import random
import time
import threading
import paho.mqtt.client as mqtt
import json

# Location name where IDs are being sent from
LOCATION = "testaamo"

# MQTT config
BROKER = "86.50.22.104"
PORT = 8883
TOPIC = "tpms/ids"
USER = ""
PASSWORD = ""

client = mqtt.Client()
client.username_pw_set(USER, PASSWORD)
client.tls_set()
client.connect(BROKER, PORT, 60)


# PREDEFINED CAR POOL

cars = [
    ["ABCD1234", "ABCD5678", "ABCD9A12", "ABCDFFEE"],
    ["1234AAAA", "1234BBBB", "1234CCCC", "1234DDDD"],
    ["9F9F0001", "9F9F0002", "9F9F0003", "9F9F0004"],
    ["BEEF1111", "BEEF2222", "BEEF3333", "BEEF4444"],
    ["C0DEAAAA", "C0DEBBBB", "C0DECCCC", "C0DEDDDD"],
]


# SIMULATION SETTINGS

ARRIVAL_INTERVAL = (2, 6) #New car arrives every 2-6s
PARK_TIME = (20, 60) #Car is parked for 20-60s


# STATE TRACKING

available_cars = cars.copy() #Cars not in parkinglot
active_cars = set() #Cars in parkinglot
lock = threading.Lock() 


# SEND MESSAGE

def send_once(sensor_id):
    payload = json.dumps({
        "id": sensor_id,
        "location": LOCATION
    })
    client.publish(TOPIC, payload)
    print(payload)


# CAR SIMULATION

def simulate_car():
    global available_cars

    # Pick a car safely
    with lock:
        if not available_cars:
            return
        sensors = random.choice(available_cars)
        available_cars.remove(sensors)
        active_cars.add(tuple(sensors))

    print(f"\nCar ARRIVES: {sensors}")

    # ENTRY → one sensor, one message
    entry_sensor = random.choice(sensors)
    send_once(entry_sensor)

    # Parked → no messages
    time.sleep(random.uniform(*PARK_TIME))

    # EXIT → one sensor, one message
    exit_sensor = random.choice(sensors)
    send_once(exit_sensor)

    print(f"Car DEPARTS: {sensors}\n")

    # Return car to pool
    with lock:
        active_cars.remove(tuple(sensors))
        available_cars.append(sensors)

# ---------------------------
# ARRIVAL LOOP
# ---------------------------
def arrival_loop():
    while True:
        time.sleep(random.uniform(*ARRIVAL_INTERVAL))
        threading.Thread(target=simulate_car, daemon=True).start()

# ---------------------------
# START
# ---------------------------
threading.Thread(target=arrival_loop, daemon=True).start()

while True:
    time.sleep(1)