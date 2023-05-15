import pandas as pd
import numpy as np
# import PySimpleGUI as sg
# from OSA import OSA
# from LASER import Laser
# import threading
import matplotlib.pyplot as plt
import os
# from json import load, dump
from time import sleep, time
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

# Possible values for the laser Reputation.
rep_values_MHz_inverted = {'78.56MHz': 1, '39.28MHz': 2, '29.19MHz': 3, '19.64MHz': 4, '15.71MHz': 5, 
                '13.09MHz': 6, '11.22MHz': 7, '9.821MHz': 8, '8.729MHz': 9, '7.856MHz': 10, '6.547MHz': 12, 
                '5.612MHz': 14, '4.910MHz': 16, '4.365MHz': 18, '3.928MHz': 20, '3.571MHz': 22, '3.143MHz': 25, 
                '2.910MHz': 27, '2.709MHz': 29, '2.455MHz': 32, '2.311MHz': 34, '2.123MHz': 37, '1.964MHz': 40}

# Sample Managment: ----------------------------------------------------------------------------------------------

def setConfig(laser,osa,cf,span,points,power,rep,sens,res):
    configureLaser(laser,power,rep)
    configureOSA(osa,cf,span,points,sens,res)

def configureLaser(laser, power,rep):
    if not debugMode:
        # Setting repetition rate
        laser.pulsePickerRation(rep)
        sleep(1)
        laser.powerLevel(int(power))

def configureOSA(osa, cf,span,points,sens,res):
    if not debugMode:
        convertDict = {
            "SPEED": {"Normal": "x1", "Fast": "x2"},
            "Sens": {"NORM/HOLD": 0, "NORM/AUTO": 1, "NORMAL": 6, "MID": 2, "HIGH1": 3, "HIGH2": 4, "HIGH3": 5}
        }
        # Set center frequency
        osa.setCenterFreq(cf)
        sleep(1)
        # Set Span
        osa.setSpan(span)
        sleep(1)
        # Set number of sampling points
        # if (points == "Auto"):
        #     points = "auto on"
        # osa.setPoints(points)
        sleep(1)
        # Set sampling sensetivity
        osa.setSens(convertDict["Sens"][sens])
        sleep(1)
        # Set sampling resolution
        osa.setRes(res.split(' ')[0][:-2])
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

def meanMeasure(laser, osa ,numOfSamples, numOfDots, debugMode):
    try:
        numOfSamples = int(numOfSamples)
    except:
        numOfSamples = 1
    if not debugMode:
        # measuretList = []
        # resultList = []
        # for i in range(0,numOfSamples):
        #     sleep(0.2)
        #     osa.sweep()
        #     data = osa.getCSVFile("noiseMeasurment")
        #     data_decoded = data.decode("utf-8")
        #     data_decoded = data_decoded.split("\r\n")
        #     smpls = data_decoded[39:-2]
        #     wavelengths = [float(pair.split(",")[0]) for pair in smpls]
        #     measurment = [float(pair.split(",")[1]) for pair in smpls]
        #     measuretList.append(measurment)
        # i = 0
        # j = 0
        # if numOfSamples > 1:
        #     while (i < numOfDots):
        #         sum = 0
        #         while (j < numOfSamples):
        #             sum += measuretList[j][i]
        #             j = j+1
        #         resultList.append(sum/numOfSamples)
        #         j = 0
        #         i = i+1
        #     return resultList
        # return measuretList[0]
        osa.setAveraging(str(numOfSamples))
        osa.sweep()
        data = osa.getCSVFile("noiseMeasurment")
        data_decoded = data.decode("utf-8")
        data_decoded = data_decoded.split("\r\n")
        smpls = data_decoded[39:-2]
        return [float(pair.split(",")[1]) for pair in smpls]
    return np.random.rand(numOfDots)*(-100)

def noiseMeasurments(laser, osa ,values, debugMode, csvName): # Dark Measurmennts
    # Here we are taking in mind that the laser and the OSA are already configed.
    print("Noise measurment, please wait...")
    sleep(0.5)
    if (not debugMode):
        laser.emission(0)
        if values["test_PTS"] == "Auto":
            osa.setPoints('auto on')
        else:
            osa.setPoints(values["test_PTS"])
        pts = osa.getPoints()
        configureOSA(osa,values['test_CF'],values['test_SPAN'],pts,values['test_sens'],values['test_res'])
    else:
        pts = 501
    darkMeasurment = meanMeasure(laser, osa ,values['darkNumSamplesParameter'], pts, debugMode)
    startF = int(values["test_CF"]) - int(values["test_SPAN"])/2
    stopF = startF + int(values["test_SPAN"])
    freqs_columns = [str(freq) for freq in np.arange(startF,stopF,int(values["test_SPAN"])/pts)]
    allResults_df =  pd.DataFrame(columns=['Date', 'Comment', 'CF',	'SPAN',	'REP_RATE',	'POWER', 'Sens','Res', 'Interval', 'SAMPLINGS_NUMBER']+freqs_columns)
    new_row = []
    new_row.append(getTime())
    new_row.append(values["TEST1_COMMENT"])
    new_row.append(values["test_CF"])
    new_row.append(values["test_SPAN"])
    new_row.append("NULL") # Repetition.
    new_row.append("NULL") # Power.
    new_row.append(values["test_sens"])
    new_row.append(values["test_res"])
    new_row.append("")
    new_row.append(values['darkNumSamplesParameter'])
    new_row = new_row + list(darkMeasurment)
    # Append the new row to the dataframe
    allResults_df.loc[len(allResults_df)] = new_row
    # End of measurments
    allResults_df.to_csv(csvName, index=False)
    sleep(0.2)

# def emptyMeasurments(laser,osa, numOfDots,emptyNum=3):
#     # Here we are taking in mind that the laser and the OSA are already configed.
#     laser.emission(1)
#     print("Empty measurment, please wait...")
#     sleep(0.5)
#     emptyMeasurment = meanMeasure(laser,osa ,emptyNum,numOfDots, debugMode)
#     return emptyMeasurment

# def laserMeasurment(laser,osa, numOfSamples,numOfDots,darkMeasurment=0,emptyMeasurment=0):
#     laser.emission(1)
#     sleep(0.5)
#     # print("Starting measurment, please wait...")
#     measurment = meanMeasure(laser,osa ,numOfSamples,numOfDots, debugMode)
#     if (darkMeasurment != 0):
#         measurment -= darkMeasurment
#     if (emptyMeasurment != 0):
#         measurment -= emptyMeasurment
#     return measurment

def getTime():
    time = str(datetime.today())
    time = time.replace('-', '_')
    time = time.replace(' ', '_')
    time = time.replace(':', '_')
    time = time.replace('.', '_')
    return time

def makedirectory(dirname, cf,span,npoints,sens,res,analyzer):
    dir = "/Results/"+getTime()+"_"+dirname+"_CF="+cf+"_Span="+span+"_analyzer="+str(analyzer)
    dir = dir.replace("<", "(")
    dir = dir.replace(">", ")")
    dir = dir.replace(".", "_")
    dir = '..'+dir
    os.mkdir(dir)
    return dir

def makeSubstaceCSV(csvname, df_original):
    csvname = csvname[:-12]+'substance.csv'
    df_substance = pd.DataFrame(columns = df_original.columns.tolist())
    r = None
    p = None
    for idx in range(len(df_original)):
        if ( (r != df_original["REP_RATE"].iloc[idx] ) or (p != df_original["POWER"].iloc[idx]) ):
            r = df_original["REP_RATE"].iloc[idx]
            p = df_original["POWER"].iloc[idx]
            df_substance.loc[len(df_substance)] = df_original.iloc[idx]
    df_substance.to_csv(csvname, index=False)

def getSweepResults(laser,osa,values,debug,csvname):
    global debugMode
    debugMode = debug
    # This function will manage all the test process and call to all the relevant functions.
    # enterSubstanceToMeasure()
    reps = getReps(values)
    if (not debugMode):
        if values["test_PTS"] == "Auto":
            osa.setPoints('auto on')
        else:
            osa.setPoints(values["test_PTS"])
        pts = osa.getPoints()
    else:
        pts = 501
    if values["test_res"] == "Manuall (Enter a value)":
        res = values["test_manuallRes"]
    else:
        res = values["test_res"]
    setConfig(laser,osa,values["test_CF"],values["test_SPAN"], pts, values["minPL"], reps[0], values['test_sens'], res)
    start = int(values["minPL"])
    if (values["testPowerLevelSweep"]):
        stop = int(values["maxPL"])
        step = int(values["stepPL"])
        powers = range(start,stop+1,step)
    else:
        powers = [start]
    # Making the CSV File
    startF = int(values["test_CF"]) - int(values["test_SPAN"])/2
    stopF = startF + int(values["test_SPAN"])
    freqs_columns = [str(freq) for freq in np.arange(startF,stopF,int(values["test_SPAN"])/pts)]
    allResults_df =  pd.DataFrame(columns=['Date', 'Comment', 'CF',	'SPAN',	'REP_RATE',	'POWER', 'Sens','Res', 'Interval', 'SAMPLINGS_NUMBER']+freqs_columns)
    # laserPower = True
    # capturePower = True
    if (not debugMode):
        laser.emission(1)
    for freq in reps:
        for p in powers:
            configureLaser(laser, p, freq)

            # Starting the test:
            if csvname[-12:-4] == "analyzer": # Analyze Graph: Beer-Lambert & Allan Variance Mode
                totalTime = int(values['totalSampleTime'])
                intervalTime = float(values['intervalTime'])
                startTime = time()
                if (not debugMode):
                    laser.emission(1)
                    sleep(0.4) # Waiting to laser Turn ON.
                #
                while(time() - startTime < totalTime):
                    lastTime = time()
                    result = meanMeasure(laser,osa, 1 ,pts, debugMode)
                    new_row = []
                    new_row.append(getTime())
                    new_row.append(values["TEST1_COMMENT"])
                    new_row.append(values["test_CF"])
                    new_row.append(values["test_SPAN"])
                    new_row.append(rep_values_MHz[freq])
                    new_row.append(p)
                    new_row.append(values["test_sens"])
                    new_row.append(values["test_res"])
                    new_row.append(lastTime-startTime)
                    new_row.append(values["substanceNumSamplesParameter"])
                    new_row = new_row + list(result)
                    # Append the new row to the dataframe
                    allResults_df.loc[len(allResults_df)] = new_row
                    timeleft = intervalTime-(time()-lastTime)
                    if timeleft > 0:
                        sleep(timeleft)
            #---------------------------------------------------------------------------------------------------------------
            else: # Regular Mode
                sleep(0.4) # Sleep - waiting to change the parameter changing parameters.
                if csvname[-9:-4] == "clean":
                    numOfSamples = values['cleanNumSamplesParameter']
                if csvname[-13:-4] == "substance":
                    numOfSamples = values['substanceNumSamplesParameter']
                result = meanMeasure(laser,osa,numOfSamples,pts, debugMode)
                new_row = []
                new_row.append(getTime())
                new_row.append(values["TEST1_COMMENT"])
                new_row.append(values["test_CF"])
                new_row.append(values["test_SPAN"])
                new_row.append(rep_values_MHz[freq])
                new_row.append(p)
                new_row.append(values["test_sens"])
                new_row.append(values["test_res"])
                new_row.append("")
                new_row.append(numOfSamples)
                new_row = new_row + list(result)
                # Append the new row to the dataframe
                allResults_df.loc[len(allResults_df)] = new_row
    # End of measurments

    # Save a substance csv
    if csvname[-12:-4] == "analyzer":
        makeSubstaceCSV(csvname, allResults_df)
    # Turn off the laser
    if (not debugMode):
        laser.emission(0) # Turn off the laser after the measurments sweep. 
    allResults_df.to_csv(csvname, index=False)

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
    csvname = 'C:\\BGUProject\\Automation-of-spectral-measurements\\Results\\Analyzer_Test\\analyzer.csv'
    allResults_df = pd.read_csv(csvname)
    makeSubstaceCSV(csvname, allResults_df)
#---------------------------------------------------------------------------------------------------------------------------
