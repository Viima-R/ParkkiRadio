# ParkkiRadio
## About
This work is a made for "ICT Infrastructure project" in Haaga-Helia University of Applied Sciences. The goal of this project is to create a solution for tracking parking lot activity with the radio signals that car tyre pressure sensors (TPMS) send.

## Why?
We wanted to learn about the use of software-defined radio (SDR), and after discovering what kind of signals could be captured we ended up going in the direction of detecting the sensors in car tyres that transmit the pressure in the tyre. After brainstorming what we could do with this information we decided to try a build a solution to aid in parking control.

## End result
We created a dashboard that displays the situtation in different parking locations. It shows the number of parked cars, how many cars are in violation of the time limit for the parking area and the capability to reset overtime cars in a location.

<img width="911" height="332" alt="kuva" src="https://github.com/user-attachments/assets/e12a8cb4-9819-4d32-8a48-e306fc67e65c" />

## Setting up guide
This guide is how to setup our project using architechture similiar to ours. If you have questions or feedback you can contact us at: parkkiradio@protonmail.com

HERE is a link to our Django repository which acts as our web framework and is running on our webserver.

### Setting up webserver/MQTT broker with Linux
First install following:
```
sudo apt update
sudo apt install -y nginx mosquitto mosquitto-clients python3 python3-pip python3-dev python3-venv
```
For setting up Django you can find a guide [HERE](https://github.com/Viima-R/ParkkiRadio/blob/main/Documentation/Django/django_notes.md)

How to setup SSL/TSL [HERE](https://github.com/Viima-R/ParkkiRadio/blob/main/Documentation/Memos/https_mqtts_and_authentication.md).

you need to do the above setup if you want to use secure authentication for login to the website/MQTT messaging.

### Setting up publisher

Guide and script for setting up the publisher machine [HERE](https://github.com/Viima-R/ParkkiRadio/tree/main/Code/publisher)

Note that you need a software defined radio to capture signals.

### Setting up database server

Install following

```
sudo apt update
sudo apt install postgresql
```

Create your database and configure the database information in the .env file in Django. Django will automatically create tables for you in the database, so you don't have to worry about those. Create a user for the database and add information about the user to the .env file. Also grant table permissions for the user.

```
sudo -u postgres psql
CREATE USER myuser WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
CREATE DATABASE mydb OWNER myuser;

\c mydb
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO myuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO myuser;
```

Open the following ports for mqtts and postgres.

```
sudo ufw allow 5432
sudo ufw allow 8883
```

Download the [mqtt subscriber](https://github.com/Viima-R/ParkkiRadio/blob/main/Code/Parempi_tpms_subscriber.py).

```
wget https://raw.githubusercontent.com/Viima-R/ParkkiRadio/refs/heads/main/Code/Parempi_tpms_subscriber.py
```

Setting up cronjob to update table for overtime cars [HERE](https://github.com/Viima-R/ParkkiRadio/blob/main/Scripts/dbcheck.md).

## Prototype
In our prototype we captured signals from TPMS sensors with [rtl-433](https://github.com/merbanan/rtl_433), we filtered out only the IDs and they got saved into a text file. We had a program that checked this file between set intervals and had functions to handle the IDs differently depending if the ID was known. A known ID meant that the car had an allocated parking spot, and an unknown IDs were visitors who had a limited parking time.

### Results and conclusions of the prototype
While the program worked mostly as we inteded, the challenges came with how TPMS sensors function:
- TPMS sensors don't transmit constantly, they usually have some time between every transmission so there are times when they pass the detection zone without transmitting.
- Detecting signals from cars that are outside the parking lot.
- The detection zone is usually larger than desired. This becomes a problem when cars are stationary in the parking lot and still occasionally send transmissions. Even though the transmisson rate is very low on stationary cars we still found that this does happen occasionally, this is a problem because we conclude a car is leaving when we detect it a second time.
- Actually separating known cars and visitors is very challenging and time consuming. You would have to record the ID of every tyre from cars that have a parking space allocated, that means if there are 10 allocated spots that would already be 40 IDs that would need to be individually captured, verified and recorded. Now imagine with multiple sets of tyres (summer and winter) and new set of tyres that would have to be registered every time.
- Some old cars don't have TPMS sensors, and the batteries in them can also run out. This means not all cars send signals when visiting the parking area.

Some workaround we came with moving forward with this design:
- The solution can only be advisory, this means that we aknowledge it isn't reliable to monitor activity with it and should only guide the person inspecting parking areas to consider going to the location with cars that have possibly over stayed.
- Think about the detection zone! Massive open spaces can be difficult to work with, you should try to block the direction of the parking spots and have it facing the entrance. Parking halls are easier to work in than outdoors since you catch way less noise.
- We did not implement this in our project, but if you want to avoid the hassle of recording every known car you could give every car that has a parking spot a separate transmitter that transmits an ID that is the same for all known cars.

## Design
Since we had decided the service we're making can only be advisory we decided to make a dashboard that displays a list of locations and shows if any location might need attention from the parking inspector.

<img width="686" height="536" alt="Image" src="https://github.com/user-attachments/assets/6dab4cf1-c725-4522-b441-5b506fa1ec65" />

### Our setup

#### Cloud hosting in cPouta
We needed a place to host the dashboard so we landed on the cloud service "cPouta" offered by the Finnish IT Center for Science. In cPouta we created a webserver to host the dashboard and a database server to handle the information being sent from the parking locations. Our webserver also acts as a broker for our MQTT messages.

#### SDR in parking locations
The software-defined radios would be attached to a Rasberry Pi that would send the IDs it detects via internet to the database server using MQTT protocol. This means there needs to be access to electricity and internet in location.

#### Data transfer
We are using MQTT protocol to publish captured data in our locations to our subscriber the database server. Since the Database server is not connected to internet we have our webserver act as a broker that forwards the messages sent to our database server that is in the same network.

We are using Eclipse Mosquitto to manage the MQTT messages received.

#### Database server
We're using PostgreSQL as our database, and there's a program in the server that processes the IDs it receives and handles them accordingly.
We have a cronjob that runs a SQL query that compares the substraction of when a car was added to the database, so when the server received the message that a car entered the parking lot, and current time to the allotted time limit in the location. If a car is over the time limit the overtime attribute is changed from FALSE to TRUE marking the car as overtime.

#### Web framework
We used Django as our web framework. With Django we could create functionalities to our site, communicate with our database by writing code with Python.

