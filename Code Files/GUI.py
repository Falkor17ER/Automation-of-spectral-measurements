# This file contains the Graphical user interface and delivers the requests from the user to devices

import PySimpleGUI as sg
from OSA import OSA
from LASER import Laser
# from Operator import *
from Operator import testManagment, runSample
import threading
import matplotlib.pyplot as plt
import os
from json import load, dump
from time import sleep
from time  import clock, time

# Globals
global layouts
global cwd
global connectionsDict
global osa
global laser
global isConnected
global debugMode
global live_plt
global laserPowerMeasurment
global laserFrequanceyMeasurment
global status
global getConnectionsText
global getSamplesText
global getTests1Text
global getRTLText
live_flag = True    # For real time monitoring
isConnected = False # Until first connection
debugMode = False
status = "The devices are not connected"
getConnectionsText = "If you don't succed to connect you can work in 'Debug Mode'"
getSamplesText = "Connect to devices first or work in 'Debug Mode'"
getTests1Text = "Connect to devices first or work in 'Debug Mode'"
getTestErrorText = ""
getRTLText = "Connect to devices first!"
flag_testPowerLevelSweep = False
flag_testAllanVariance = False
flag_testBeerLambertLaw = False
flag_endText = False

# sg.theme_previewer()

# Initial reads
# The Currently working directory - where this .py file can be found.
cwd = os.getcwd()
#cwd = cwd+"\\BGU_Project"
# Possible values for the laser Reputation.
rep_values_MHz = {'78.56MHz': 1, '39.28MHz': 2, '29.19MHz': 3, '19.64MHz': 4, '15.71MHz': 5, 
                '13.09MHz': 6, '11.22MHz': 7, '9.821MHz': 8, '8.729MHz': 9, '7.856MHz': 10, '6.547MHz': 12, 
                '5.612MHz': 14, '4.910MHz': 16, '4.365MHz': 18, '3.928MHz': 20, '3.571MHz': 22, '3.143MHz': 25, 
                '2.910MHz': 27, '2.709MHz': 29, '2.455MHz': 32, '2.311MHz': 34, '2.123MHz': 37, '1.964MHz': 40}
# The size of the GUI window.
SIZE = (600,600)
#sg.theme('DarkBlue')

# Functions:

# This function is the first Tab of the GUI window - Responsible for the connections with the Laser & OSA devices.
def getConnections():
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    connections = [[sg.Push(), sg.Text("OSA", font='David 15 bold'), sg.Push()],
                    [sg.Text("IP Address:"), sg.Push(), sg.Input(connectionsDict["OSA"]["IP"],s=15)],
                    [sg.Text("Port:"), sg.Push(), sg.Input(connectionsDict["OSA"]["PORT"],s=15)],
                    [sg.Push(), sg.Text("Laser", font='David 15 bold'), sg.Push()],
                    [sg.Text("COM:"), sg.Push(), sg.Input(connectionsDict["LASER"]["COM"],s=15)],
                    [sg.Text("Serial:"), sg.Push(), sg.Input(connectionsDict["LASER"]["Serial"],s=15)],
                    [sg.Push(), sg.Button("Connect"), sg.Push()],
                    [sg.Text(getConnectionsText)]]
    return connections

def updateConnections(values):
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    connectionsDict["OSA"]["IP"] = values[0]
    connectionsDict["OSA"]["PORT"] = values[1]
    connectionsDict["LASER"]["COM"] = values[2]
    connectionsDict["LASER"]["Serial"] = values[3]
    with open(cwd+"\\connections.json", 'w') as f:
        dump(connectionsDict, f)

#--- Here we finished with Connections.

def getSampleL():
    if (isConnected or debugMode):
        sampleL = [[sg.Push(), sg.Text("OSA", font='David 15 bold'), sg.Push()],
                    [sg.Text("Center Frequency:"), sg.Push(), sg.Input("1500",s=15,key="CF"), sg.Text("[nm]")],
                    [sg.Text("Span:"), sg.Push(), sg.Input("50",s=15,key="SPAN"), sg.Text("[nm]")],
                    [sg.Text("Ponits:"), sg.Push(), sg.Input("Auto (500)",s=15,key="PTS")],
                    [sg.Text("Speed:"), sg.Push(), sg.Combo(["Normal", "Fast"], default_value='Normal',key="SPD")],
                    [sg.Push(), sg.Text("Laser", font='David 15 bold'), sg.Push()],
                    [sg.Text("Power:"), sg.Push(), sg.Input("6",s=15,key="POWER"), sg.Text("%")],
                    [sg.Text("Repetition Rate:"), sg.Push(), sg.Combo(list(rep_values_MHz.keys()), key="REP", default_value=list(rep_values_MHz.keys())[0])],
                    [sg.Push(), sg.Text("Misc", font='David 15 bold'), sg.Push()],
                    [sg.Checkbox("Save sample", key="Save"), sg.Push(), sg.Text("Output name:"), sg.Input("demo_sample", s=15, key="sample_name")],
                    [sg.Checkbox("Plot sample", key="Plot")],
                    [sg.Push(), sg.Button("Sample"), sg.Push()],
                    [sg.Text(getSamplesText)]]
    else:
        sampleL = [[sg.Text("Connect to devices first or work in 'Debug Mode'")]]
    return sampleL

def collapse(layout, key, visible):
    return sg.pin(sg.Column(layout, key=key, visible=visible))

def getTests():
    powerSweepSection = [[sg.Text("Stop Power Level"), sg.Input("50",s=3,key="maxPL"),sg.Text("Step:"), sg.Input("10",s=3,key="stepPL")]]
    allanVarianceSection = [[sg.Text("Parametr1"),sg.Input("0",s=3,key="allanV1"),sg.Text("Parameter2"),sg.Input("0",s=3,key="allanV2"),sg.Text("Parameter3"),sg.Input("0",s=3,key="allanV3")]]
    beerLambertLawSection = [[sg.Text("Interaction length [cm]"), sg.Input("10",s=5,key="interactionLength"),sg.Text("Line Strength (According to Manufactor):"), sg.Input("50",s=5,key="lineStrength")]]
    endTextSection = [[sg.Push(),sg.Text(str(getTestErrorText)),sg.Push()]]
    if (isConnected or debugMode):
        test_values = [[sg.Push(), sg.Text("Tests - choose the tests you want", font='David 15 bold'), sg.Push()],
                    [sg.Text("Center Frequency:"), sg.Input("1500",s=5,key="test_CF"), sg.Text("[nm]"),
                    sg.Text("Span:"), sg.Input("50",s=5,key="test_SPAN"), sg.Text("[nm]")],
                    [sg.Text("Num of Ponits:"), sg.Input("Auto (500)",s=12,key="test_PTS"), sg.Text("Speed:"), sg.Combo(["Normal", "Fast"], default_value='Normal',key="test_SPD")],
                    [sg.Text("Start Power Level [%]:"), sg.Input("6",s=3,key="minPL"), sg.Checkbox(text="Sweep?", enable_events=True, key="testPowerLevelSweep"), collapse(powerSweepSection, 'section_powerSweep', False)],
                    [sg.Text("Number of samples per parameter: "), sg.Input("1",s=2,key="numSamplesParameter"), sg.Text("(max: 3)")],
                    [sg.Text("Choose the repetition rates [MHz]:"),sg.Checkbox(text="Select all", enable_events=True, key="selectAllRep")],
                    [sg.Checkbox(text="78.56",font='David 11',key="r1",default=False),sg.Checkbox(text="39.28",font='David 11',key="r2",default=False),sg.Checkbox(text="29.19",font='David 11',key="r3",default=False),sg.Checkbox(text="19.64",font='David 11',key="r4",default=False),sg.Checkbox(text="15.71",font='David 11',key="r5",default=False),sg.Checkbox(text="13.09",font='David 11',key="r6",default=False),sg.Checkbox(text="11.22",font='David 11',key="r7",default=False),sg.Checkbox(text="9.82",font='David 11',key="r8",default=False)],
                    [sg.Checkbox(text="8.729",font='David 11',key="r9",default=False),sg.Checkbox(text="7.856",font='David 11',key="r10",default=False),sg.Checkbox(text="6.547",font='David 11',key="r12",default=False),sg.Checkbox(text="5.612",font='David 11',key="r14",default=False),sg.Checkbox(text="4.910",font='David 11',key="r16",default=False),sg.Checkbox(text="4.365",font='David 11',key="r18",default=False),sg.Checkbox(text="3.928",font='David 11',key="r20",default=False),sg.Checkbox(text="3.571",font='David 11',key="r22",default=False)],
                    [sg.Checkbox(text="3.143",font='David 11',key="r25",default=False),sg.Checkbox(text="2.910",font='David 11',key="r27",default=False),sg.Checkbox(text="2.709",font='David 11',key="r29",default=False),sg.Checkbox(text="2.455",font='David 11',key="r32",default=False),sg.Checkbox(text="2.311",font='David 11',key="r34",default=False),sg.Checkbox(text="2.123",font='David 11',key="r37",default=False),sg.Checkbox(text="1.964",font='David 11',key="r40",default=False)],
                    [],[],
                    [sg.Text("Output name:"), sg.Input("Test_sample1", s=15, key="test_name"), sg.Push()],[],
                    [sg.Checkbox(text="Allan Variance test?",enable_events=True,key="testAllanVariance")], [collapse(allanVarianceSection, 'section_allanVariance', False)],
                    [sg.Checkbox(text="Beer-Lambert Law test?",enable_events=True,key="testBeerLambertLaw")], [collapse(beerLambertLawSection, 'section_beerLambertLaw', False)],
                    [sg.Text("Comments:"),sg.Input("",s=30,key="TEST1_COMMENT")],
                    [sg.Push(), sg.Button("Start Test"), sg.Push()],
                    [sg.Text(text="",enable_events=True,key="endText")],[collapse(endTextSection, 'section_endText', True)]]
    else:
        test_values = [[sg.Text("Connect to devices first or run in 'Debug Mode'")]]
    return test_values

def reopenMainL(window = None):
    mainL = [[sg.TabGroup([[sg.Tab('Connections',getConnections()), sg.Tab('Single Sample', getSampleL()), sg.Tab('Tests', getTests())]], size = (SIZE[0],SIZE[1]-70))],
        [[sg.Button("Close"), sg.Button("Debug Mode"), sg.Push(), sg.Text(status)]]]
    try:
        window.close()
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE)
    except:
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE)
    return window
    
def updateJsonFileBeforeEnd(values):
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    connectionsDict["OSA"]["IP"] = values[0]
    connectionsDict["OSA"]["PORT"] = values[1]
    connectionsDict["LASER"]["COM"] = values[2]
    connectionsDict["LASER"]["Serial"] = values[3]
    connectionsDict["Samples"]["Serial"] = values[3]
    with open(cwd+"\\connections.json", 'w') as f:
        dump(connectionsDict, f)

def startMessage():
    message = [[sg.Push(),sg.Text("Finish the darl measurment"),sg.Push()],[sg.Push(),sg.Text("Insert the substance to the box and press 'Continue'"),sg.Push()],[sg.Push(),sg.Button("Continue"),sg.Push()]]
    return message

def enterSubstanceToMeasure():
    thread = threading.Thread(target=startMessage)
    thread.start()
    message = startMessage()
    insertWindow = [[sg.TabGroup(message)]]
    try:
        window.close()
        window = sg.Window('Insert Substance', insertWindow, disable_close=True, size = SIZE)
    except:
        window = sg.Window('Insert Substance', insertWindow, disable_close=True, size = SIZE)
    return window
    
    
        
    waitRespondTime = clock()
    #while (time()-waitRespondTime <= 600):
    while (True):
        if (event == "Continue"):
            thread.close()
            return True
    return False

# The checking events - The managment of the GUI:

window = reopenMainL()
while True:
    event, values = window.read()
    if event == 'Connect':
        try:
            osa = OSA(values[0])
            laser = Laser(values[2])
            if not isConnected:
                isConnected = True
                debugMode = False
                status = "Devices are connected"
                getConnectionsText = getSamplesText = getTests1Text = getRTLText = "The devices are connected"
                window.close()
                window = reopenMainL()
        except:
            print("Failed to connect to OSA or Laser, try again or continue wiht DEBUG mode.")
        updateConnections(values)
        
    elif event == 'Debug Mode':
        debugMode = True
        status = "Debug Mode"
        getConnectionsText = getSamplesText = getTests1Text = "Now you are working in 'Debug Mode'!"
        laser = None
        osa = None
        window = reopenMainL(window)

    elif event == 'Sample':
        if ( isConnected or (not debugMode) ):
            setConfig(laser,osa,values["CF"],values["SPAN"],values["PTS"],values["POWER"],values["REP"])
            getSamplesText = runSample(laser,osa, isConnected,debugMode, values)
    
    elif event == "testPowerLevelSweep":
        flag_testPowerLevelSweep = not flag_testPowerLevelSweep
        window['section_powerSweep'].update(visible=flag_testPowerLevelSweep)

    elif event == "selectAllRep":
        RepList = ["r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r12","r14","r16","r18","r20","r22","r25","r27","r29","r32","r34","r37","r40"]
        for i in RepList:
            values[i] = not values[i]
        window.update(default=values["selectAllRep"])##### lesader
        print(values)

    elif event == "testAllanVariance":
        flag_testAllanVariance = not flag_testAllanVariance
        window['section_allanVariance'].update(visible=flag_testAllanVariance)

    elif event == "testBeerLambertLaw":
        flag_testBeerLambertLaw = not flag_testBeerLambertLaw
        window['section_beerLambertLaw'].update(visible=flag_testBeerLambertLaw)

    elif event == "Start Test":
        getTestErrorText = ""
        flag_endText = False
        if (isConnected or debugMode):
            if (int(values["test_CF"]) < 700):
                getTestErrorText = "Error: The 'Center Frequency' can only be between 700nm to 1600nm."
            elif (int(values["test_SPAN"]) > 250):
                getTestErrorText = "Error: The 'Span' value can only be between XXX to YYY."
            elif ( (values["test_PTS"] != "Auto (500)") and int(values["test_PTS"]) > 2000):
                getTestErrorText = "Error: The max Number of Points per sample is XXX points."
            elif (int(values["minPL"]) < 6 or int(values["minPL"]) > 100):
                getTestErrorText = "Error: The start power of the laser must be btween 6 to 100"
            elif ( values["testPowerLevelSweep"] and (int(values["maxPL"]) < 6 or int(values["maxPL"]) > 100) ):
                getTestErrorText = "Error: The end power of the laser must be btween 6 to 100"
            elif ( values["testPowerLevelSweep"] and (int(values["minPL"]) > int(values["maxPL"])) ):
                getTestErrorText = "Error: The start power must be smaller than the end power"
            elif (int(values["numSamplesParameter"]) > 3 or int(values["numSamplesParameter"]) <= 0):
                getTestErrorText = "Error: The number of samples must be between 1 to 3."
            elif (not values["r1"] and not values["r2"] and not values["r3"] and not values["r4"] and not values["r5"] and not values["r6"] and not values["r7"] and not values["r8"] and not values["r9"] and not values["r10"] and not values["r12"] and not values["r14"] and not values["r16"] and not values["r18"] and not values["r20"] and not values["r22"] and not values["r25"] and not values["r27"] and not values["r29"] and not values["r32"] and not values["r34"] and not values["r37"] and not values["r40"]):
                getTestErrorText = "Error: No repetition value was chosen"
            elif (values["test_name"] == ""):
                getTestErrorText = "Error: No name for 'Output name'."
            elif (values["testAllanVariance"] and (int(values["allanV1"]) < 0)):
                getTestErrorText = "Error: The first Allan parameter must be bigger than zero."
            elif (values["testAllanVariance"] and (int(values["allanV2"]) < 0)):
                getTestErrorText = "Error: The second Allan parameter must be bigger than zero."
            elif (values["testAllanVariance"] and (int(values["allanV3"]) < 0)):
                getTestErrorText = "Error: The third Allan parameter must be bigger than zero."    
            elif (values["testBeerLambertLaw"] and (int(values["interactionLength"]) < 0)):
                getTestErrorText = "Error: (Beer-Lamber Law) The 'Interaction Length' must be bigger than zero."    
            elif (values["testBeerLambertLaw"] and (int(values["lineStrength"]) < 0)):
                getTestErrorText = "Error: (Beer-Lamber Law) The 'Line Strength' must be bigger than zero."
            if (getTestErrorText == ""):
                testManagment(laser,osa,values,debugMode)
                enterSubstanceToMeasure()
            else:
                flag_endText = True
                window['section_endText'].update(visible=True)

    elif event == "Start laser":
        if isConnected:
            laser.emission(1)
    elif event == "Stop laser":
        if isConnected or debugMode:
            laser.emission(0)
    
    elif event == 'Close':
        #updateJsonFileBeforeEnd()
        break

window.close()

# -------------------------------------------------------------------------------------

# def getRTL():
#     if (isConnected):
#         RTL = [[sg.Button("Open monitor"), sg.Button("Close monitor"), sg.Push()],
#             [sg.Button("Start laser"), sg.Button("Stop laser"), sg.Push()],
#             [sg.Text(getRTLText), sg.Push()]]
#     else:
#         RTL = [[sg.Text(getRTLText)]]
#     return RTL

# def startMonitor():
#     sample_name = "Live OSA"
#     def updateGraph(osa, sample_name):
#         # getting to data the swept values
#         data = osa.getCSVFile(sample_name)
#         data_decoded = data.decode("utf-8")
#         data_decoded = data_decoded.split("\r\n")
#         smpls = data_decoded[39:-2]
#         wavelengths = [float(pair.split(",")[0]) for pair in smpls]
#         vals = [float(pair.split(",")[1]) for pair in smpls]
#         # performing a sweep (like a sample)

#         plt.plot(wavelengths, vals, '-', color='r', linewidth=2)
#         plt.xlabel('Wavelength [nm]')
#         plt.ylabel('Power [dB]')
#         plt.title("Calibration")
#         plt.ylim(-100, 0)
#         plt.pause(1)
#         plt.clf()
#         plt.draw()
    
#     osa.setSpeed("x2")
#     osa.setPoints("300")

#     while live_flag:
#         osa.sweepLive()
#         updateGraph(osa, sample_name)
#     plt.close()

# ---------------------------------------------------------------------

    # elif event == 'Open monitor':
    #     if isConnected or debugMode:
    #         # setting flag to allow plot
    #         live_flag = True
    #         # Create the thread
    #         thread = threading.Thread(target=startMonitor)
    #         # Start the thread
    #         thread.start()

    # elif event == "Close monitor":
    #     live_flag = False
    #     laser.emission(0)

# ---------------------------------------------------------------------

