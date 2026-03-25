# Cron

.sql file (/tmp/check_overtime.sql) that checks if the difference between time now and the time when the car parked is greater than the time_limit for that location (IN MINUTES!)
Then it changes the overtime vaule to TRUE if that is the case.
A cron job can be now created that checks the database in set interval.
"crontab -e"
"* * * * * /home/ubuntu/run_cron.sh"
(* * * * * means every minute)
