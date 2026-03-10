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
