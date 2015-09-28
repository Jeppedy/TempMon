import rfmon_sensorbaseclass

class rfmon_aquarium(rfmon_sensorbaseclass.rfmon_BASE):

    transmitterID = "A2"
    transmitterName = "aquarium"
    sensorInterval = 60
    sensorParms = ( ["1", "house", "House", 0.0], 
                    ["2", "hvac", "HVAC", 1.0],   
                    ["unused", "", "", 0.0], 
                    ["unused", "", "", 0.0] 
                  )

    def THIS_IS_HOW_TO_OVERRIDE_PAYLOAD_PARSING_parsePayload( self, recvBufferIn ):
        """ Returns three parameters after parsing: Node, Interval, parms """
        recv_string = ""
        for x in recvBufferIn:
            recv_string += chr(x)

        ##print recv_string

        string_parts = recv_string.split(",")
        numtemps = len(string_parts) - 2

        ##print "Number of Temps found: [%d]" % numtemps
        numtemps = numtemps - 1  # replacing the final temperature

        self._node = string_parts[0]
        self._seq  = string_parts[1]

        self._temparray = []
        for x in range(2,numtemps+2):
            tempvar = (float(string_parts[x])/10)+self.sensorParms[x-2][3]
            self._temparray.append( tempvar )

        # Appending a computed Temp Differential
        # Remote sensor minus room sensor
        tempDiff = (self._temparray[1]-self._temparray[0])
        self._temparray.append( tempDiff ) 

        if( tempDiff > 15 ):
            self._temparray.append( 1 ) 
        elif( tempDiff < -10 ):
            self._temparray.append( 1 ) 
        else:
            self._temparray.append( 0 ) 
            

        ##print "Computed Differential: [%f]" % tempDiff
        ##print self._temparray

        return self._node, self._seq, self._temparray
