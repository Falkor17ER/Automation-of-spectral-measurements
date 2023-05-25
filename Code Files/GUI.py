# This file contains the Graphical user interface and delivers the requests from the user to devices
# from time import time as time
from OSA import OSA
from LASER import Laser
from Operator import getSweepResults, runSample, setConfig, makedirectory, noiseMeasurments
from json import load, dump
from time import sleep
import PySimpleGUI as sg
import os
import signal
import shutil
import threading
import subprocess
import tkinter.messagebox as tkm
import time

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

class ReturnValueHolder:
    def __init__(self):
        self.return_value = None

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
SIZE = (600,630)
#sg.theme('DarkBlue')
sg.theme('Default')
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
                    [sg.Text("Ponits: (Auto recommended)"), sg.Push(), sg.Input("Auto",s=15,key="PTS")],
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

def getTests():
    powerSweepSection = [[sg.Text("Stop Power Level"), sg.Input("50",s=3,key="maxPL"),sg.Text("Step:"), sg.Input("10",s=3,key="stepPL")]]
    analyzerSection = [[sg.Text("Total time for test"),sg.Input("60",s=3,key="totalSampleTime"),sg.Text("[seconds]"),sg.Push(),sg.Text("Interval time: "),sg.Input("1",
    s=3,key="intervalTime"), sg.Text("seconds")]]
    stopTestSection = [[sg.Button("Stop Test")]]
    if (isConnected or debugMode):
        test_values = [[sg.Push(), sg.Text("Tests - choose the tests you want", font='David 15 bold'), sg.Push()],
                    [sg.Text("Center Frequency:"), sg.Input("1500",s=5,key="test_CF"), sg.Text("[nm]"),
                    sg.Text("Span:"), sg.Input("50",s=5,key="test_SPAN"), sg.Text("[nm]")],
                    [sg.Text("Number of Ponits: (Auto recommended)"), sg.Input("Auto",s=12,key="test_PTS"), sg.Text("Sensetivity: "), sg.Combo(["NORM/HOLD", "NORM/AUTO", "NORMAL", "MID", "HIGH1", "HIGH2", "HIGH3"], default_value='MID',key="test_sens")], [sg.Text("Resolution: "), sg.Combo(["0.02nm <0.019nm>", "0.05nm <0.043nm>", "0.1nm <0.076nm>", "0.2nm <0.160nm>", "0.5nm <0.408nm>", "1nm <0.820nm>", "2nm <1.643nm>"], enable_events=True, default_value="1nm <0.820nm>" ,key="test_res")],
                    [sg.Text("Start Power Level [%]:"), sg.Input("6",s=3,key="minPL"), sg.Checkbox(text="Sweep?", enable_events=True, key="testPowerLevelSweep"), collapse(powerSweepSection, 'section_powerSweep', False)],
                    [sg.Text("Sample Averaging (Dark Measurments): "), sg.Input("5",s=2,key="darkNumSamplesParameter"), sg.Text("(max: 100)")],
                    [sg.Text("Sample Averaging (Clean/Empty Measurments): "), sg.Input("5",s=2,key="cleanNumSamplesParameter"), sg.Text("(max: 100)")],
                    [sg.Text("Sample Averaging (Substance): "), sg.Input("1",s=2,key="substanceNumSamplesParameter"), sg.Text("(max: 100)")],
                    [sg.Text("Choose the repetition rates [MHz]:"),sg.Checkbox(text="Select all", enable_events=True, key="selectAllRep")],
                    [sg.Checkbox(text="78.56",font='David 11',key="r1",default=False),sg.Checkbox(text="39.28",font='David 11',key="r2",default=False),sg.Checkbox(text="29.19",font='David 11',key="r3",default=False),sg.Checkbox(text="19.64",font='David 11',key="r4",default=False),sg.Checkbox(text="15.71",font='David 11',key="r5",default=False),sg.Checkbox(text="13.09",font='David 11',key="r6",default=False),sg.Checkbox(text="11.22",font='David 11',key="r7",default=False),sg.Checkbox(text="9.82",font='David 11',key="r8",default=False)],
                    [sg.Checkbox(text="8.729",font='David 11',key="r9",default=False),sg.Checkbox(text="7.856",font='David 11',key="r10",default=False),sg.Checkbox(text="6.547",font='David 11',key="r12",default=False),sg.Checkbox(text="5.612",font='David 11',key="r14",default=False),sg.Checkbox(text="4.910",font='David 11',key="r16",default=False),sg.Checkbox(text="4.365",font='David 11',key="r18",default=False),sg.Checkbox(text="3.928",font='David 11',key="r20",default=False),sg.Checkbox(text="3.571",font='David 11',key="r22",default=False)],
                    [sg.Checkbox(text="3.143",font='David 11',key="r25",default=False),sg.Checkbox(text="2.910",font='David 11',key="r27",default=False),sg.Checkbox(text="2.709",font='David 11',key="r29",default=False),sg.Checkbox(text="2.455",font='David 11',key="r32",default=False),sg.Checkbox(text="2.311",font='David 11',key="r34",default=False),sg.Checkbox(text="2.123",font='David 11',key="r37",default=False),sg.Checkbox(text="1.964",font='David 11',key="r40",default=False)],
                    [],[],
                    [sg.Text("Output name:"), sg.Input("Test_sample1", s=15, key="test_name"), sg.Push(), sg.Text("Comments:"),sg.Input("",s=30,key="TEST1_COMMENT")], [],
                    [sg.Checkbox(text="Analyzer (Beer-Lambert & Allan Variance) ?",enable_events=True,key="test_analyzer")], [collapse(analyzerSection, 'section_analyzer', False)],
                    [sg.Push(), sg.Button("Start Test"), sg.Push()],[sg.Push(), collapse(stopTestSection, 'section_stopTest', False), sg.Push()],
                    [sg.Push(),sg.Text(str(getTestErrorText), key="test_errorText", justification='center'),sg.Push()]]
    else:
        test_values = [[sg.Push(), sg.Text("Connect to devices first or run in 'Debug Mode'"), sg.Push()]]
    return test_values

def getDatabases():
    # This function is to check and show the list of files it is possible to load to the 'Results' Rublica.
    try:
        foldersNames = os.listdir("..\\Databases")
    except:
        os.mkdir("..\\Databases")
        foldersNames = os.listdir("..\\Databases")
    foldersNames.sort()   
    return foldersNames

# The fourth layout - the results window:
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
    # This function is to update the list in the result rublica after a measurment was finished.
    foldersNames = os.listdir("..\\Results")
    foldersNames.sort()
    window['-SAMPLE_TO_PLOT-'].update(foldersNames)

# End of Layouts.

#---------------------------------------------------------------------------------------------------------------------------

# 

def open_Interactive_Graphs(dirName, analyzer_substance = False):
    try:
        command = 'py'
        if analyzer_substance:
            args = ['Interactive_Graph.py', '--csv_name', dirName+"\\", '--analyzer_substance', '1']
        else:
            args = ['Interactive_Graph.py', '--csv_name', dirName+"\\"]
        process = subprocess.Popen([command] + args)
        pid = process.pid
        return pid
    except:
        command = 'Interactive_Graph.exe'
        if analyzer_substance:
            args = ['--csv_name', dirName+"\\", '--analyzer_substance', '1']
        else:
            args = ['--csv_name', dirName+"\\"]
        process = subprocess.Popen([command] + args)
        pid = process.pid
        return pid

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
    # Checking all the condition if everything is ok and we can start the test:
    getTestErrorText = ""
    if (int(values["test_CF"]) < 700):
        getTestErrorText = "Error: The 'Center Frequency' can only be between 700nm to 1600nm."
    elif (int(values["test_SPAN"]) > 250):
        getTestErrorText = "Error: The 'Span' value can only be between XXX to YYY."
    elif (values["test_PTS"] != "Auto"):
        try:
            if (int(values["test_PTS"]) > 2000) or (int(values["test_PTS"]) < 101):
                getTestErrorText = "Error: The max Number of Points per sample is XXX points."
        except:
                getTestErrorText = "Error: The max Number of Points per sample is XXX points."
    elif ( (values["test_res"] == "Manuall (Enter a value)") and ((float(values["test_manuallRes"]) < 0) or (float(values["test_manuallRes"]) > 4) )):
        getTestErrorText = "Error: The resolution you enter is not good value."
    elif (int(values["minPL"]) < 6 or int(values["minPL"]) > 100):
        getTestErrorText = "Error: The start power of the laser must be btween 6 to 100"
    elif ( values["testPowerLevelSweep"] and (int(values["maxPL"]) < 6 or int(values["maxPL"]) > 100) ):
        getTestErrorText = "Error: The end power of the laser must be btween 6 to 100"
    elif ( values["testPowerLevelSweep"] and (int(values["minPL"]) > int(values["maxPL"])) ):
        getTestErrorText = "Error: The start power must be smaller than the end power"
    elif int(values["darkNumSamplesParameter"]) <= 0:
        getTestErrorText = "Error: The number of samples (Dark) must be higher than 0"
    elif int(values["cleanNumSamplesParameter"]) <= 0:
        getTestErrorText = "Error: The number of samples (Clean) must be higher than 0"
    elif int(values["substanceNumSamplesParameter"]) <= 0:
        getTestErrorText = "Error: The number of samples (Substannce) must be higher than 0"
    elif (not values["r1"] and not values["r2"] and not values["r3"] and not values["r4"] and not values["r5"] and not values["r6"] and not values["r7"] and not values["r8"] and not values["r9"] and not values["r10"] and not values["r12"] and not values["r14"] and not values["r16"] and not values["r18"] and not values["r20"] and not values["r22"] and not values["r25"] and not values["r27"] and not values["r29"] and not values["r32"] and not values["r34"] and not values["r37"] and not values["r40"]):
        getTestErrorText = "Error: No repetition value was chosen"
    elif (values["test_name"] == ""): # Not a must.
        getTestErrorText = "Error: No name for 'Output name'."
    elif (values["test_analyzer"] and ( (int(values["totalSampleTime"]) < 0) or (int(values["totalSampleTime"]) > 3600) )):
        getTestErrorText = "Error: (Analyzer) The 'Total time sample' must be bigger than zero. Max: 1 Hour."
    elif (values["test_analyzer"] and ( (float(values["intervalTime"]) < 0.1) or (float(values["intervalTime"]) > int(values["totalSampleTime"])) )):
        getTestErrorText = "Error: (Analyzer) The interval time must be bigger than 0.5 seconds and smaller from the Total time."
    return getTestErrorText

#---------------------------------------------------------------------------------------------------------------------------

def reopenMainL(window = None):
    # This function start the GUI window:
    mainL = [[sg.TabGroup([[sg.Tab('Connections',getConnections()), sg.Tab('Single Sample', getSampleL()), sg.Tab('Tests', getTests()), sg.Tab('Results', getResultsTabLayout())]], size = (SIZE[0]+30,SIZE[1]-70))],[sg.Button("Close"), sg.Button("Debug Mode"), sg.Push(), sg.Text(status)]]
    try:
        window.close()
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE)
    except:
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE)
    return window

def popup(message):
    #sg.theme('DarkGrey')
    sg.theme('Default')
    layout = [[sg.Text(message)]]
    window = sg.Window('Message', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    return window

#----------------------------------------------------------------------------------------------------------------------------------------

class theTestThread(threading.Thread):
    def __init__(self, arg1, arg2, arg3, arg4, arg5, arg6):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.arg1 = arg1 # Laser
        self.arg2 = arg2 # OSA
        self.arg3 = arg3 # values
        self.arg4 = arg4 # debugMode
        self.arg5 = arg5 # dirName
        self.arg6 = arg6 # window
        self.result = None

    def run(self):
        # Set names:
        laser = self.arg1
        osa = self.arg2
        values = self.arg3
        debugMode = self.arg4
        dirName = self.arg5
        window = self.arg6
        reason = None
        #
        window['test_errorText'].update("Part 1/3: Executing 'Dark' Test...")
        noiseMeasurments(laser, osa ,values, debugMode, dirName+"\\dark.csv")
        window['test_errorText'].update("Part 2/3: Executing 'Clean/Empty' Tests...")
        reason = getSweepResults(laser,osa,values,debugMode,dirName+"\\clean.csv", window, "Part 2/3: Executing 'Clean/Empty' Tests...", self)
        if reason == False:
            self.result = False
            return False
        window['test_errorText'].update("Part 2/3: Executing 'Clean/Empty' Tests... (100%)")
        # For user
        tempEvent = tkm.askokcancel(title="Enter Substance!", message="Empty measurment finished.\nPlease insert substance, then press 'OK'.\nChoosing 'Cancel' will stop the all process\nand delete all the measurments.")
        #tempEvent = sg.popup_ok_cancel("Enter Substance!", "Empty measurment finished.\nPlease insert substance, then press 'OK'.\nChoosing 'Cancel' will stop the all process\nand delete all the measurments.")
        # OK was chosen
        if tempEvent:
            window['test_errorText'].update("Part 3/3: Executing 'Substance' Test...")
            if (values['test_analyzer']):
                if (not debugMode):
                    laser.emission(0)
                    sleep(8)
                reason = getSweepResults(laser,osa,values,debugMode,dirName+"\\analyzer.csv", window, "Part 3/3: Executing 'Substance' Tests...", self) 
            else:
                reason = getSweepResults(laser,osa,values,debugMode,dirName+"\\substance.csv", window, "Part 3/3: Executing 'Substance' Tests...", self)
            if reason == False:
                self.result = False
                return False
            window['test_errorText'].update("Part 3/3: Executing 'Substance' Test... (100%)")
            # Adding to Results tab.
            updateResults(window)
            # Open a new process of the graph/grphs.
            ######################################################################### To check about this
            if reason != False: # Everyting is OK, can open Graphs window.
                if (values['test_analyzer']): 
                    graphs_pids.append(open_Interactive_Graphs(dirName, analyzer_substance = True))
                else:
                    graphs_pids.append(open_Interactive_Graphs(dirName))
            ############################################################################3
        else:
            shutil.rmtree(dirName)
        window['Start Test'].update(disabled=False)
        window['section_stopTest'].update(visible=False)
        window['test_errorText'].update("Finish Testing.")
        if reason:
            self.result = True
            return True
    # End of the test thread.

    def stop(self):
        self.stop_event.set()

#----------------------------------------------------------------------------------------------------------------------------------------

# The checking events - The managment of the GUI:
testProcess = None
window = reopenMainL()
while True:
    event, values = window.read()
    
    if event == 'Connect':
        # This function try connect the devices:
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
        # Move and working in Debug Mode to allow the relevant functions and rest of the GUI.
        debugMode = True
        status = "Debug Mode"
        getConnectionsText = getSamplesText = getTestsText = getTestErrorText = "Now you are working in 'Debug Mode'!"
        laser = None
        osa = None
        window = reopenMainL(window)

    elif event == 'Sample':
        # To do only one sample.
        if ( isConnected or (not debugMode) ):
            setConfig(laser,osa,values["CF"],values["SPAN"],values["PTS"],values["POWER"],values["REP"])
            getSamplesText = runSample(laser,osa, isConnected,debugMode, values)
    
    elif event == "testPowerLevelSweep":
        # To show the power test parameters setting.
        if (values["testPowerLevelSweep"] == True):
            window['section_powerSweep'].update(visible=True)
        else:
            window['section_powerSweep'].update(visible=False)

    elif event == "selectAllRep":
        # Checking or unchecking all the reputations together.
        RepList = ["r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r12","r14","r16","r18","r20","r22","r25","r27","r29","r32","r34","r37","r40"]
        for i in RepList:
            values[i] = values['selectAllRep']
            window[i].update(values["selectAllRep"])
        print(values)

    elif event == "test_analyzer":
        # To show the parameters part of the analyzer setting.
        if (values["test_analyzer"] == True):
            window['section_analyzer'].update(visible=True)
        else:
            window['section_analyzer'].update(visible=False)

    elif event == "Start Test":
        if (isConnected or debugMode):
            getTestErrorText = checkStartConditions(values) # Checking if all the parameters & conditions to start the tests are OK.
            if (getTestErrorText == ""):
                # EveryThing is OK - Starting the test.
                if values["test_res"] == "Manuall (Enter a value)":
                    res = values["test_manuallRes"]
                else:
                    res = values["test_res"]
                window['Start Test'].update(disabled=True)
                window['section_stopTest'].update(visible=True)
                window['test_errorText'].update("Executing Clean Test...")
                dirName = makedirectory(values["test_name"],values["test_CF"],values["test_SPAN"],values["test_PTS"],values["test_sens"],res,values["test_analyzer"])
                testThread = theTestThread(laser,osa,values,debugMode,dirName,window)
                testThread.start()
            else:
                window['test_errorText'].update(getTestErrorText)
            getTestErrorText = ""

    elif event == "Stop Test":
        tempEvent = sg.popup_ok_cancel("Stop Running test?", "Are you sure you want to stop the running test?\n'Ok' - Yes, stop the test.\n'Cancel' - Opps, continue the test.")
        if (tempEvent.upper()=="OK"):
            # Open and close a window
            testThread.stop()
            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
            animation = time.time()
            timeToWaitForStop = time.time()
            while ( (testThread.result != False) and (time.time() - timeToWaitForStop <= 2*float(values['intervalTime'])) ):
                if (time.time() - animation > 0.05):
                    sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                    animation = time.time()
            sg.PopupAnimated(None)
            window['section_stopTest'].update(visible=False)
            window['Start Test'].update(disabled=False)
            window['test_errorText'].update("The testing process was stopped.")
            sg.popup_ok("The test process was stopped by the user!")
            getTestErrorText = ""

    elif event == "-LOAD_SAMPLE-":
        # This function load a result from the forth rublic.
        try:
            command = 'py'
            dirName = "..\\Results\\"+values['-SAMPLE_TO_PLOT-'][0]+"\\"
            filesList = os.listdir(dirName)
            filesList = [name[:-4] for name in filesList]
            if 'analyzer' in filesList:
                graphs_pids.append(open_Interactive_Graphs(dirName, analyzer_substance = True))
            graphs_pids.append(open_Interactive_Graphs(dirName))
        except:
            continue

    elif event == '-DELETE_SAMPLE-':
        #  This function delete the selected result from the results list in the forth rublic.
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
        # This function close the main GUI.
        window.close()
        for pid in graphs_pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Process with PID {pid} killed successfully.")
            except OSError as e:
                print(f"Error killing process with PID {pid}: {e}")
        break

# End of GUI





#_________________________________________________________________________________Delete_________________________________________________________________________________
