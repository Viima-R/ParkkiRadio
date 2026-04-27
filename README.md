# ParkkiRadio
## About
This work is a made for "ICT Infrastructure project" in Haaga-Helia University of Applied Sciences the goal of this project is to create a solution for tracking parking lot activity with the radiosignals car tyre pressure sensors (TPMS) send.

## Why?
We wanted to learn about the use of software-defined radios(SDR) and after discovering what kind of signals could be captured we ended up going in the direction of detecting the sensors in car tyres that transmit the pressure in the tyre. After brainstorming what we could do with this information we decided to try a build a solution to aid in parking control.

## Prototype
In our prototype we captured signals from TPMS sensors with [rtl-433](https://github.com/merbanan/rtl_433), we filtered out only the IDs and they got saved into a text file. We had a program that checked this file between set intervals and had functions to handle the IDs differently depending if the ID was known which meant they had an allocated parking spot or a visitor which meant they had limited parking time.

### Results and conclusions of the prototype
While the program worked as we inteded, the challenges came with how TPMS sensors function:
- TPMS sensors don't transmit constantly, they usually have some time between every transmission so there are times when they pass the detection zone without transmitting.
- Detecting traffic from outside the parking lot.
- The detection zone is usually larger than desired, you can catch signals from very far away. This becomes a problem when cars are stationary in the parking lot and still occasionally send transmissions. Even though the transmisson rate is very low on stationary cars we still found that this does happen occasionally, this is a problem because we conclude a car is leaving when we detect it a second time.
- Actually separating known cars and visitors is very challenging and time consuming. You would have to record the ID of every tyre from cars that have a parking lot allocated, that means if there are 10 allocated spots that would already be 40 IDs that would have to be individually captured, verified and recorded. Now imagine with multiple sets of tyres (summer and winter) and new tyres would have to be registered every time.
- Some old cars don't have TPMS sensors in the tyres, the batteries in them can alos run out.

Some workaround we came with moving forward with this design:
- The solution can only be only advisory, this means that we aknowledge it isn't reliable to monitor activity with and should only guide the person monitoring parking lots to maybe consider going to the location with cars that have possibly over stayed.
- Think about the detection zone! Massive open spaces can be difficult to work with, you should try to block the direction of the parking spots and have it facing the entrance. Parking halls are easier to work in than outdoors since you catch way less noise
- We did not implement this in our project, but if you want to avoid the hassle of recording every known car you could give every car that has a spot a separate transmitter that transmits an ID thats the same for all known cars.

## Design
Since we had decided the service we're making can only be advisory we decided to make a dashboard that displays a list of locations and shows if any location might have cars that are parked over the time limit.

<img width="911" height="332" alt="kuva" src="https://github.com/user-attachments/assets/e12a8cb4-9819-4d32-8a48-e306fc67e65c" />


<img width="686" height="536" alt="Image" src="https://github.com/user-attachments/assets/6dab4cf1-c725-4522-b441-5b506fa1ec65" />

### cPouta
We needed a place to host the dashboard so we landed on the cloud service the Finnish IT Center for Science offers cPouta. In cPouta we created a webserver to host the dashboard and a database server to handle the information being sent from the parking locations.

### SDR in parking locations
The software-defined radios would be attached to a rasberry pi that would send the IDs it detects via internet to the database server using MQTT protocol. This means there needs to be access to electricity and internet in location.

### MQTT and Mosquitto
MQTT is lightweigth, reliable and easy to scale in this kind of a project. Mosquitto is fairly easy to set-up and protect from unwanted data.

### Database server
We're using PostgreSQL as our database, theres a program in the server that processes the IDs it receives and handles them accordingly.
