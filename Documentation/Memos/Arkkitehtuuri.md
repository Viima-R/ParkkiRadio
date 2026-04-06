# Arkkitehtuuri

## Softaradio
Havaitsee TPMS sensorit

## IoT (raspberry Pi)  
Heittää tietoja eteenpäin

## MQTT
Asennetaan Mosquitto välittäjäksi. Tietokanta toimii välittäjänä ja kuuntelijana, serveri lähettäjänä Raspberri Pilla. Lähetyksenä on renkaan ID ja Raspberry Pihin kohdistettu ID, jotka tallennetaan tietokantaan.

## Tietokanta

Tietokanta on nimeltään Parkkiradio alla kuva sen rakenteesta.

![alt text](db_diag.png)

### Yliajan tarkistaminen tietokannasta cron:illa

Kotihakemistossa on scriptitiedosto nimeltään check_db.sh joka ajaa tiedoston /tmp/check_overtime.sql joka vertaa auton alkuaikaa nykyaikaan ja niiden erotusta sallittuun aikaan ja muuttaa tarvittaessa yliajan trueksi.

Tämä scripti tiedosto ajetaan voidaan ajaa cron:illa tietyn ajan välein tekemällä cron job seuraavin komennoin.


```
crontab -e
* * * * * /home/ubuntu/check_db.sh
```

Tämä ajaa scriptin check_db.sh minuutin välein.

Tässä vielä check_db.sh ja check_overtime.sql sisällöt.

```
#!/bin/bash
sudo -u postgres psql -d parkkiradio -f /tmp/check_overtime.sql
```

```
UPDATE timers t
SET overtime = TRUE
FROM location l
WHERE t.location = l.location_id
AND t.overtime = FALSE
AND NOW() - t.start_time > (l.time_limit || ' minutes')::INTERVAL;

```

## Python backend
Python ohjelma, joka hoitaa ajastimet yms.

## WebApi
Django, automaatio, joka tarkistaa IDt ja tekee tarvittavat.

## Verkkosivu

Verkkosivulla perustoimintona tulisi olla sijainnit ja sijaintijen tiedoissa tieto onko siellä yliaikaa olevia autoja.

## Servers

Palvelimet CSC:n cPouta alustalla, cPouta on OpenStackiin perustuva pilvipalvelu.

Meillä on webserveri julkisessa aliverkossa ja tietokanta palvelin yksityisessä, johon saa yhteyden vain hyppäämällä ensin webserverin kautta.

Security groupit on määritelty siten, että asiattomilta pääsy tietokanta palvelimelle ei pitäisi onnistua.

Webserverillä on domain nimi https://parkkiradio.duckdns.org/idapp/location-list/, luotu käyttämällä duckdns.

Sertifiointi https varten tehty certbottia käyttäen.
