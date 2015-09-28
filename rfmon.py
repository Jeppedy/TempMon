#!/usr/bin/env python
 
# ToDo
# - include PushMon alert pipe in each class definition to allow for selective monitoring by device
# - include Xively Device ID in each class definition to allow flexibility
# - Break out the Temp Sensor handling code from the radio receiving code to allow for completely different uses of RF

import os
import sys
import time
from datetime import datetime
import pytz
import tzlocal
import requests
import urllib2
import json
import RPi.GPIO as GPIO
import sqlite3
import rfmon_house as rfmon_house
import rfmon_commonsensor as rfbase

from nrf24 import NRF24

STATUSCAKE_URL="https://push.statuscake.com/?PK=50bc5a406146489&TestID=510385"

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
      ["F1", "Grill", 60, GRILL_API_KEY, GRILL_FEED_ID, "grill",
        (["1", "pittemp", "PitTemp"], ["2", "food1temp", "Food1Temp"], ["3", "food2temp", "Food2Temp"]) ]
    , ["C1", "Nathan", 600, DEFAULT_API_KEY, DEFAULT_FEED_ID, "nathan",
        (["unused", "", ""], ["1", "humidity", "Humidity"], ["2", "C1_temp", "C1_Temp"]) ]
    , ["C3", "Freezer", 300, DEFAULT_API_KEY, DEFAULT_FEED_ID, "freezer",
        (["1", "temp", "FreezerTemp"], ["unused", "", ""], ["unused", "", ""]) ]
    , ["C5", "Plant",  1800, DEFAULT_API_KEY, DEFAULT_FEED_ID, "plant",
        (["1", "water", "WaterLevel"], ["2", "volts", "Voltage"], ["unused", "", ""]) ]
    , ["C4", "TestUnit", 300, DEFAULT_API_KEY, DEFAULT_FEED_ID, "testunit",
        (["1", "temp", "TestTemp"], ["2", "volts", "Voltage"], ["unused", "", ""]) ]
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

        parms = n.getSensorParms()  # Get info from Sensor class

        doPublish = False
        metricsString= ""
        numTemps = len(tempList)
        for x in range(numTemps):
	    _metricguid = parms[x][1]
	    _metricname = parms[x][2]
	    _metric     = tempList[x]

            if( _metric > 990 or parms[x][0] == "unused" ):
		continue

            # SQLITE DB write
            try:
		conn = sqlite3.connect(DBLOCATION)
		curs = conn.cursor()
		print "Before Execute"
		curs.execute("INSERT INTO rawdata (nodeid, seqnum, metricid, metricguid, metricname, metric, metricdt) VALUES (?,?,?,?,?,?,?) ", \
			( nodeID, seq, parms[x][0], _metricguid, _metricname, _metric, myDateTime))
		print "After Execute"
		conn.commit()  #done by the 'with' statement
		print "After commit"
		curs.close() ;
		print "After cursor close"
            except( sqlite3.OperationalError ) as e:
                print "Error Inserting to DB!({0}:".format(e)
            finally:
                conn.close()

            if( n.needsPublishing(myDateTime) ):
	        # GroveStream metric string build-up
	        metricsString += "&"+_metricguid+"="+str(tempList[x])
                doPublish = True
			
        if( doPublish ):
	    print "- Updating"

            # GroveStream push for all streams for a node (component)
            try:
                url = GROVESTREAMS_URL+"&seq="+str(seq)+"&compId="+n.getComponentID()+metricsString
	        urlhandle = urllib2.urlopen(url) 
	        urlhandle.close() 
                #print( url ) ;
            except( requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
                print "Error updating GroveStreams with RF Data!!({0}): {1}".format(e.errno, e.strerror)

            n.markPublished(myDateTime)
            doPublish = False
        else:
            print "- TOO SOON" 

    radio.startListening()

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
try:
    run()
except KeyboardInterrupt:
    print "Keyboard Interrupt..."
finally:
    print "Exiting."
    GPIO.cleanup()

