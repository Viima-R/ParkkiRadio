# Weekly reports  

# Week 7 (first week of reporting)  

We had a meeting with our project tutor, Harto Holmström. Meeting was a quick run-through of our project plan; weekly goals, considered problems and ideas how to solve them.  

## Project Management  

- documentation in GitHub
- setting up Teams for quick chat and meetings
- unspoken contract of weekly meetings, mostly on Teams to check up progress, and next week a hands-on contact meeting for a field test/research
- finalaze the on going weeks goals
- planning next weeks agenda (getting a car and trying to activate our TMPS sensors)
  
## List of aquired hardware  

- One additional rtl-dongle (two in total)
- Four TPMS sensors

## Done

- Research for managing the rtl-dongle and saving received information, and general info about the TMPS sensors.
- Creating SQL commands to filter saved data
- Created a program for listing car IDs


## TO/DO

- Contact a tyre company to ask about the activation of a TMPS sensor
- Aquire a car for testing
- Making a script for saving wanted data

# Week 8

## Field research 20.02. at 13.30 // Cancelled

## DONE

- Script tweaks
- SQL tweaks
- Code enhancment

# Week 9

Second meeting with our tutor teacher for cathing up. Realezing that the product works in a way, but the problem for practical usage percist.


## Field research 26.2. // *Rescheduled*

- Lidl in 4. linja
- General scanning of tyres/cars
- Creating scenarios with our "known car"
- Photos for documentation

## TO/DO

- Thinking about the end product: trigger alarm
- Creating an emulating program to test the program


# Week 10

This week we started with a field experiment. We also have a meeting with our tutor to discuss our findings.

## Field research 2.3.

![IMG_5494](https://github.com/user-attachments/assets/f45a11f6-2386-4961-975d-71572a77806d)  
Merihaka test enviroment

Testing hardware:
- Two computers; linux and mac
- Two receiver dongles
- One Mercedes-Benz

Testing area:
- Lidl basement parking in Kallio, Helsinki
- Merihaka parking hall, semi outside area, but surrounded by heavy concrete walls, area about 60x60 meters

Tests:
- Identifying the tires in our test car
- Noting how parked cars usually don't send data
- Three sets of testing the length, which the transmitter captures the sent data from our test car

Conclusions:
- The indentification of a tyre set is supposedly easy in a heavily controlled space
- The strength of the transmitter is about 40 to 45 meters in a walled space, but without any disturbance in the line of transmission
- More brainstorming needed to find a suitable way to use the 'product'

TO/DO
- Measurementing the potential strength of the receiver/dongle

## Ideas going forward

- Application for use, maybe just a web application
- An application for parking halls, measuring traffic on a specific spot
- A database, MQTT, CSC for linux virtual sevice (6 months), pouta, a cloud server, lampstack  
[csc pouta](https://docs.csc.fi/cloud/pouta/launch-vm-from-web-gui/)  

## TO/DO

- Creating a virtual server with cPouta/ePouta
- Ponder with MQTT
- Creating a webpage...

# Week 11

We've had a week of research to search a bit the direction for the project. Now, the week starts with a meeting with our tutor. 
Processes with the server, MQTT and webpage to be continued.

Team meating on friday to check progress:

- Servers are coming up
- MQTT is almost in order
- making the architecture a bit more clearer
- django to be an intermediate between the servers and webpage
- Webpage has a solid default page

## TO/DO

- Database server to run
- MQTT to automatically write in to the database
- Setting up Django
- Webpage tbc  
![Documentation/Memos/Screenshot 2026-03-13 at 11.33.53.png](https://github.com/Viima-R/ParkkiRadio/blob/main/Documentation/Memos/Screenshot%202026-03-13%20at%2011.33.53.png)

# Week 12

We are pacing up and checking progress this week on thursday.

# Week 13

A team meeting on friday. We have worked on the tasks at hand:

- MQTT readyness to the server and to the database.
- Cron setting to the Database
- Working on the role of Django

## TO/DO

- MQTT in practise
- Django
- Cron
- General cleanup

# Week 14

Meeting with the tutor after 3 weeks of working by ourselves. Time for a project progress report.

# Week 15

# Week 16

Check up session with the tutor teacher; realization of the limits of our concept, trying to make more simple and to find a way to publish.... 

- Bluetooth-beacons over TMPS

# Week 17

Final push. We managed to connect the pieces and the tube works. Publisher filters the wanted sensors from the RTL-SDR feed, Subscriber automatically adds wanted data into the database, automation towards the webpage works.

# Week 18

Everything is in its place. Preparing presentation.
