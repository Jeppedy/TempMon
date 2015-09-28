import rfmon_sensorbaseclass as BaseClass

class rfmon_nathan(BaseClass.rfmon_BASE):

    transmitterID = "D1"
    transmitterName = "Nathan"
    sensorInterval = 300
    sensorParms = ( ["1", "nate_temp", "Nathan_Temp"],  
                    ["2", "humidity", "Humidity"], 
                    ["unused", "", ""] 
                  )

