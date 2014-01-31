#!/usr/bin/python

import subprocess
import re
import sys
import time
import datetime
import gspread
import os
import subprocess
import time 
import gps
import math

#calculates the distance between two locations in meters
def distance(lat, lon, lat2, lon2):

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
        
    # phi = 90 - latitude
    phi1 = (90.0 - lat)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
        
    # theta = longitude
    theta1 = lon*degrees_to_radians
    theta2 = lon2*degrees_to_radians
        
    # Compute spherical distance from spherical coordinates.
    
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )
    
    #converts the distance to get degrees
    arc=arc*6373000
    return arc

#Kills all previous GPS sessions as they can interfere and prevent the program displaying a fix
#os.system('sudo killall gpsd')
os.system('sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock')

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

# Open a worksheet from your spreadsheet using the filename
try:
    worksheet = gc.open(spreadsheet).sheet1
  # Alternatively, open a spreadsheet using the spreadsheet's key
   #worksheet = gc.open_by_key('0Auj2nNMNpo59dHFKZkdEZ3MxV2xwYWttQ3NCYWt0MWc')
except:
    print "Unable to open the spreadsheet.  Check your filename: %s" % spreadsheet
    sys.exit()


print "Getting the GPS data..."
#get the co-ordinates from the chip

# Listen on port 2947 (gpsd) of localhost
session = gps.gps(host="localhost", port="2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while True:
    try:
        report = session.next()
        # Wait for a 'TPV' report which means it has a fix
        #print report, means you can see all of the reprt data from the GPS
        if (report['class'] == 'TPV'):
            #print report
            if hasattr(report, 'lat'):
                lat=report.lat
                lon=report.lon
                
                output=str(report.lat) + ","+ str(report.lon)
                print "The coordinates are: "+output
                
                #gathers the data in the first column
                col=worksheet.col_values(1)
                #goes through the gps coordinates in the spreadsheet, except for the first value as that says location
                for column in col[1:]:
                    #print column
   
                    #extracts the latitude and the longitude data from each row in the  spreadsheet
                    lat2, lon2 = column.split(",")
                    lat2= float(lat2)
                    lon2=float(lon2)
 
                    #print distance(lat, lon, lat2, lon2)
                    if (distance(lat, lon, lat2, lon2)<1000):
                        exists=1
                    else:
                        exists=0
                #if it does not exist
                if exists==0:
                    try:
                        url="https://xively.com/feeds/546310020"
                        values = [output,url]
                        #adds a new row to the spreadsheet with the gps data
                   
                        worksheet.append_row(values)
                        print "Wrote a row to the spreadsheet" 
                        #Wait 30 seconds before continuing
                        time.sleep(30)
                    except:
                        print "Unable to append data.  Check your connection?"
                        sys.exit()
                else:
                    print "The coordinate already exists"
                    time.sleep(100)
            else:
                print "No signal"
        else:
            print "No signal"
            #time.sleep(60)  # Delay for 1 minute (60 seconnds)
    except KeyError:
        pass
    except KeyboardInterrupt:
        sys.exit()
    except StopIteration:
        session = None
        print "GPSD has terminated"


  

