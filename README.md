# TempMon
Temperature Monitoring hub running on the RasPi

rfmon.py is deprecated.  We no longer pull from RF and publish to all locations.

rftoq.py and qmon.py took over for rfmon.py

Various publishers can push into the queue
  rftoq.py is one main publisher, reading the RF messages and pushing to the queue
  tempmon.py sends WUnderground temp into the queue
  Future work with ESP8266 WiFi-enabled boards will push directly to the queue

qmon.py then pulls messages from the queue, the single event source, and publishes as needed.

