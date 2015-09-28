#!/usr/bin/env python
 
import os
import sys
import time
import datetime
import requests
import urllib2
import json

SLEEP_SECONDS = 10

# main program entry point - runs continuously updating our datastream with the
def run():

  while True:
    url = "http://google.com"
    urlhandle = urllib2.urlopen(url) 
    urlrtn = urlhandle.read() 
    print "Calling PushMon"
    #print "Got Return: ", urlrtn 
    urlhandle.close() 

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
try:
    run()
except KeyboardInterrupt:
    print "Keyboard Interrupt..."
finally:
    print "Exiting."

