# This file contains the Graphical user interface and delivers the requests from the user to devices.
from OSA import OSA
from LASER import Laser
from Operator import getSweepResults, runSample, setConfig, makedirectory, noiseMeasurments
from Interactive_Graph import interactiveGraph
from multiprocessing import Process, freeze_support
from json import load, dump
from time import sleep
import time
import os
import shutil
import threading
import tkinter.messagebox as tkm
import PySimpleGUI as sg

# Globals:
global layouts
global cwd
global connectionsDict
global osa
global laser
global isConnected
global debugMode
global status
global getConnectionsText
global getSamplesText
global getTestsText
global getTestErrorText
isConnected = False # Until first connection
debugMode = False
status = "The devices are not connected"
getConnectionsText = "If you don't succed to connect you can work in 'Debug Mode'"
getSamplesText = "Connect to devices first or work in 'Debug Mode'"
getTestsText = "Connect to devices first or work in 'Debug Mode'"
getTestErrorText = ""
graphs_pids = []
# sg.theme_previewer()

# Initial reads:
cwd = os.getcwd() # The Currently working directory - where this .py file can be found.

# Possible values for the laser Reputation.
rep_values_MHz = {'78.56MHz': 1, '39.28MHz': 2, '29.19MHz': 3, '19.64MHz': 4, '15.71MHz': 5, 
                '13.09MHz': 6, '11.22MHz': 7, '9.821MHz': 8, '8.729MHz': 9, '7.856MHz': 10, '6.547MHz': 12, 
                '5.612MHz': 14, '4.910MHz': 16, '4.365MHz': 18, '3.928MHz': 20, '3.571MHz': 22, '3.143MHz': 25, 
                '2.910MHz': 27, '2.709MHz': 29, '2.455MHz': 32, '2.311MHz': 34, '2.123MHz': 37, '1.964MHz': 40}

# The size of the GUI window (Width, Length).
SIZE = (600,630)

sg.theme('DefaultNoMoreNagging')
# sg.theme('DarkBlue')
# sg.theme('Default')

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
                    [sg.Push(), sg.Text(getConnectionsText, key='getConnectText'), sg.Push()]]
    return connections

def updateConnections(values):
    # This function gets the values from the user in the main GUI window and if the connection was successful than it saves the correct parameters (IP Address, Port, COM, Serial) for the next connection.
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    connectionsDict["OSA"]["IP"] = values[0]
    connectionsDict["OSA"]["PORT"] = values[1]
    connectionsDict["LASER"]["COM"] = values[2]
    connectionsDict["LASER"]["Serial"] = values[3]
    with open(cwd+"\\connections.json", 'w') as f:
        dump(connectionsDict, f)

#--- Here we finished with Connections.

def collapse(layout, key, visible):
    # Hide or show the relevants fields. This function responsible for allowing us to show and hide relevant parts in a layout according to user checkbox chooses. When the relevant choice done there is an event, and this function is called to do the work.
    return sg.pin(sg.Column(layout, key=key, visible=visible))

def getSampleL():
    # This function creates the layout for the second tab, the 'Single Sample' tab. This function allows to operate one single measurement and by that to learn each relevant parameter and his influence on the measurement result. To be prepared for the full test in the next tab.
    sampleL = [[sg.Push(), sg.Text("OSA", font='David 15 bold'), sg.Push()],
                [sg.Text("Center Wavelength:"), sg.Push(), sg.Input("1500",s=15,key="CF"), sg.Text("[nm]")],
                [sg.Text("Span:"), sg.Push(), sg.Input("50",s=15,key="SPAN"), sg.Text("[nm]")],
                [sg.Text("Number of Points (Auto recommended):"), sg.Push(), sg.Input("Auto",s=15,key="PTS")],
                [sg.Text("Sensetivity: "), sg.Push(), sg.Combo(["NORM/HOLD", "NORM/AUTO", "NORMAL", "MID", "HIGH1", "HIGH2", "HIGH3"], default_value='MID',key="sens")],
                [sg.Text("Resolution: "), sg.Push(), sg.Combo(["0.02nm <0.019nm>", "0.05nm <0.043nm>", "0.1nm <0.076nm>", "0.2nm <0.160nm>", "0.5nm <0.408nm>", "1nm <0.820nm>", "2nm <1.643nm>"], enable_events=True, default_value="1nm <0.820nm>" ,key="res")],
                [sg.Text("")],
                [sg.Push(), sg.Text("Laser", font='David 15 bold'), sg.Push()],
                [sg.Text("Power:"), sg.Push(), sg.Input("6",s=15, key="POWER"), sg.Text("%")],
                [sg.Text("Repetition Rate:"), sg.Push(), sg.Combo(list(rep_values_MHz.keys()), key="REP", default_value=list(rep_values_MHz.keys())[0])],
                [sg.Text("")],
                [sg.Push(), sg.Text("Misc", font='David 15 bold'), sg.Push()],
                [sg.Checkbox("Save sample", key="Save"), sg.Push(), sg.Text("Output name:"), sg.Input("demo_sample", s=15, key="sample_name")],
                [sg.Checkbox("Plot sample", key="Plot")],
                [sg.Push(), sg.Button("Sample"), sg.Push()],
                [sg.Push(), sg.Text(getSamplesText, key="singleSampleText"), sg.Push()]]
    sample_message = [[sg.Push(), sg.Text("Connect to devices first or work in 'Debug Mode'"), sg.Push()]]
    sampleLayout = [[sg.Push(), collapse(sample_message, 'sample_status_message', True), sg.Push()], [sg.Push(), collapse(sampleL, 'sample_status_menu', False), sg.Push()]]
    return sampleLayout

def getTests():
    # This function creates the layout for the third tab, the 'Tests' tab. Here it is possible to set combinations of powers and repetitions, to choose the Laser and OSA parameters, to set the total time and interval time for Allan deviation and Beer-Lambert law.
    powerSweepSection = [[sg.Text("Stop Power Level"), sg.Input("50",s=3,key="maxPL"),sg.Text("Step:"), sg.Input("10",s=3,key="stepPL")]]
    analyzerSection = [[sg.Text("Total time for test"),sg.Input("60",s=3,key="totalSampleTime"),sg.Text("[seconds]"),sg.Push(),sg.Text("Interval time: "),sg.Input("1",
    s=3,key="intervalTime"), sg.Text("seconds")]]
    stopTestSection = [[sg.Button("Stop Test")]]
    test_values = [[sg.Push(), sg.Text("Tests - choose the tests you want", font='David 15 bold'), sg.Push()],
                [sg.Text("Center Wavelength:"), sg.Input("1500",s=5,key="test_CF"), sg.Text("[nm]"),
                sg.Text("Span:"), sg.Input("50",s=5,key="test_SPAN"), sg.Text("[nm]")],
                [sg.Text("Number of Points: (Auto recommended)"), sg.Input("Auto",s=12,key="test_PTS"), sg.Text("Sensetivity: "), sg.Combo(["NORM/HOLD", "NORM/AUTO", "NORMAL", "MID", "HIGH1", "HIGH2", "HIGH3"], default_value='MID',key="test_sens")], [sg.Text("Resolution: "), sg.Combo(["0.02nm <0.019nm>", "0.05nm <0.043nm>", "0.1nm <0.076nm>", "0.2nm <0.160nm>", "0.5nm <0.408nm>", "1nm <0.820nm>", "2nm <1.643nm>"], enable_events=True, default_value="1nm <0.820nm>" ,key="test_res")],
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
                [sg.Checkbox(text="Analyzer (Beer-Lambert & Allan Deviation) ?",enable_events=True,key="test_analyzer")], [collapse(analyzerSection, 'section_analyzer', False)],
                [sg.Push(), sg.Button("Start Test"), sg.Push()],[sg.Push(), collapse(stopTestSection, 'section_stopTest', False), sg.Push()],
                [sg.Push(),sg.Text(str(getTestErrorText), key="test_errorText", justification='center'),sg.Push()]]
    test_message = [[sg.Push(), sg.Text("Connect to devices first or run in 'Debug Mode'"), sg.Push()]]
    #
    test_values = [[sg.Push(), collapse(test_message, 'test_status_message', True), sg.Push()], [sg.Push(), collapse(test_values, 'test_status_menu', False), sg.Push()]]
    return test_values

def getDatabases():
    # This function checks and show the list of files that are possible to load for the 'Results' tab.
    try:
        foldersNames = os.listdir("..\\Databases")
    except:
        os.mkdir("..\\Databases")
        foldersNames = os.listdir("..\\Databases")
    foldersNames.sort()   
    return foldersNames

# The fourth layout - the results window:
def getResultsTabLayout():
    # This function creates the layout for the fourth tab, the 'Results' tab. This tab allows to load, show, and compare on the graphs previous measurements were done.
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

def reopenMainL(window = None):
    # This function start the GUI window:
    mainL = [[sg.TabGroup([[sg.Tab('Connections',getConnections(), key='-TAB1-'), sg.Tab('Single Sample', getSampleL(), key='-TAB2-'), sg.Tab('Tests', getTests(), key='-TAB3-'), sg.Tab('Results', getResultsTabLayout(), key='-TAB4-')]], key='-TABGROUP-', size = (SIZE[0]+30,SIZE[1]-70))],[sg.Button("Close"), sg.Button("Debug Mode"), sg.Push(), sg.Text(status, key='status')]]
    try:
        window.close()
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE, finalize = True)
    except:
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE, finalize = True)
    return window

window = reopenMainL()
window['-TAB3-'].select()
print("Hello")


#  A solution: https://github.com/PySimpleGUI/PySimpleGUI/issues/2591



#subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'PySimpleGUI'])




















# -------------------------------------------------------------------------------------------------------------------------------------------

# import PySimpleGUI as sg

# tab1_layout = [[sg.Text('This is tab 1')]]
# tab2_layout = [[sg.Text('This is tab 2')]]

# layout = [[sg.TabGroup([[sg.Tab('Tab 1', tab1_layout), sg.Tab('Tab 2', tab2_layout)]], key='-TABGROUP-')],
#           [sg.Button('Select Tab 1'), sg.Button('Select Tab 2')]]

# window = sg.Window('Window Title', layout)

# while True:
#     event, values = window.read()
#     if event == sg.WIN_CLOSED:
#         break
#     elif event == 'Select Tab 1':
#         window['-TABGROUP-'].SelectTab(0)
#     elif event == 'Select Tab 2':
#         window['-TABGROUP-'].SelectTab(1)

# window.close()



# #import tkinter as tk
# from tkinter import messagebox

# #root = tk.Tk()

# def on_button_click():
#     messagebox.showinfo("Message", "Hello, World!")
#     # The message box will close when the user clicks the "OK" button or presses the "Enter" key

# messagebox.showinfo("Message", "Hello, World!")
# #button = tk.Button(root, text="Show Message", command=on_button_click)
# #button.pack()

# #root.mainloop()
