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

## Linux (Debian 12) 
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


## iOS
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

