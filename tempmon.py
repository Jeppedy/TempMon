#!/usr/bin/env python
 
import os
import sys
import glob
import time
from datetime import datetime
import requests
import urllib2
import json
import paho.mqtt.client as mqtt


COMPONENT = "computerroom"
CHANNELOUT = "outsidetemp"
GROVESTREAMS_URL = "http://grovestreams.com/api/feed?asPut&api_key=521dfde4-e9e2-36b6-bf96-18242254873f"

Q_CLIENTID="tempmon"
Q_BROKER="m11.cloudmqtt.com"
Q_PORT=19873
Q_USER="prcegtgc"
Q_PSWD="7frPa1U_VXqA"
Q_TOPIC="hello"

DEBUG = True
 
SLEEP_SECONDS = 60*5+5

def on_connect(client, userdata, flags, rc):
    print("Connected with result code [%d]" % rc)

def on_publish(client,userdata,mid):
    print("Data Published, Msg ID: [%d]" % mid)
    pass

def utc2local (utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return utc + offset

# main program entry point - runs continuously updating our datastream with the
def run():

  client = mqtt.Client(Q_CLIENTID)
  client.on_publish = on_publish
  client.on_connect = on_connect
  client.username_pw_set(Q_USER, Q_PSWD)

  while True:
    temp_f = 0.0 
    location = ""

    #myDateTime = datetime.utcnow() 
    #localDateTime = utc2local(myDateTime)

    # WUnderground Update
    try:
      f = urllib2.urlopen('http://api.wunderground.com/api/939d46d3584b09b6/geolookup/conditions/q/KVPZ.json')
      json_string = f.read()
      parsed_json = json.loads(json_string)
      location = parsed_json['location']['city']
      temp_f = parsed_json['current_observation']['temp_f']
    except (requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
      print "Error reading WUnderground info!!({0}): {1}".format(e.errno, e.strerror)

    if DEBUG:
	print "%s: Current temperature in %s is: %s" % (datetime.now(), location, temp_f)

    try:
        url = GROVESTREAMS_URL+"&compId="+COMPONENT+"&"+CHANNELOUT+"="+str(temp_f)
#       urlhandle = urllib2.urlopen(url)
#       urlhandle.close()
    except( requests.exceptions.ConnectionError, requests.HTTPError) as e:
        print "Error updating GroveStreams with RF Data!!({0}): {1}".format(e.errno, e.strerror)

    client.connect(Q_BROKER, Q_PORT, keepalive=60)
    msgToSend = str(datetime.now())+"  compId="+COMPONENT+"&"+CHANNELOUT+"="+str(temp_f)
    client.publish(Q_TOPIC,msgToSend)
    client.disconnect()

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
try: 
    print datetime.now()
    run()
except KeyboardInterrupt: 
    print "Keyboard Interrupt..."
finally: 
    print "Exiting."

