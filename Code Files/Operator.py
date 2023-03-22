import pandas as pd
import numpy as np
# import PySimpleGUI as sg
import allantools # Documentation: https://pypi.org/project/AllanTools/
from Allan_Variance import allan_variance, params_from_avar # Documentation: https://github.com/nmayorov/allan-variance
# from OSA import OSA
# from LASER import Laser
# import threading
import matplotlib.pyplot as plt
import os
# from json import load, dump
from time import sleep
import time
# import pylab as plb
# from GUI import enterSubstanceToMeasure
from datetime import datetime

#Globals
global numOfMeasurments
global wavelengths
global debugMode

rep_values_MHz = {1: '78.56MHz', 2: '39.28MHz', 3: '29.19MHz', 4: '19.64MHz', 5: '15.71MHz',
            6: '13.09MHz', 7: '11.22MHz', 8: '9.821MHz', 9: '8.729MHz', 10: '7.856MHz',
            12: '6.547MHz', 14: '5.612MHz', 16: '4.910MHz', 18: '4.365MHz', 20: '3.928MHz',
            22: '3.571MHz', 25: '3.143MHz', 27: '2.910MHz', 29: '2.709MHz', 32: '2.455MHz',
            34: '2.311MHz', 37: '2.123MHz', 40: '1.964MHz'}

# Sample Managment: ----------------------------------------------------------------------------------------------

def setConfig(laser,osa,cf,span,points,speed,power,rep):
    configureLaser(laser,power,rep)
    configureOSA(osa,cf,span,points,speed)

def configureLaser(laser, power,rep):
    if not debugMode:
        # Setting repetition rate
        laser.pulsePickerRation(rep_values_MHz[rep])
        sleep(1)
        laser.powerLevel(int(power))

def configureOSA(osa, cf,span,points,speed):
    if not debugMode:
        convertDict = {
            "SPEED": {"Normal": "x1", "Fast": "x2"}
        }
        # Set center frequency
        osa.setCenterFreq(cf)
        sleep(1)
        # Set Span
        osa.setSpan(span)
        sleep(1)
        # Set number of sampling points
        if (points == "Auto (500)"):
            points = "auto on"
        osa.setPoints(points)
        sleep(1)
        # Set sampling speed
        osa.setSpeed(convertDict["SPEED"][speed])
        sleep(1)

# End Sample Managment: ----------------------------------------------------------------------------------------------

# Tests Managment: ----------------------------------------------------------------------------------------------

def getReps(values):
    # returns all the reptition rate keys that are checked True
    rep_keys = ["r"+str(k) for k in range(1,41,1)]
    reps = []
    for rep_key in rep_keys:
        try:
            if values[rep_key]:
                # Key exists and value is True
                reps.append(int(rep_key[1:]))
        except:
            continue
    return reps

def meanMeasure(laser,osa ,numOfSamples,numOfDots):
    if not debugMode:
        measuretList = []
        resultList = []
        for i in numOfSamples:
            sleep(0.2)
            osa.sweep()
            data = osa.getCSVFile("noiseMeasurment")
            data_decoded = data.decode("utf-8")
            data_decoded = data_decoded.split("\r\n")
            smpls = data_decoded[39:-2]
            wavelengths = [float(pair.split(",")[0]) for pair in smpls]
            measurment = [float(pair.split(",")[1]) for pair in smpls]
            measuretList.append(measurment)
        i = 0
        j = 0
        while (i < numOfDots):
            sum = 0
            while (j < numOfSamples):
                sum += measuretList[j][i]
                j = j+1
            resultList.append(sum/numOfSamples)
            j = 0
            i = i+1
        return resultList
    return np.random.rand(numOfDots)*(-100)

def noiseMeasurments(laser,osa, numOfDots,noiseNum=3):
    # Here we are taking in mind that the laser and the OSA are already configed.
    laser.emission(0)
    print("Noise measurment, please wait...")
    sleep(0.5)
    darkMeasurment = meanMeasure(laser,osa ,noiseNum,numOfDots)
    return darkMeasurment

def emptyMeasurments(laser,osa, numOfDots,emptyNum=3):
    # Here we are taking in mind that the laser and the OSA are already configed.
    laser.emission(1)
    print("Empty measurment, please wait...")
    sleep(0.5)
    emptyMeasurment = meanMeasure(laser,osa ,emptyNum,numOfDots)
    return emptyMeasurment

def laserMeasurment(laser,osa, numOfSamples,numOfDots,darkMeasurment=0,emptyMeasurment=0):
    laser.emission(1)
    sleep(0.5)
    # print("Starting measurment, please wait...")
    measurment = meanMeasure(laser,osa ,numOfSamples,numOfDots)
    if (darkMeasurment != 0):
        measurment -= darkMeasurment
    if (emptyMeasurment != 0):
        measurment -= emptyMeasurment
    return measurment

#def CSVFilecreator():
#    skip

#def analyizer():
#    skip

#def plotResults():
#    skip

def getTime():
    time = str(datetime.today())
    time = time.replace('-', '_')
    time = time.replace(' ', '_')
    time = time.replace(':', '_')
    time = time.replace('.', '_')
    return time

def testManagment(laser,osa,values,debug):
    global debugMode
    debugMode = debug
    # This function will manage all the test process and call to all the relevant functions.
    # enterSubstanceToMeasure()
    reps = getReps(values)
    if values["test_PTS"] == "Auto (500)":
        pts = 500
    else:
        pts = int(values["test_PTS"])
    setConfig(laser,osa,values["test_CF"],values["test_SPAN"], pts, values['test_SPD'], values["minPL"], reps[0])
    start = int(values["minPL"])
    if (values["testPowerLevelSweep"]):
        stop = int(values["maxPL"])
        step = int(values["stepPL"])
    else:
        stop = start + 1
        step = 1
    powers = range(start,stop,step)
    
    # Making the CSV File
    startF = int(values["CF"]) - int(values["SPAN"])/2
    stopF = startF + int(values["SPAN"])
    freqs_columns = [str(freq) for freq in np.arange(startF,stopF,int(values["SPAN"])/pts)]
    allResults_df =  pd.DataFrame(columns=['Date', 'Comment', 'CF',	'SPAN',	'REP_RATE',	'POWER', 'Start Power (I0)','End Power (I)', 'I/I0 Ratio', 'SAMPLINGS_NUMBER']+freqs_columns)

    # Start the tests:
    for freq in reps:
        for p in powers:
            configureLaser(laser, p,freq)
            if not debugMode:
                laser.emission(1)
            result = meanMeasure(laser,osa, values["numSamplesParameter"],pts)
            if not debugMode:
                laser.emission(0)
            laserPower = calculateLaserLightPower(p,freq)
            capturePower = calculateCaptureLightPower()
            # Preparing new row for allResults
            new_row = []
            new_row.append(getTime())
            new_row.append(values["TEST1_COMMENT"])
            new_row.append(values["CF"])
            new_row.append(values["SPAN"])
            new_row.append(rep_values_MHz[freq])
            new_row.append(p)
            new_row.append(laserPower)
            new_row.append(capturePower)
            new_row.append(capturePower/laserPower)
            new_row.append(values["numSamplesParameter"])
            new_row = new_row + list(result)
            # Append the new row to the dataframe
            allResults_df.loc[len(allResults_df)] = new_row

    allResults_df.to_csv(getTime()+"_"+values["TEST1_COMMENT"]+'.csv', index=False)


# This function responsibles for Beer-Lambert Law:

def calculateCaptureLightPower():
    return True # OSA - Power of capture light

def calculateLaserLightPower(power,frequency):
    return True
def calculateConcentrationOfSubstance():
    return True

def beerLambertLaw(laserpower):
    calculateCaptureLightPower()
    calculateLaserLightPower(laserpower)
    calculateConcentrationOfSubstance()

# End Tests Managment: ----------------------------------------------------------------------------------------------

# Sample function:

def runSample(laser,osa, isConnected,debugMode, values):
    if ( isConnected or (not debugMode) ):
        laser.emission(1)
        print("Waiting 5 seconds for Laser to start TX\n")
        sleep(5)
        #performing a sweep (like a sample)
        osa.sweep()
        #getting to data the swept values
        data = osa.getCSVFile(values["sample_name"])
        data_decoded = data.decode("utf-8")
        data_decoded = data_decoded.split("\r\n")

        print("Stop laser TX and return power to 6%\n")
        laser.emission(0)
        laser.powerLevel(6)
    else:
        # If in debug mode
        with open("debug_sample.csv", "r") as f:
            data = f.read()
            data_decoded = data.split("\n")

    smpls = data_decoded[39:-2]
    wavelengths = [float(pair.split(",")[0]) for pair in smpls]
    vals = [float(pair.split(",")[1]) for pair in smpls]

    if values["Plot"]:
        #plotting the sample
        plt.plot(wavelengths, vals, '-', color='r', linewidth=1)
        plt.xlabel('Wavelength [nm]')
        plt.ylabel('Power [dB]')
        plt.title("\""+ values["sample_name"] + "\" Sample")
        plt.ylim(-100,0)
        plt.show()

    if (values["Save"] and isConnected):
        # #saving the values to csv
        with open(values["sample_name"]+".csv", "wb") as f:
            f.write(data)
        return "Finish the sample process"
    else:
        return "Can't Save the file - device is not connsected"

# End of "Operator.py"


if __name__ == '__main__':
    print("this is operator.py")