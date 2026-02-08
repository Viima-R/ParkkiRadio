Testing done on Feb 1st.

I did some testing with an RTL dongle that I already owned. I was near the window on the sixth floor. There was a small parking lot with 5-6 cars below the window. Some cars left or arrived to the parking lot or just dropped people off, but many cars had probably been there for a long time and were not emitting signals during the time when I was doing the testing.

I ran the rtl-433 program for a bit over 2 hours and captured more than 1200 signals. 336 signals were marked "TPMS" and others were weather sensors etc.

I only got signals from a few Toyotas and one other car make, so the information is limited.

The Toyotas and the other car had these in common: time, model, type (TPMS), id (hexadecimal), and mic (the value was CHECKSUM for one and CRC) for the other.

The different parameters were: flags, status, pressure_kPa/pressures_PSI, temperature_F/temperature_C.

Some of my findings:

- TPMS signals seem to be easy to filter, because they're marked "type: TPMS". It would be good to verify that this is always the case with every sensor.
- some temperature were in Celsius "temperature_C", others in Fahrenheit "temperature_F"
- some tyre pressures were in PSI "pressure_PSI", others in kPA "pressure_kPa"
- the Celsius temperature ranged from -7 to -16. However, the air temperature at the time was probably not as low as -16, so how reliable is the temperature? Also, the temperature is of course connected to the weather, so if we want to use the tyre temperature, should we also know the current weather? Or take the temperature from the beginning and then see how much it has changed?
- the temperature was always full degrees (not 12,5, for example)
- the sensor ids of a car seem to start with the same characters. This might not always be the case, though? Depends how the sensor was configured.
- based on the ids, one car was present for the whole 2 hours and in that time it sent about 280 signals, approximately two signals every minute


Later I did more testing next to a window where there was a street below. I didn't get a signal from most cars. 

Conclusion: Capturing the signals was not a problem at all, because the signal seems to travel well at least in a clear weather, and also being behind a window does not affect it. The problem is the timing: how often does the car send the signal. 

TODO: I could look more into the pattern of how often the signals were sent from the Toyota that sent them for the full 2 hours.
