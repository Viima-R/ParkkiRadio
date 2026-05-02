### Domain name

We got a subdomain from duckdns and pointed it to the IP address of our webserver. We are using our domain name in the instructions, replace with your own.

### Certification

SSL/TSL certification for https and mqtts was done using LetsEncrypts CertBot.

```
sudo apt install python3-certbot-nginx
sudo certbot --nginx -d parkkiradio.duckdns.org
```

Now our certs are here:

/etc/letsencrypt/live/parkkiradio.duckdns.org

Give permissions for mosquitto.

```
sudo usermod -aG ssl-cert mosquitto
sudo chgrp ssl-cert /etc/letsencrypt/live/mqtt.example.com/privkey.pem
sudo chmod 640 /etc/letsencrypt/live/mqtt.example.com/privkey.pem
sudo chmod 755 /etc/letsencrypt/live
sudo chmod 755 /etc/letsencrypt/archive
```

Create a MQTT user so authentication our publisher and subscriber uses.

```
sudo mosquitto_passwd -c /etc/mosquitto/passwd mqttuser
```

And get certification for mqtts. The file: /etc/mosquitto/mosquitto.conf should look like below.

```
listener 8883
certfile /etc/letsencrypt/live/parkkiradio.duckdns.org/fullchain.pem
keyfile /etc/letsencrypt/live/parkkiradio.duckdns.org/privkey.pem

allow_anonymous false

password_file /etc/mosquitto/passwd

persistence true
persistence_location /var/lib/mosquitto/

log_dest file /var/log/mosquitto/mosquitto.log

```
Restart mosquitto and ngingx.

```
sudo systemctl restart mosquitto
sudo systemctl restart nginx
```

Open ports for mqtts and https in firewall, examples for ubuntu.

```
sudo ufw allow 8883
sudo ufw allow 443
```
