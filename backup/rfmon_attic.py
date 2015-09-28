import rfmon_sensorbaseclass as BaseClass

class rfmon_attic(BaseClass.rfmon_BASE):

    transmitterID = "C3"
    transmitterName = "Attic"
    sensorInterval = 120
    sensorParms = ( ["1", "attic", "Attic"],  
                    ["unused", "", ""], 
                    ["unused", "", ""] 
                  )

