# This file contains the Graphical user interface and delivers the requests from the user to devices
from OSA import OSA
from LASER import Laser
from Operator import getSweepResults, runSample, setConfig, makedirectory
from Interactive_Graph import regularSweepGraph, interactiveGraph
from Analyzer import getAnalyzerTransmition
from json import load, dump
import PySimpleGUI as sg
import subprocess
import os
import threading
import signal
import shutil

#---------------------------------------------------------------------------------------------------------------------------

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
global getTestsText
global getTestErrorText
live_flag = True    # For real time monitoring
isConnected = False # Until first connection
debugMode = False
status = "The devices are not connected"
getConnectionsText = "If you don't succed to connect you can work in 'Debug Mode'"
getSamplesText = "Connect to devices first or work in 'Debug Mode'"
getTestsText = "Connect to devices first or work in 'Debug Mode'"
getTestErrorText = ""
graphs_pids = []
# sg.theme_previewer()

#---------------------------------------------------------------------------------------------------------------------------

# Initial reads
# The Currently working directory - where this .py file can be found.
cwd = os.getcwd()
#cwd = cwd+"\\BGU_Project"
# Possible values for the laser Reputation.
rep_values_MHz = {'78.56MHz': 1, '39.28MHz': 2, '29.19MHz': 3, '19.64MHz': 4, '15.71MHz': 5, 
                '13.09MHz': 6, '11.22MHz': 7, '9.821MHz': 8, '8.729MHz': 9, '7.856MHz': 10, '6.547MHz': 12, 
                '5.612MHz': 14, '4.910MHz': 16, '4.365MHz': 18, '3.928MHz': 20, '3.571MHz': 22, '3.143MHz': 25, 
                '2.910MHz': 27, '2.709MHz': 29, '2.455MHz': 32, '2.311MHz': 34, '2.123MHz': 37, '1.964MHz': 40}
# The size of the GUI window (Width, Length).
SIZE = (600,600)
#sg.theme('DarkBlue')

#---------------------------------------------------------------------------------------------------------------------------

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
                    [sg.Push(), sg.Text(getConnectionsText), sg.Push()]]
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

#---------------------------------------------------------------------------------------------------------------------------

#--- Here we start with Layouts:

def collapse(layout, key, visible):
    # Hide or show the relevants fields.
    return sg.pin(sg.Column(layout, key=key, visible=visible))

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
                    [sg.Push(), sg.Text(getSamplesText), sg.Push()]]
    else:
        sampleL = [[sg.Push(), sg.Text("Connect to devices first or work in 'Debug Mode'"), sg.Push()]]
    return sampleL

def getDatabases():
    try:
        foldersNames = os.listdir("..\\Databases")
    except:
        os.mkdir("..\\Databases")
        foldersNames = os.listdir("..\\Databases")
    foldersNames.sort()   
    return foldersNames

def getTests():
    powerSweepSection = [[sg.Text("Stop Power Level"), sg.Input("50",s=3,key="maxPL"),sg.Text("Step:"), sg.Input("10",s=3,key="stepPL")]]
    analyzerSection = [[sg.Text("Interaction length: "), sg.Input("10",s=5,key="interactionLength"), sg.Text("mm")], [sg.Text("Total time for test"),sg.Input("60",s=3,key="totalSampleTime"),sg.Text("[seconds]"),sg.Push(),sg.Text("Interval time: "),sg.Input("1",s=3,key="intervalTime"), sg.Text("seconds")]]
    manuallResSection = [[sg.Text("Please enter a value: "), sg.Input("2",s=5,key="test_manuallRes"), sg.Text("nm")]]
    databasefolder = getDatabases()
    databaseLayout = [[sg.Text("Select Substance info from database:", font='David 12 bold')],
                [sg.Listbox(databasefolder, select_mode='LISTBOX_SELECT_MODE_SINGLE', key="test_database", size=(SIZE[1],2))]]
    if (isConnected or debugMode):
        test_values = [[sg.Push(), sg.Text("Tests - choose the tests you want", font='David 15 bold'), sg.Push()],
                    [sg.Text("Center Frequency:"), sg.Input("1500",s=5,key="test_CF"), sg.Text("[nm]"),
                    sg.Text("Span:"), sg.Input("50",s=5,key="test_SPAN"), sg.Text("[nm]")],
                    [sg.Text("Num of Ponits:"), sg.Input("Auto (500)",s=12,key="test_PTS"), sg.Text("Speed:"), sg.Combo(["Normal", "Fast"], default_value='Normal',key="test_SPD"), sg.Text("Sensetivity: "), sg.Combo(["NORM/HOLD", "NORM/AUTO", "NORMAL", "MID", "HIGH1", "HIGH2", "HIGH3"], default_value='MID',key="test_sens")], [sg.Text("Resolution: "), sg.Combo(["0.02nm <0.019nm>", "0.05nm <0.043nm>", "0.1nm <0.076nm>", "0.2nm <0.160nm>", "0.5nm <0.408nm>", "1nm <0.820nm>", "2nm <1.643nm>", "Manuall (Enter a value)"], enable_events=True, default_value="1nm <0.820nm>" ,key="test_res"), collapse(manuallResSection, 'section_manuallRes', False)],
                    [sg.Text("Start Power Level [%]:"), sg.Input("6",s=3,key="minPL"), sg.Checkbox(text="Sweep?", enable_events=True, key="testPowerLevelSweep"), collapse(powerSweepSection, 'section_powerSweep', False)],
                    [sg.Text("Number of samples per parameter: "), sg.Input("1",s=2,key="numSamplesParameter"), sg.Text("(max: 100)")],
                    [sg.Text("Choose the repetition rates [MHz]:"),sg.Checkbox(text="Select all", enable_events=True, key="selectAllRep")],
                    [sg.Checkbox(text="78.56",font='David 11',key="r1",default=False),sg.Checkbox(text="39.28",font='David 11',key="r2",default=False),sg.Checkbox(text="29.19",font='David 11',key="r3",default=False),sg.Checkbox(text="19.64",font='David 11',key="r4",default=False),sg.Checkbox(text="15.71",font='David 11',key="r5",default=False),sg.Checkbox(text="13.09",font='David 11',key="r6",default=False),sg.Checkbox(text="11.22",font='David 11',key="r7",default=False),sg.Checkbox(text="9.82",font='David 11',key="r8",default=False)],
                    [sg.Checkbox(text="8.729",font='David 11',key="r9",default=False),sg.Checkbox(text="7.856",font='David 11',key="r10",default=False),sg.Checkbox(text="6.547",font='David 11',key="r12",default=False),sg.Checkbox(text="5.612",font='David 11',key="r14",default=False),sg.Checkbox(text="4.910",font='David 11',key="r16",default=False),sg.Checkbox(text="4.365",font='David 11',key="r18",default=False),sg.Checkbox(text="3.928",font='David 11',key="r20",default=False),sg.Checkbox(text="3.571",font='David 11',key="r22",default=False)],
                    [sg.Checkbox(text="3.143",font='David 11',key="r25",default=False),sg.Checkbox(text="2.910",font='David 11',key="r27",default=False),sg.Checkbox(text="2.709",font='David 11',key="r29",default=False),sg.Checkbox(text="2.455",font='David 11',key="r32",default=False),sg.Checkbox(text="2.311",font='David 11',key="r34",default=False),sg.Checkbox(text="2.123",font='David 11',key="r37",default=False),sg.Checkbox(text="1.964",font='David 11',key="r40",default=False)],
                    [],[],
                    [sg.Text("Output name:"), sg.Input("Test_sample1", s=15, key="test_name"), sg.Push(), sg.Text("Comments:"),sg.Input("",s=30,key="TEST1_COMMENT")], [],
                    [sg.Checkbox(text="Analyzer (Beer-Lambert & Allan Variance) ?",enable_events=True,key="test_analyzer")], [collapse(analyzerSection, 'section_analyzer', False)],
                    [collapse(databaseLayout, 'section_database', False)],
                    [sg.Push(), sg.Button("Start Test"), sg.Push()],
                    [sg.Push(),sg.Text(str(getTestErrorText), key="test_errorText"),sg.Push()]]
    else:
        test_values = [[sg.Push(), sg.Text("Connect to devices first or run in 'Debug Mode'"), sg.Push()]]
    return test_values

def getResultsTabLayout():
    try:
        foldersNames = os.listdir("..\\Results")
    except:
        os.mkdir("..\\Results")
        foldersNames = os.listdir("..\\Results")
    foldersNames.sort()
    Layout = [[sg.Text("Select sample to plot", font='David 15 bold')],
                [sg.Listbox(foldersNames, select_mode='LISTBOX_SELECT_MODE_SINGLE', key="-SAMPLE_TO_PLOT-", size=(SIZE[1],20))],
                [sg.Push(), sg.Button("Load", key="-LOAD_SAMPLE-"), sg.Button("Delete", key="-DELETE_SAMPLE-"), sg.Push()]]
    return Layout

def updateResults(window):
    foldersNames = os.listdir("..\\Results")
    foldersNames.sort()
    window['-SAMPLE_TO_PLOT-'].update(foldersNames)

# End of Layouts.-----------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------------------

def updateJsonFileBeforeEnd(values):
    # This funciton save default connection parameters.
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    connectionsDict["OSA"]["IP"] = values[0]
    connectionsDict["OSA"]["PORT"] = values[1]
    connectionsDict["LASER"]["COM"] = values[2]
    connectionsDict["LASER"]["Serial"] = values[3]
    connectionsDict["Samples"]["Serial"] = values[3]
    with open(cwd+"\\connections.json", 'w') as f:
        dump(connectionsDict, f)

def checkStartConditions(values):
    getTestErrorText = ""
    if (int(values["test_CF"]) < 700):
        getTestErrorText = "Error: The 'Center Frequency' can only be between 700nm to 1600nm."
    elif (int(values["test_SPAN"]) > 250):
        getTestErrorText = "Error: The 'Span' value can only be between XXX to YYY."
    elif ( (values["test_PTS"] != "Auto (500)") and int(values["test_PTS"]) > 2000):
        getTestErrorText = "Error: The max Number of Points per sample is XXX points."
    elif ( (values["test_res"] == "Manuall (Enter a value)") and ((float(values["test_manuallRes"]) < 0) or (float(values["test_manuallRes"]) > 4) )):################################################
        getTestErrorText = "Error: The resolution you enter is not good value."
    elif (int(values["minPL"]) < 6 or int(values["minPL"]) > 100):
        getTestErrorText = "Error: The start power of the laser must be btween 6 to 100"
    elif ( values["testPowerLevelSweep"] and (int(values["maxPL"]) < 6 or int(values["maxPL"]) > 100) ):
        getTestErrorText = "Error: The end power of the laser must be btween 6 to 100"
    elif ( values["testPowerLevelSweep"] and (int(values["minPL"]) > int(values["maxPL"])) ):
        getTestErrorText = "Error: The start power must be smaller than the end power"
    elif (int(values["numSamplesParameter"]) > 100 or int(values["numSamplesParameter"]) <= 0):
        getTestErrorText = "Error: The number of samples must be between 1 to 3."
    elif (not values["r1"] and not values["r2"] and not values["r3"] and not values["r4"] and not values["r5"] and not values["r6"] and not values["r7"] and not values["r8"] and not values["r9"] and not values["r10"] and not values["r12"] and not values["r14"] and not values["r16"] and not values["r18"] and not values["r20"] and not values["r22"] and not values["r25"] and not values["r27"] and not values["r29"] and not values["r32"] and not values["r34"] and not values["r37"] and not values["r40"]):
        getTestErrorText = "Error: No repetition value was chosen"
    elif (values["test_name"] == ""): # Not a must.
        getTestErrorText = "Error: No name for 'Output name'."
    elif (values["test_analyzer"] and ( (int(values["interactionLength"]) < 0) or (int(values["interactionLength"]) > 1000) )):
        getTestErrorText = "Error: (Analyzer) The 'Interaction Length' must be bigger than zero and smaller than 1000 [mm]."
    elif (values["test_analyzer"] and ( (int(values["totalSampleTime"]) < 0) or (int(values["totalSampleTime"]) > 3600) )):
        getTestErrorText = "Error: (Analyzer) The 'Total time sample' must be bigger than zero. Max: 1 Hour."
    elif (values["test_analyzer"] and ( (int(values["intervalTime"]) < 0.5) or (int(values["intervalTime"]) > int(values["totalSampleTime"])) )):
        getTestErrorText = "Error: (Analyzer) The interval time must be bigger than 0.5 seconds and smaller from the Total time."
    return getTestErrorText

#---------------------------------------------------------------------------------------------------------------------------

def reopenMainL(window = None):
    # This function start the GUI window.
    mainL = [[sg.TabGroup([[sg.Tab('Connections',getConnections()), sg.Tab('Single Sample', getSampleL()), sg.Tab('Tests', getTests()), sg.Tab('Results', getResultsTabLayout())]], size = (SIZE[0]+30,SIZE[1]-70))],[sg.Button("Close"), sg.Button("Debug Mode"), sg.Push(), sg.Text(status)]]
    # mainL = [[sg.TabGroup([[sg.Tab('Connections',getConnections()), sg.Tab('Single Sample', getSampleL()), sg.Tab('Tests', getTests()), sg.Tab('Results', getResultsTabLayout())]], size = (SIZE[0],SIZE[1]-70))],[sg.Button("Close"), sg.Button("Debug Mode"), sg.Button("Debug Graph"), sg.Push(), sg.Text(status)]]
    try:
        window.close()
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE)
    except:
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE)
    return window

def popup(message):
    sg.theme('DarkGrey')
    layout = [[sg.Text(message)]]
    window = sg.Window('Message', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    return window

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
                getConnectionsText = getSamplesText = getTestsText = getTestErrorText = "The devices are connected"
                window.close()
                window = reopenMainL()
        except:
            print("Failed to connect to OSA or Laser, try again or continue wiht DEBUG mode.")
        updateConnections(values)
        
    elif event == 'Debug Mode':
        debugMode = True
        status = "Debug Mode"
        getConnectionsText = getSamplesText = getTestsText = getTestErrorText = "Now you are working in 'Debug Mode'!"
        laser = None
        osa = None
        window = reopenMainL(window)

    elif event == 'Sample':
        if ( isConnected or (not debugMode) ):
            setConfig(laser,osa,values["CF"],values["SPAN"],values["PTS"],values["POWER"],values["REP"])
            getSamplesText = runSample(laser,osa, isConnected,debugMode, values)
    
    elif event == "testPowerLevelSweep":
        if (values["testPowerLevelSweep"] == True):
            window['section_powerSweep'].update(visible=True)
        else:
            window['section_powerSweep'].update(visible=False)

    elif event == "selectAllRep":
        RepList = ["r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r12","r14","r16","r18","r20","r22","r25","r27","r29","r32","r34","r37","r40"]
        for i in RepList:
            values[i] = values['selectAllRep']
            window[i].update(values["selectAllRep"])
        print(values)

    elif event == "test_res":
        if values["test_res"] == "Manuall (Enter a value)":
            window['section_manuallRes'].update(visible=True)
        else:
            window['section_manuallRes'].update(visible=False)

    elif event == "test_analyzer":
        if (values["test_analyzer"] == True):
            window['section_analyzer'].update(visible=True)
            window['section_database'].update(visible=True)
        else:
            window['section_analyzer'].update(visible=False)
            window['section_database'].update(visible=False)

    elif event == "Start Test":
        if (isConnected or debugMode):
            getTestErrorText = checkStartConditions(values)
            if (getTestErrorText == ""):
                # EveryThing is OK
                if values["test_res"] == "Manuall (Enter a value)":
                    res = values["test_manuallRes"]
                else:
                    res = values["test_res"]
                window['Start Test'].update(disabled=True)
                window_message = sg.Window("",[[sg.Text("Executing Clean Test...")]])
                
                dirName = makedirectory(values["test_name"],values["test_CF"],values["test_SPAN"],values["test_PTS"],values["test_SPD"],values["test_sens"],res,values["test_analyzer"])
                getSweepResults(laser,osa,values,debugMode,dirName+"\\clean.csv")
                window_message.close()
                # For user
                tempEvent = sg.popup_ok_cancel("Empty measurment finished.\nPlease insert substance, then press 'OK'.")
                # OK was chosen
                if (tempEvent.upper()=="OK"):
                    window_message = sg.Window("",[[sg.Text("Executing Substance Test...")]])
                    if (values['test_analyzer']):
                        getSweepResults(laser,osa,values,debugMode,dirName+"\\analyzer.csv") 
                    else:
                        getSweepResults(laser,osa,values,debugMode,dirName+"\\substance.csv")
                    window_message.close()
                    # Adding to Results tab.
                    updateResults(window)
                    # Open a new process of the graph/grphs.
                    command = 'py'
                    args = ['Interactive_Graph.py', '--csv_name', dirName+"\\"]
                    process = subprocess.Popen([command] + args)
                    pid = process.pid
                    graphs_pids.append(pid)
                else:
                    shutil.rmtree(dirName)
                window['Start Test'].update(disabled=False)
            window['test_errorText'].update()

    elif event == "-LOAD_SAMPLE-":
        try:
            dirName = "..\\Results\\"+values['-SAMPLE_TO_PLOT-'][0]+"\\"
            command = 'py'
            args = ['Interactive_Graph.py', '--csv_name', dirName]
            process = subprocess.Popen([command] + args)
            pid = process.pid
            graphs_pids.append(pid)
        except:
            continue

    elif event == '-DELETE_SAMPLE-':
        tempEvent = sg.popup_ok_cancel("Are you sure you  want to delete this sample?")
        if ( tempEvent.upper() == "OK" ):
            try:
                dirName = "..\\Results\\"+values['-SAMPLE_TO_PLOT-'][0]+"\\"
                shutil.rmtree(dirName)
            except:
                continue
            updateResults(window)
            #window['-SAMPLE_TO_PLOT-'].Update()

    elif ( (event == 'Close') or (event == sg.WIN_CLOSED) ):
        window.close()
        for pid in graphs_pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Process with PID {pid} killed successfully.")
            except OSError as e:
                print(f"Error killing process with PID {pid}: {e}")
        break

    # elif event == 'Debug Graph':
    #     csvFile = "..\\Results\\2023_03_23_15_29_25_116512_Eyal & Alex\\"
    #     command = 'py'
    #     args = ['Interactive_Graph.py', '--csv_name', csvFile]
    #     process = subprocess.Popen([command] + args)
    #     pid = process.pid
    #     graphs_pids.append(pid)

# End of File.

#---------------------------------------------------------------------------------------------------------------------------

                # popup_win = popup('Starting Clean Test...')
                # window.force_focus()
                #popup_win.close()
                #popup_win = popup('Starting Substance Test...')
                #window.force_focus()
                #popup_win.close()
                #popup_win = popup('Starting Allan Variance Test...')
                #window.force_focus()
                        