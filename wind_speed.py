#!/usr/bin/env python

# Import GPIO and time libraries
import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime
import oled_display
import os

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18,GPIO.IN)
GPIO.setup(24,GPIO.OUT)
# inspired by https://www.explainingcomputers.com/sample_code/Wind_Speed.py


# Anamometer vane diameter (set to the value for your cup-to-cup in mm)
vane_diameter = float(220)

# Calculate vane circumference in metres
vane_circ = float (vane_diameter/1000)*3.1415

# Set an anamometer factor to account for inefficiency (value is a guess)
afactor = float(4)

# Start measuring wind speed and let us know things are happening!
# print('Measuring wind speed...')

# Define variables rotations and trigger (trigger = 1 if sensor triggered)
rotations = float(0)
trigger = 0

# Define variable endtime to be current time in seconds plus 10 seconds
interval_seconds=10
endtime = time.time() + interval_seconds

# Get initial state of sensor
sensorstart = GPIO.input(18)

def get_output_file():
    output_file_tmp=os.path.join(os.path.dirname(__file__),"data","windspeed-"+time.strftime("%Y%m%d-%H%M%S")+".csv")
    return output_file_tmp

oled_display.display_text("Sample Interval:",str(interval_seconds)+' seconds')
previous_ymd='0'
output_file=''
i=0

while True:
    # Measurement loop to run for n seconds
    while time.time() < endtime:
        if GPIO.input(18)==1 and trigger==0:
            rotations = rotations + 1
            trigger=1
            GPIO.output(24,GPIO.HIGH)
        if GPIO.input(18)==0:
            trigger = 0
            GPIO.output(24,GPIO.LOW)
        # We seem to need to add a little delay to make things work reliably...
        time.sleep(0.001)

    # Loop has now finished. But if sensor triggered at start and did not move,
    # rotations value will be 1, which is probably wrong, so . . .
    if rotations==1 and sensorstart==1:
        rotations = 0

    # Calculate stuff!
    rots_per_second = float(rotations/interval_seconds)
    windspeed = float((rots_per_second)*vane_circ*afactor) # meters per second
    windspeed_mph=round((windspeed*2.237),2)
#     print(windspeed_mph)
   # print("Wind Speed: {0} mph".format(windspeed_mph))
    oled_display.display_text("Wind Speed:",str(windspeed_mph))

    header = ['time_stamp','wind_speed','rotations_per_second']
    current_datetime = datetime.now().isoformat(sep=" ", timespec="seconds")
    data = [current_datetime,windspeed_mph,round(rots_per_second,2)]
    
    # check to see if it's a new day. If so, start a new file. 1 file per day
    current_ymd=time.strftime("%Y%m%d")
    if current_ymd != previous_ymd:
        previous_ymd=current_ymd
        output_file=get_output_file()

    with open(output_file, 'a', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)

        # write the header but only on the first loop
        if i==0:
            writer.writerow(header)

        # write the data
        writer.writerow(data)
    i+=1
    endtime = time.time() + interval_seconds
    rotations=0
    trigger=0
    sensorstart = GPIO.input(18)
    

# cleanup the GPIO before finishing :)
GPIO.cleanup()
