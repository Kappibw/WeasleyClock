# Embedded Code
This directory contains two python scripts for running the weasley clock on a raspberry pi.

## Setup
Each stepper motor driver needs 4 GPIO pins from the raspberry pi. To keep the same configuration that we used, see
these pin assignments:

|               |              | GPIO Pin | GPIO Pin | GPIO Pin | GPIO Pin |
|---------------|--------------|----------|----------|----------|----------|
| **Shaft**      | **Servo Driver**    |**Input A**   | **Input B** | **Input C** | **Input D** |
| Outer          | D1(top)       | GPIO7     | GPIO8     | GPIO25    | GPIO24    |
| Outer-Middle   | D2            | GPIO9     | GPIO10    | GPIO22    | GPIO27    |
| Inner-Middle   | D3            | GPIO14    | GPIO15    | GPIO18    | GPIO23    |
| Inner          | D4(bottom)    | GPIO2     | GPIO3     | GPIO4     | GPIO17    |


![pin_out](https://learn.microsoft.com/en-us/windows/iot-core/media/pinmappingsrpi/rp2_pinout.png)

## Scripts
### main_loop.py
This script should be run periodically from cron:
```bash
crontab
```
For example, to run every minute:
```
* * * * * /usr/bin/python3 /path/to/main_loop.py
```

The script fetches location data from api.thinkkappi.com and processes it to compute how much each hand should move to point at the 
user's current semantic location. It then gives the stepper motors commands to move the hands the computed amount.

### reset_hands.py
This script can be run on an ad-hoc basis. It is a cli that will guide the user to select a clock hand, 
and then use the arrow keys to move the hand clockwise or anticlockwise until the hand is pointing up at 12. This allows for easy
resetting of state on the clock, as we don't have sensors to get abosulte hand position, and various errors may get introduced (for
example if a hand slips or drags from friction).

This script is older and uses python 2.
