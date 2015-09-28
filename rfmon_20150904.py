#!/usr/bin/env python
 
# ToDo
# - include PushMon alert pipe in each class definition to allow for selective monitoring by device
# - include Xively Device ID in each class definition to allow flexibility
# - Break out the Temp Sensor handling code from the radio receiving code to allow for completely different uses of RF

import os
import sys
import time
from datetime import datetime
#from pytz import timezone
import pytz
import tzlocal
import requests
import urllib2
import json
import RPi.GPIO as GPIO
import sqlite3
#import rfmon_xively as xive
import rfmon_house as rfmon_house
import rfmon_commonsensor as rfbase

from nrf24 import NRF24

STATUSCAKE_URL="https://push.statuscake.com/?PK=50bc5a406146489&TestID=510385"
#STATUSCAKE_URL="https://push.statuscake.com/?PK=50bc5a406146489&TestID=510385&time=0"

PUSHMON_URL="http://ping.pushmon.com/pushmon/ping/"
PUSHMON_ID="WmpnHI"
PUSHINGBOX_URL="http://api.pushingbox.com/pushingbox"
PUSHINGBOX_ID="vF6098C58E4A4D96"

GROVESTREAMS_URL = "http://grovestreams.com/api/feed?asPut&api_key=521dfde4-e9e2-36b6-bf96-18242254873f"

DBLOCATION="/media/USBHDD1/TempMonData/rfmonDB.db"

DEFAULT_API_KEY = "IjPjyGRBNX4215uvu7sAB86NBjCtklQByFAIb1VoJT2TUeXF"
DEFAULT_FEED_ID = "1785749146"

GRILL_API_KEY   = "JEksVghaisFnIpO6NyQM51ITpVeKZ5K1r8xZEBc934zZtDsl"
GRILL_FEED_ID   = "1130159067"

# REMEMBER: OneWire is ALWAYS on Pin #4

##  RF Read Code
pipes = [[0xF0, 0xF0, 0xF0, 0xF0, 0xE1], [0xF0, 0xF0, 0xF0, 0xF0, 0xD1]]
CE_PIN_       = 25  #18
IRQ_PIN_      = 23
RF_CHANNEL    = 76
PAYLOAD_SIZE  = 21

SLEEP_SECONDS = 1 

radio = NRF24()

def init_GPIO():
    GPIO.setmode(GPIO.BCM)

def initRadioReceive():
    radio.begin(0, 0, CE_PIN_, IRQ_PIN_)

    #radio.setDataRate(NRF24.BR_1MBPS)
    radio.setDataRate(NRF24.BR_250KBPS)
    radio.setPALevel(NRF24.PA_MAX)
    radio.setChannel(RF_CHANNEL)
    radio.setRetries(15,15)
    radio.setAutoAck(0)
    radio.setPayloadSize(PAYLOAD_SIZE)
    ##radio.enableDynamicPayloads()

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1, pipes[1])

    radio.startListening()
    radio.stopListening()
    radio.printDetails()
    print "-"*40

    radio.startListening()


def initSensors( sensorArrayIn ):
  sensorList = (  
      ["F1", "Grill", 300, GRILL_API_KEY, GRILL_FEED_ID, "grill",
        (["1", "pittemp", "PitTemp"], ["2", "food1temp", "Food1Temp"], ["3", "food2temp", "Food2Temp"]) ]
    , ["C1", "Nathan", 600, DEFAULT_API_KEY, DEFAULT_FEED_ID, "nathan",
        (["unused", "", ""], ["1", "humidity", "Humidity"], ["2", "C1_temp", "C1_Temp"]) ]
    , ["C3", "Freezer", 300, DEFAULT_API_KEY, DEFAULT_FEED_ID, "freezer",
        (["1", "temp", "FreezerTemp"], ["unused", "", ""], ["unused", "", ""]) ]
    , ["A2", "Aquarium", 300, DEFAULT_API_KEY, DEFAULT_FEED_ID, "aquarium",
        (["1", "house", "House"], ["2", "aquarium", "Aquarium"], ["unused", "", ""]) ]
               ) 

  for y in sensorList:
    x = rfbase.rfmon_BASE( y[0], y[1], y[2], y[3], y[4], y[5], y[6] )
    sensorArrayIn[x.getTransmitterID()] = x

  # Add the unique House Monitor
  x = rfmon_house.rfmon_house( "C2", "housetemp", 300, DEFAULT_API_KEY, DEFAULT_FEED_ID, "house",
        (["1", "house", "House", 0], ["2", "hvac", "HVAC", 1.0], ["3", "furnace", "Furnace", 0]) 
      )
  sensorArrayIn[x.getTransmitterID()] = x

  #print sensorArrayIn
  


# main program entry point - runs continuously updating our datastream with the
def run():

  init_GPIO()
  initRadioReceive()

  conn = sqlite3.connect(DBLOCATION)
  curs = conn.cursor()

  newSensors = {}
  initSensors( newSensors ) 

  while True:
    pipe = [1]
    while( radio.available(pipe, False) ):
        recv_buffer = []
        myDateTime = datetime.utcnow().replace(tzinfo=pytz.utc);

        radio.read(recv_buffer)
	#print "[%s]" % recv_buffer


        nodeID = rfbase.getNodeIDFromPayload(recv_buffer)
	#print "Node: [%s]" % nodeID
        if( nodeID not in newSensors ):
            print "No match found for Node {0}".format(nodeID)
            continue

        n = newSensors[nodeID]
        nodeID, seq, tempList = n.parsePayload( recv_buffer )  # Get info from packet
        print "[", nodeID, "] ", seq, "-", myDateTime.astimezone(tzlocal.get_localzone()).strftime("%Y-%m-%d %H:%M:%S %Z"), ": ", tempList,  # trailing comma says no NEWLINE


        if( n.needsPublishing(myDateTime) ):
            print "- Updating"

#	    if( n.getTransmitterID() == "C3" ):
#                try:
#                    # Send proactive ping to a monitoring service
#                    url = PUSHMON_URL+PUSHMON_ID
#                    urlhandle = urllib2.urlopen(url) 
#                    urlhandle.close() 
#                except urllib2.HTTPError as e:
#                    print "PushMon returned error [", e.code, "]"
#                    # Tell an alerting service that PushMon is not accepting our Pings
#                    url = PUSHINGBOX_URL+"?devid="+PUSHINGBOX_ID+"&svc=pushmon.com"+"&rtncode="+str(e.code)
#                    urlhandle = urllib2.urlopen(url) 
#                    urlhandle.close() 
#
#                try:
#                    # Send proactive ping to StatusCake  monitoring service
#                    url = STATUSCAKE_URL+"&time="+str(int(seq)*1000)  # send the sequence number as the time param to track gaps
#                    urlhandle = urllib2.urlopen(url) 
#                    urlhandle.close() 
#                except urllib2.HTTPError as e:
#                    print "StatusCake returned error [", e.code, "]"
#                    # Tell an alerting service that StatusCake is not accepting our Pings
#                    url = PUSHINGBOX_URL+"?devid="+PUSHINGBOX_ID+"&svc=StatusCake"+"&rtncode="+str(e.code)
#                    urlhandle = urllib2.urlopen(url) 
#                    urlhandle.close() 

            numTemps = len(tempList)
            parms = n.getSensorParms()  # Get info from Sensor class
	    metricsString= ""
            for x in range(numTemps):
		_metricguid = parms[x][1]
		_metricname = parms[x][2]
		_metric     = tempList[x]
                if( tempList[x] < 900 and parms[x][0] <> "unused" ):
		    # GroveStream metric string build-up
	            metricsString += "&"+_metricguid+"="+str(tempList[x])
			
#                    try:
#                        xive.xively_update( n.getAPIKey(), n.getFeedID(), parms[x][1], parms[x][2], tempList[x], myDateTime ) 
#                    except( requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
#                      print "Error updating Xively with RF Data!!({0}): {1}".format(e.errno, e.strerror)

		    # SQLITE DB write
                    curs.execute("INSERT INTO rawdata (nodeid, metricid, metricguid, metricname, metric, metricdt) VALUES (?,?,?,?,?,?) ", \
                       ( nodeID, parms[x][0], parms[x][1], parms[x][2], tempList[x], myDateTime))
                    conn.commit()

	    # GroveStream push for all streams for a node (component)
	    try:
	       url = GROVESTREAMS_URL+"&seq="+str(seq)+"&compId="+n.getComponentID()+metricsString
	       urlhandle = urllib2.urlopen(url) 
	       urlhandle.close() 
	    except( requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
	      print "Error updating GroveStreams with RF Data!!({0}): {1}".format(e.errno, e.strerror)

	    n.markPublished(myDateTime)

        else:
            print "- TOO SOON" 



    radio.startListening()

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
try:
    testp = requests.exceptions.ConnectionError ()

    run()
except KeyboardInterrupt:
    print "Keyboard Interrupt..."
finally:
    print "Exiting."
    GPIO.cleanup()

