#!/usr/bin/python
# =========================================
#                 BEGIN
# =========================================

# import the time library.
import time

# record the starting time of initialization.
t_start = time.time()


# =========================================
#             INITIALIZATIONS
# =========================================

# import other necessary libraries.
# import wiringpi
import RPi.GPIO as GPIO
import MAX6675_GPIO as MAX6675
import functions
import csv
import os
import smtplib
import subprocess
from Adafruit_CharLCD import Adafruit_CharLCD
from subprocess import * 

# declare variables.

OUTPUT_NAME = 'temp.csv'        # output file name for temperature data
CONTROL_NAME = 'control.csv'    # input file name for control parameters

# # WiringPi Pin Convention.
# CS0      = 2            # chip select pin for 1st thermocouple
# CS1      = 3            # chip select pin for 2nd thermocouple
# SO       = 1            # output pin
# SCK      = 0            # clock pin
# RelayPin = 4            # relay switch pin

# GPIO BCM Pin Convention.
CS0      = 0            # chip select pin for 1st thermocouple
CS1      = 1            # chip select pin for 2nd thermocouple
SO       = 17            # output pin
SCK      = 4            # clock pin
RelayPin = 8            # relay switch pin

units    = 2            # degree Fahrenheit
size     = 5            # number of temp readings to be averaged

t_control       = 0     # initialize control time
t_alert_high    = 0     # initialize alert_high time
t_alert_desired = 0     # initialize alert_desired time
ControlDelay    = 35    # control delay in second
AlertDelay      = 60    # alert delay in second
tolerance       = 2     # tolerance

# initialize variables.
t     = []          # time
temp0 = []          # 1st temperature
temp1 = []          # 2nd temperature

# # initialize 'wiringpi'.
# wiringpi.wiringPiSetup()

# initialize 'GPIO'.
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RelayPin, GPIO.OUT)

# initialize LCD
lcd = Adafruit_CharLCD()
lcd.begin(16,1)

# IP address
cmd1 = "ip addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"
cmd = "ip addr show wlan0 | grep inet | awk '{print $2}' | cut -d/ -f1"

# remove the old data file if it exists and initalize the new data file.
if os.path.isfile(OUTPUT_NAME):
    os.remove(OUTPUT_NAME)
f = open(OUTPUT_NAME,'wb')
output = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)

# end of initialization.
t_end = time.time()

# print initialization time.
print ( t_end - t_start )


# =========================================
#           CONTROL TEMPERATURES
# =========================================

t_0 = time.time()

# read data from RaspPi, plot the data, and save the data.
while 1 == 1 :
    
    # collect data.
    t.append( round(time.time() - t_0, 1) )                                 # current time round to 1 decimal
    temp0.append( round( functions.readTemp(CS0,SO,SCK,units,size), 1 ) )   # current temperatures round to 1 decimal.
    temp1.append( round( functions.readTemp(CS1,SO,SCK,units,size), 1 ) )

    # save data to the output file 'temp.csv'.
    output.writerow([t[-1], temp0[-1], temp1[-1]])
    f.close()
    f = open(OUTPUT_NAME,'a')
    output = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)

    # print current data.
#    print t[-1], temp0[-1], temp1[-1]
    
    # display temperature on LCD
    lcd.clear()
#    nofile = 1
#    try:
#	ip = open('/var/www/cgi-bin/ipaddress', 'r')
#    except IOError:
#	nofile = 0
#    if nofile:
#	ipaddr = ip.readline()
#	ip.close()
#    else:
#	ipaddr = ''

    ipaddr = functions.run_cmd(cmd)
#    print ipaddr
    if ipaddr == '':
	ipaddr = functions.run_cmd(cmd1)
#	print "ipaddr is empty"
#    print ipaddr
#    if not ipaddr
#	ipaddr = functions.run_cmd(cmd1)
    lcd.message('T1=%sF T2=%sF\n' % ( temp0[-1], temp1[-1] ))
    lcd.message('IP %s' % ( ipaddr ) )
    
    # read the 'control.csv' file.
    g = open(CONTROL_NAME,'rb')
    control_input = csv.reader(g, quoting=csv.QUOTE_NONNUMERIC)
    control_data = [[item for number, item in enumerate(row) if item] for row in control_input]
    g.close()

    if not control_data[0]:                 # set control switch
        control_switch = 0
    else:
        control_switch = 1
    desired_temp   = control_data[1][0]     # set desired temperature
    
    if not control_data[2]:                 # set alert switch
        alert_switch = 0
    else:
        alert_switch = 1
    alert_high    = control_data[3][0]      # set the maximum temperature limit for alert
    alert_desired = control_data[4][0]      # set the desired temperature limit for alert
    
    # uncomment to print control variables.
#    print control_switch, desired_temp, tolerance, alert_switch, alert_high, alert_desired


    # ===================
    # ===================
    # the control system
    # ===================
    # ===================
    
    # --------------------------------------
    # PART I:  The Instant-Response Version
    # --------------------------------------
    
#    functions.controller(control_switch, desired_temp, temp1[-1], tolerance)

    # -----------------------------------------------
    # PART II: The Delayed-Response Version (Default)
    # -----------------------------------------------

    # control switch
    if (control_switch == 1) & ( (t_control == 0) | (t[-1]-t_control  >= ControlDelay) ):
        # start control
        t_control = t[-1]
        if ( temp1[-1] - desired_temp ) < -tolerance:
#             wiringpi.digitalWrite(RelayPin,1)
            GPIO.output(RelayPin,1)
        elif ( temp1[-1] - desired_temp ) > tolerance:
#             wiringpi.digitalWrite(RelayPin,0)
            GPIO.output(RelayPin,0)


    # ===================
    # ===================
    # the alert system
    # ===================
    # ===================

    # alert switch
    if alert_switch == 1:
        
        # send out high temperature alert
        if (temp0[-1] >= alert_high)    &    ( (t_alert_high == 0) | (t[-1]-t_alert_high >= AlertDelay) ):
            t_alert_high = t[-1]
            #server = smtplib.SMTP("smtp.gmail.com", 587)
            #server.starttls()
            #server.login('rp.smartbbq@gmail.com', '030206raspberrypi')
            #server.sendmail('Smart BBQ', '5107177937@smtext.com', 'Your meat needs care! The temperature is above ' + str(alert_high) + ' F')
	    print "trying to send a tweet"
            tweetcommand = "/usr/local/bin/twitter -erp.smartbbq@gmail.com set Your meat needs care! %s" % (int(t[-1]))
            subprocess.call(tweetcommand, shell=True)

        # send out desired temperature alert
        if ( (alert_desired-tolerance) <= temp1[-1] )   &   ( (t_alert_desired == 0) | (t[-0]-t_alert_desired >= AlertDelay) ):
            t_alert_desired = t[-1]
            #server = smtplib.SMTP("smtp.gmail.com", 587)
            #server.starttls()
            #server.login('rp.smartbbq@gmail.com', '030206raspberrypi')
            #server.sendmail('Smart BBQ', '5107177937@smtext.com', 'Your meat has the desired temperature. Enjoy!')
	    print "trying to send a tweet!"
	    tweetcommand = "/usr/local/bin/twitter -erp.smartbbq@gmail.com set Your meat is almost done %s" % (int(t[-1]))
	    subprocess.call(tweetcommand, shell=True)