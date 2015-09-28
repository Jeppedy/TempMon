#!/usr/bin/env python
 
import os
import sys
import time
import datetime
import requests
import urllib2
import json
import RPi.GPIO as GPIO
import rfmon_xively as xive
import rfmon_aquarium as rfmon_aquarium
import rfmon_nathan as rfmon_nathan
import rfmon_attic as rfmon_attic
import rfmon_sensorbaseclass as rfbase

from nrf24 import NRF24

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
  for y in [rfmon_aquarium.rfmon_aquarium, rfmon_nathan.rfmon_nathan, rfmon_attic.rfmon_attic]:
    x = y()
    sensorArrayIn[x.getTransmitterID()] = x


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
        myDateTime = datetime.datetime.utcnow() 

        radio.read(recv_buffer)
	#print "[%s]" % recv_buffer
        nodeID = rfbase.getNodeIDFromPayload(recv_buffer)
	#print "Node: [%s]" % nodeID
        if( nodeID not in newSensors ):
            print "No match found for Node {0}".format(nodeID)
            continue

        n = newSensors[nodeID]
        nodeID, seq, tempList = n.parsePayload( recv_buffer )  # Get info from packet
        print "[", nodeID, "] ", seq, " - ", myDateTime, ":  ", tempList,  # trailing comma says no NEWLINE

        if( n.needsPublishing(myDateTime) ):
            print "- Updating"

            numTemps = len(tempList)
            parms = n.getSensorParms()  # Get info from Sensor class
            for x in range(numTemps):
                if( tempList[x] < 900 and parms[x][0] <> "unused" ):
                    try:
                        xive.xively_update( parms[x][1], parms[x][2], tempList[x], myDateTime ) 
                        n.markPublished(myDateTime)
                    except( requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
                      print "Error updating Xively with RF Data!!({0}): {1}".format(e.errno, e.strerror)
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

