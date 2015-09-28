import rfmon_sensorbaseclass as BaseClass

class rfmon_grill(BaseClass.rfmon_BASE):

    transmitterID = "F1"
    transmitterName = "Grill"
    sensorInterval = 30   # in Seconds
    sensorParms = ( ["1", "pittemp", "PitTemp"],  
                    ["2", "food1temp", "Food1Temp"], 
                    ["3", "food2temp", "Food2Temp"] 
                  )

