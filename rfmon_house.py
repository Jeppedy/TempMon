import rfmon_commonsensor

lTransmitterID = "C2"
lTransmitterName = "housetemp"
lSensorInterval = 60
lSensorParms = ( ["1", "house", "House", 0.0], 
	        ["2", "hvac", "HVAC", 1.0],   
	        ["3", "furnace", "Furnace", 0.0] 
	      )

class rfmon_house(rfmon_commonsensor.rfmon_BASE):

    def __init__(self, lTransmitterID, lTransmitterName, lSensorInterval, lAPIKey, lFeedID, lComponentID,  lSensorParms):
        super(rfmon_house, self).__init__(lTransmitterID, lTransmitterName, lSensorInterval, lAPIKey, lFeedID, lComponentID, lSensorParms)

    def parsePayload( self, recvBufferIn ):
        """ Returns three parameters after parsing: Node, Interval, parms """
        recv_string = ""
        for x in recvBufferIn:
            recv_string += chr(x)
        #print recv_string

        string_parts = recv_string.split(",")
        numtemps = len(string_parts) - 2

        #print "Number of Temps found on recv string: [%d]" % numtemps
        numtemps = numtemps - 1  # replacing the final temperature

        self._node = string_parts[0]
        self._seq  = string_parts[1]

        self._temparray = []
        for x in range(2,numtemps+2):
            tempvar = (float(string_parts[x])/10)+self._sensorParms[x-2][3]
            self._temparray.append( tempvar )

        # Remote sensor minus room sensor
        tempDiff = (self._temparray[1]-self._temparray[0])

        if( tempDiff > 15 ):
            self._temparray.append( 1 ) 
        elif( tempDiff < -10 ):
            self._temparray.append( 1 ) 
        else:
            self._temparray.append( 0 ) 
            

        #print "Number of Temps now: [%d]" % len(self._temparray)
        #print self._temparray

        return self._node, self._seq, self._temparray

