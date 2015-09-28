#!/usr/bin/env python
 
import os
#import sys
import glob
import subprocess
import time
import datetime
import requests
import RPi.GPIO as GPIO

LED_PIN = 17

DEBUG = False
 
SLEEP_SECONDS = 5

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

 
# main program entry point - runs continuously updating our datastream with the
def run():

  init_GPIO()

  while True:
    myDateTime = datetime.datetime.utcnow() 

    deg_c, deg_f = read_temp()
    print myDateTime, " -> ", "{:4.1f}".format(deg_f)

    time.sleep(SLEEP_SECONDS)
 
run()

