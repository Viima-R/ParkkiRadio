### Diagram for a database called parkkiradio

![alt text](db_diag.png)

### Commands used

CREATE DATABASE parkkiradio;

CREATE TABLE location (location_id SERIAL PRIMARY KEY, name TEXT NOT NULL, address TEXT, time_limit INT);

CREATE TABLE permitted (tpms_id TEXT PRIMARY KEY, lot_number INT, location INT REFERENCES location(location_id) ON DELETE CASCADE); 

CREATE TABLE timers (car_id TEXT PRIMARY KEY, location INT REFERENCES location(location_id) ON DELETE CASCADE, start_time TIMESTAMP DEFAULT NOW(), overtime BOOLEAN DEFAULT FALSE);

### Command templates

INSERT INTO location (name, address, time_limit) VALUES('', '', '');

INSERT INTO timers (car_id, location) VALUES('', (SELECT location_id FROM location WHERE name = ''));

INSERT INTO permitted (tpms_id, lot_number, location) VALUES('', '', (SELECT location_id FROM location WHERE name = ''));

DELETE FROM timers WHERE car_id = '';

DELETE FROM permitted WHERE lot_number = '';

DELETE FROM permitted WHERE tpms_id = '';
