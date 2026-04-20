### Domain name

We got a subdomain from duckdns and pointed it to the IP address of our webserver.

### Certification

Certification for https was done using LetsEncrypts CertBot.

sudo apt install python3-certbot-nginx
sudo certbot --nginx -d parkkiradio.duckdns.org