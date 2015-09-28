import os
import sys
import glob
import time
import datetime
import xively
import requests
#import subprocess
#import urllib2
#import json
#import threading

FEED_ID = "1785749146"
API_KEY = "IjPjyGRBNX4215uvu7sAB86NBjCtklQByFAIb1VoJT2TUeXF"
DEBUG = False
 
def xively_getAPI():
  if not hasattr(xively_getAPI, "api_"):
    xively_getAPI.api_ = xively.XivelyAPIClient(API_KEY)
  return xively_getAPI.api_

def xively_getFeed():
  if not hasattr(xively_getFeed, "feed_"):
    xively_getFeed.feed_ = xively_getAPI().feeds.get(FEED_ID)
  return xively_getFeed.feed_

# function to return a datastream object. This either creates a new datastream,
# or returns an existing one
def xively_getdatastream(ChannelIn, ChannelTagsIn):

  feed =  xively_getFeed()

  try:
    datastream = feed.datastreams.get(ChannelIn)
    if DEBUG:
      print "Existing Stream:  Min: ", datastream.min_value, "  Max: ", datastream.max_value, "  Curr: ", datastream.current_value
    return datastream

  except:
    if DEBUG:
      print "Creating new datastream"
    datastream = feed.datastreams.create(ChannelIn, tags=ChannelTagsIn)

  datastream.max_value = None
  datastream.min_value = None

  return datastream


def xively_update( ChannelIn, ChannelTagsIn, currtemp, currdate ):
  datastream = xively_getdatastream(ChannelIn, ChannelTagsIn) 

  datastream.at = currdate
  datastream.current_value = str(currtemp)

  if DEBUG:
    print "Updating Xively ", ChannelIn, ": ", currdate, " -> ",datastream.current_value 

  try:
    # Then send them to the server.
    datastream.update()
  except (requests.exceptions.ConnectionError, requests.HTTPError) as e:
    print "Error!!({0}): {1}".format(e.errno, e.strerror)

  return
