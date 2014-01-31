# Part of the code is based upon code from Adafruit found at 
# http://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi/script
#!/usr/bin/env python

from __future__ import division
import time
import os
import RPi.GPIO as GPIO
import eeml
import eeml.datastream
import sys
import syslog
import json
import gspread
import math
import re

# Account details for google docs
email       = 'illuminous100@gmail.com'
password    = 'illuminous'
spreadsheet = 'gps'

# Login with the Google account
print "logging in to Google..."
try:
    gc = gspread.login(email, password)
except:
    print "Unable to log in.  Check your email address/password"
    sys.exit()

 
GPIO.setmode(GPIO.BCM)
DEBUG = 0
 
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)
 
        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low
 
        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
 
        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1
 
        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout
 
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25
 
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

#define input pins of ADC (inputs 0 through 7)
current_sensor = 1;
voltage_sensor = 0;
cell_sensor = 2;
 
#change this variable to calibrate reading of current sensor#
#perform calibration  by placing a current meter (multimeter) in series with input pins of the sensor,#
#and compare readings from current meter against readings from current sensor#
correction_factor = -35

#enter your "API key" and "Feed ID" here obtained from your xively account#
API_KEY = 'bQtVBc1P4jvFQfVdXQNvn8yDN5L8lAkLyVkaXC5svli7ncwW'
FEED = 546310020
API_URL = '/v2/feeds/{feednum}.xml' .format(feednum = FEED)

while True:
    
     # Open a worksheet from your spreadsheet using the filename
    try:
        worksheet = gc.open(spreadsheet).sheet1
       # Alternatively, open a spreadsheet using the spreadsheet's key
       #worksheet = gc.open_by_key('0Auj2nNMNpo59dHFKZkdEZ3MxV2xwYWttQ3NCYWt0MWc')
    except:
        print "Unable to open the spreadsheet.  Check your filename: %s" % spreadsheet
        sys.exit()
    
    #gathers the data in the first column
    col=worksheet.col_values(1)
    
    #Extracts last coordinate in column
    for column in col[1:]:
        output=column
    
    
    current_reading = []
    voltage_reading = []
    current_reading_a = voltage_reading_a = 0
    
    #a loop which reads in voltage from 5V pin and current sensor 10 times#
    for x in range(10):
        current_reading = readadc(current_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
        voltage_reading = readadc(voltage_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
        current_reading_a += current_reading
        voltage_reading_a += voltage_reading        
        time.sleep(0.1)
    
    #calculates average for readings from 5V pin and current sensor"
    current_reading_a /= 10;
    voltage_reading_a /= 10;
    
    #calculates voltage from 5V pin averaged reading and stores it in a variable#
    vcc_reading = 6 / 1023 * voltage_reading_a
    
    #calculates voltage from current sensor averaged reading and stores it in a variable#
    current_sensor_voltage = 3.28 / 1023 * current_reading_a
    
    #calculates current (in mA) from current sensor averaged reading and stores it in a variable#
    current = ((6 / 1023 * (voltage_reading_a + correction_factor) / 2) - (3.3 / 1023 * (current_reading_a + correction_factor)) ) /0.1 * 1000
    
    #reads in and calculates solar cell voltage from solar cell ADC reading#
    cell_reading = 6 / 1023 * readadc(cell_sensor, SPICLK, SPIMOSI, SPIMISO, SPICS)
    
    #calculates power(in Watts) by multiplying current and voltage values#
    power = cell_reading * (current / 1000)
    power = round(power, 2)
    
    #outputs readings from 5V pin, current sensor and solar cell into terminal for monitoring#
    print "Voltage reading: %.3f Current sensor reading: %.3f current(mA): %.3f" % (vcc_reading, current_sensor_voltage, current)
    print "Cell reading %.3f" % (cell_reading)
    
    #changes GPS coordinates string into xively suitable format#
    output = output.replace(",","__LONG_")
        
    # open up your feed
    pac = eeml.Pachube(API_URL, API_KEY)
    
    #compile data
    pac.update([eeml.Data("Power__coordinates__LAT_"+output, power)])


    
    # send data to xively
    pac.put()
    
    #change the value inside brackets to increase or decrease the frequency (in seconds) at which feed is updated#
    time.sleep(2)
