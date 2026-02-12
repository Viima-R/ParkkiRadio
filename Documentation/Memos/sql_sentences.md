Here is a frame work for the database:

CREATE TABLE auto  
  (auto_id		VARCHAR(10)  PRIMARY KEY  
  ,tyre_id		VARCHAR(10)  NOT NULL  
  );


CREATE TABLE spot  
  (spot_id	VARCHAR(10)  PRIMARY KEY  
  ,auto_id	VARCHAR(10)  FOREIGN KEY  
  );
  

CREATE TABLE tyre  
  (tyre_id VARCHAR(10)  PRIMARY KEY  
  );



INSERT INTO auto  
(auto_id, tyre_id)  
VALUES


INSERT INTO spot  
(spot_id, auto_id)  
VALUES


INSERT INTO tyre  
VALUES
