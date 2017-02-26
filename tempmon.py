#!/usr/bin/env python
 
import os
import sys
import glob
import time
from datetime import datetime
import requests
import urllib2
import json
import ConfigParser

import paho.mqtt.client as mqtt


UNITID = "O1"
COMPONENT = "raspi"
CHANNELOUT = "outsidetemp"
GROVESTREAMS_URL = "http://grovestreams.com/api/feed?asPut&api_key=521dfde4-e9e2-36b6-bf96-18242254873f"

# ---- Globals ----
IsConnected=False
IsCnxnErr=False

SLEEP_SECONDS = 60*5+5

config = None

# ----------------------------------------------------------------
def getConfigExt( configSysIn, sectionIn, optionIn, defaultIn=None ):
    optionOut=defaultIn
    if( configSysIn.has_option( sectionIn, optionIn)):
        optionOut = configSysIn.get(sectionIn, optionIn)
    return optionOut

def getConfigExtBool( configSysIn, sectionIn, optionIn, defaultIn=False ):
    optionOut=defaultIn
    if( configSysIn.has_option( sectionIn, optionIn)):
        optionOut = configSysIn.getboolean(sectionIn, optionIn)
    return optionOut


def on_connect(client, userdata, flags, rc):
    global IsConnected,IsCnxnErr
    print("CB: Connected;rtn code [%d]"% (rc) )
    if( rc == 0 ):
        IsConnected=True
    else:
        IsCnxnErr=True

def on_disconnect(client, userdata, rc):
    global IsConnected
    print("CB: Disconnected with rtn code [%d]"% (rc) )
    IsConnected=False

def on_publish(client,userdata,mid):
    print("Data Published, Msg ID: [%d]" % mid)
    pass

def on_log(client, userdata, level, buf):
    print("log: ",buf)


def utc2local (utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return utc + offset

# main program entry point - runs continuously updating our datastream with the
def run( client ):

  client.on_publish = on_publish
  client.on_connect = on_connect
  client.on_disconnect = on_disconnect
  if( getConfigExtBool(config, "DEFAULT", 'qlog_enable') ):
      client.on_log = on_log
  if( getConfigExt(config, "DEFAULT", 'user', None) and getConfigExt(config, "DEFAULT", 'pswd', None) ):
      print( "Setting User and pswd")
      client.username_pw_set( config.get("DEFAULT", 'user'), config.get("DEFAULT", 'pswd') )

  client.connect(config.get("DEFAULT", 'broker'), config.get("DEFAULT", 'port'), 60)

  client.loop_start()

  retry=0
  while( (not IsConnected) and (not IsCnxnErr) and retry <= 10):
      print("Waiting for Connect")
      time.sleep(.05)
      retry += 1
  if( not IsConnected or IsCnxnErr ):
      print("No connection could be established")
      return


  while True:
    temp_f = 0.0 
    location = ""

    # WUnderground Update
    try:
      f = urllib2.urlopen( config.get("DEFAULT", 'wunderground_url') )
      json_string = f.read()
      parsed_json = json.loads(json_string)
      location = parsed_json['location']['city']
      temp_f = parsed_json['current_observation']['temp_f']
    except (requests.exceptions.ConnectionError, requests.HTTPError, urllib2.URLError) as e:
      print "Error reading WUnderground info!!({0}): {1}".format(e.errno, e.strerror)

    if ( getConfigExtBool(config, "DEFAULT", 'debug') ) :
	print "%s: Current temperature in %s is: %s" % (datetime.now(), location, temp_f)

    msgToSend = "%s,%03d,%04d,9990,9990" % (UNITID,0,temp_f*10)
    if ( getConfigExtBool(config, "DEFAULT", 'debug') ) :
	print "%s: %s" % (datetime.now(), msgToSend)

    if( not IsConnected ):
        print( "ERROR: RF Msg received; NO CONNECTION to queue" )
    else:
        client.publish(config.get("DEFAULT", 'topic'), msgToSend)

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
# -------------------------------------

client = mqtt.Client(__file__)

try: 
    configFile=os.path.splitext(__file__)[0]+".conf"
    if( not os.path.isfile( configFile )):
        print( "Config file [%s] was not found.  Exiting" ) % configFile
        exit()

    config = ConfigParser.SafeConfigParser()
    config.read(configFile)
    if( getConfigExtBool(config, "DEFAULT", 'debug') ):
        print("Using config file [%s]") % configFile

    if ( getConfigExtBool(config, "DEFAULT", 'debug') ) :
        print datetime.now()

    run( client )

except KeyboardInterrupt: 
    print "Keyboard Interrupt..."
finally: 
    print "Exiting."

    time.sleep(.25)
    client.disconnect()
    while( IsConnected ):
        print("Waiting for Disconnect")
        time.sleep(.05)
    client.loop_stop()

