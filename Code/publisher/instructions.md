# Instructions for Mosquitto Publisher

- Download the publisher folder

- Run install.sh  
  - First: **chmod +x install.sh**   
  - Then run: **./install.sh**  

- The installation program will ask you your preferred Broker address, used port, topic for the message, location of your device, username and password.  
Then it will install all the necessary programs needed to run RTL-433 and Mosquitto.

- Now you are ready with everything and can just put the publisher running:  
**source /opt/tpms_publisher/venv/bin/activate**  
**python3 tpms_publisher.py**
