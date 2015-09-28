import time

def getNodeIDFromPayload(payloadIN):
    # Need to parse out NodeID to find which payload parser to use...
    recv_string = ""
    for x in payloadIN:
        recv_string += chr(x)
    string_parts = recv_string.split(",")
    nodeID   = string_parts[0]
    return nodeID


class rfmon_BASE:
    """ Used to test inheritance """

    transmitterID = "TEMPLATE"
    transmitterName = "TEMPLATE_NAME"
    sensorInterval = 60

    # Use "unused" for an unused metric/temperature
    sensorParms =  [ "metricid", "metricguid", "metricname" ]

    _lastPublishedTime = 0
    _node = None
    _seq = None
    _temparray = None

    def getTransmitterID(self):
        return self.transmitterID

    def getSensorInterval(self):
        return self.sensorInterval

    def getSensorParms(self):
        """ Returns only the sensor list for Xively"""
        return self.sensorParms

    def getSensorNodeConfig(self):
        """ DEPRECATED!  Returns the full List as it used to be """
        return [self.sensorInterval, self.sensorParms]

    def needsPublishing(self, dateTimeIn=None):
        """Tells caller whether an update should be published"""
        readyToPub = 0
        if( dateTimeIn == None ):
            dateTimeIn = time.time()

        if( self._lastPublishedTime == 0 ):
            readyToPub = 1
        elif ( (dateTimeIn - self._lastPublishedTime).total_seconds() >= self.getSensorInterval() ):
            readyToPub = 1
        return readyToPub

    def markPublished(self, dateTimeIn=None):
        """Records current time for spacing INet updates"""
        if( dateTimeIn == None ):
            dateTimeIn = time.time()

        self._lastPublishedTime = dateTimeIn
        return
 
    def parsePayload( self, recvBufferIn ):
        """ Returns three parameters after parsing: Node, Interval, parms """
        recv_string = ""
        for x in recvBufferIn:
            recv_string += chr(x)

        string_parts = recv_string.split(",")
        numtemps = len(string_parts) - 2
        ##print "Number of Temps found: [%d]" % numtemps

        self._node = string_parts[0]
        self._seq  = string_parts[1]

        self._temparray = []
        for x in range(2,numtemps+2):
            tempvar = float(string_parts[x])/10
            self._temparray.append( tempvar )

        return self._node, self._seq, self._temparray

    def parsedPayloadDebugString( self, dateTimeIn=None ):
        tempString = ""
        if( dateTimeIn == None ):
            dateTimeIn = time.time()

        tempString = "[%s|%10s] (#%3s) - %s - %s" % \
          (self._node, 
           self.transmitterName,
           self._seq, 
           dateTimeIn.strftime("%Y-%m-%d %H:%M:%S"), 
           repr(self._temparray) 
          )
        return tempString


