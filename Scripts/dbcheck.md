# Script

We have the following script that runs a query that updates the idapp_timers table based on how much time has passed since each row's timestamp, so how long a car has been in the lot.
If it's over the timelimit it changes overtime to TRUE.

```
#!/bin/bash

sudo -u postgres psql -d parkkiradio -c "
UPDATE idapp_timer t
SET overtime = TRUE
FROM idapp_location l
WHERE t.location_id = l.\"locationID\"
  AND t.overtime = FALSE
  AND NOW() - t.timestamp > l.time_limit * INTERVAL '1 minute';
"


```

# Cronjob

We opened crontab with "crontab -e" and added the following line.

```
* * * * * /home/ubuntu/check_db.sh >> /home/ubuntu/cron.log 2>&1; sleep 30; /home/ubuntu/check_db.sh >> /home/ubuntu/cron.log 2>&1
```

Now it runs the script we created every 30s and generates logs.

You can turn it on and off with systemctl on cron.
