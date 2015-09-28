import rfmon_sensorbaseclass as BaseClass

class rfmon_freezer(BaseClass.rfmon_BASE):

    transmitterID = "C3"
    transmitterName = "Freezer"
    sensorInterval = 60   # in Seconds
    sensorParms = ( ["1", "freezer", "Freezer"],  
                    ["unused", "", ""], 
                    ["unused", "", ""] 
                  )

