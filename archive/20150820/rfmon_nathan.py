import rfmon_sensorbaseclass as BaseClass

class rfmon_nathan(BaseClass.rfmon_BASE):

    transmitterID = "C1"
    transmitterName = "Nathan"
    sensorInterval = 300
    sensorParms = ( ["unused", "", ""],
                    ["1", "humidity", "Humidity"], 
                    ["2", "C1_temp", "C1_Temp"],  
                  )

