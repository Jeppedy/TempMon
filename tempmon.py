#!/usr/bin/env python
 
import os
import sys
import glob
#import xively
import subprocess
import time
from datetime import datetime
import requests
import urllib2
import json
import sqlite3
import RPi.GPIO as GPIO

LED_PIN = 17
# REMEMBER: OneWire is ALWAYS on Pin #4

# FEED_ID = "1785749146"
# API_KEY = "IjPjyGRBNX4215uvu7sAB86NBjCtklQByFAIb1VoJT2TUeXF"
GROVESTREAMS_URL = "http://grovestreams.com/api/feed?asPut&api_key=521dfde4-e9e2-36b6-bf96-18242254873f"

DEBUG = True
 
DBLOCATION="/media/USBHDD1/TempMonData/rfmonDB.db"

COMPONENT = "computerroom"
CHANNEL = "computerroomtemp"
CHANNEL_TAGS = "ComputerRoomTemp"
CHANNELOUT = "outsidetemp"
CHANNELOUT_TAGS = "OutsideTemp"
SLEEP_SECONDS = 60*5+5

#api = xively.XivelyAPIClient(API_KEY)

def init_GPIO():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup( LED_PIN, GPIO.OUT)

def blinkLED( state ):
  GPIO.output( LED_PIN, state )
  
def init_onewire():
  os.system('modprobe w1-gpio')
  os.system('modprobe w1-therm')

  base_dir = '/sys/bus/w1/devices/'
  device_folder = glob.glob(base_dir + '28*')[0]
  device_file = device_folder + '/w1_slave'
  return device_file

def get_device_file():
  if not hasattr(get_device_file, "static_device_file"):
    get_device_file.static_device_file = init_onewire()
  return get_device_file.static_device_file 

def read_temp_raw():
  device_file = get_device_file()

  f = open(device_file, 'r')
  lines = f.readlines()
  f.close()
  return lines

def read_temp():
    blinkLED( True )
    lines = read_temp_raw()
    blinkLED( False )

    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        temp_c = round(temp_c, 1)
        temp_f = round(temp_f, 1)
        return temp_c, temp_f

 
# function to return a datastream object. This either creates a new datastream,
# or returns an existing one
#def xively_getdatastream(ChannelIn, ChannelTagsIn):

#  feed = api.feeds.get(FEED_ID)

#  try:
#    datastream = feed.datastreams.get(ChannelIn)
#    if DEBUG:
#      print "Existing Stream:  Min: ", datastream.min_value, "  Max: ", datastream.max_value, "  Curr: ", datastream.current_value
#    return datastream
#
#  except:
#    if DEBUG:
#      print "Creating new datastream"
#    datastream = feed.datastreams.create(ChannelIn, tags=ChannelTagsIn)
#
#  datastream.max_value = None
#  datastream.min_value = None
#
#  return datastream
#
#
#def xively_update( ChannelIn, ChannelTagsIn, currtemp, currdate ):
#  datastream = xively_getdatastream(ChannelIn, ChannelTagsIn) 
#
#  datastream.at = currdate
#  datastream.current_value = str(currtemp)
#
#  print "Updating Xively ", ChannelIn, ": ", currdate, " -> ",datastream.current_value 
#
#  # Then send them to the server.
#  datastream.update()
#
#  return
#

def utc2local (utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return utc + offset

# main program entry point - runs continuously updating our datastream with the
def run():

  init_GPIO()

  lastUpdateTime = 0

  while True:
    temp_f = 0.0 
    location = ""

    myDateTime = datetime.utcnow() 
    localDateTime = utc2local(myDateTime)

    # WUnderground Update
    try:
      f = urllib2.urlopen('http://api.wunderground.com/api/939d46d3584b09b6/geolookup/conditions/q/KVPZ.json')
      json_string = f.read()
      parsed_json = json.loads(json_string)
      location = parsed_json['location']['city']
      temp_f = parsed_json['current_observation']['temp_f']
    except (requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
      print "Error reading WUnderground info!!({0}): {1}".format(e.errno, e.strerror)

    # Insert reading into DB
    conn = sqlite3.connect(DBLOCATION)
    with conn:
        curs = conn.cursor()
        curs.execute("INSERT INTO rawdata (nodeid, metricid, metricguid, metricname, metric, metricdt) VALUES (?,?,?,?,?,?) ", \
          ( "wu", "1", CHANNELOUT, CHANNELOUT_TAGS, temp_f, localDateTime))
    curs.close()

    if DEBUG:
	print "%s: Current temperature in %s is: %s" % (datetime.now(), location, temp_f)

    if( (time.time() - lastUpdateTime) >= 0 ):
        try:
           url = GROVESTREAMS_URL+"&compId="+COMPONENT+"&"+CHANNELOUT+"="+str(temp_f)
           urlhandle = urllib2.urlopen(url)
           urlhandle.close()
        except( requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
           print "Error updating GroveStreams with RF Data!!({0}): {1}".format(e.errno, e.strerror)

    lastUpdateTime = time.time()

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
try: 
    print datetime.now()
    run()
except KeyboardInterrupt: 
    print "Keyboard Interrupt..."
finally: 
    print "Exiting."
    GPIO.cleanup()

