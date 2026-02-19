### Commands to extract the ID from rtl-433 feed

``rtl_433 -F json | jq -r --unbuffered 'select(has("type")) | select(.type=="TPMS") | .id' | tee -a filename.txt``

Below is a code that uses a ready-made json instead of the output from the rtl 433. The test.json is at least somewhat "anonymized" and the IDs are not the actual IDs that were captured.

``jq -r --unbuffered 'select(has("type")) | select(.type=="TPMS") | .id'  test.json | tee -a filename.txt``

Sources:  
https://jqlang.org/manual/  
https://www.baeldung.com/linux/jq-command-json  
https://earthly.dev/blog/jq-select/


### A simple script for adding a new ID into the database

Remember to give yourself execute rights for the script: ``chmod u+x name_of_script.sh``
Run the script: ./name_of_script.sh

addid.sh   

```                                                 
#! /usr/bin/bash
echo "Anna uusi ID"
read id


echo "Lisätään tietokantaan test.db: insert into tbl1  (id)  values (\"$id\");"
sqlite3 test.db "insert into tbl1 (id) \
         values (\"$id\");"

```

### A script for removing an ID from the database (doesn't do any checks)

removeid.sh

```
#! /usr/bin/bash
echo "Anna poistettava ID"
read id


echo "Poistetaan tietokannasta test.db: DELETE FROM tbl1 WHERE id = (\"$id\");"
sqlite3 test.db "delete from tbl1 where id = (\"$id\");"
```

Source: https://stackoverflow.com/questions/4152321/how-to-insert-into-sqlite-database-using-bash


