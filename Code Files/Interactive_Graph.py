# Interactive Graph GUI:
import pandas as pd
import PySimpleGUI as sg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.colors as mcolors
from Analyzer import getNormlizedByCustomFreq, beerLambertLaw
import argparse
import os

GRAPH_SIZE = (1280,1024)
PLOT_SIZE = (12,7)

graphStatusText = "Choose graph type"
imageStatusText = ""


#---------------------------------------------------------------------------------------------------------------------------

###############################################Class of Mouse################################################

# https://www.tutorialspoint.com/how-to-add-a-cursor-to-a-curve-in-matplotlib
class CursorClass(object):
    def __init__(self, ax, x, y):
        self.ax = ax
        self.ly = ax.axvline(color='yellow', alpha=0.5)
        self.marker, = ax.plot([0], [0], marker="o", color="red", zorder=3)
        self.x = x
        self.y = y
        self.txt = ax.text(0.7, 0.9, '')

    def mouse_event(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            indx = np.searchsorted(self.x, [x])[0]
            x = self.x[indx]
            y = self.y[indx]
            self.ly.set_xdata(x)
            self.marker.set_data([x], [y])
            self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
            self.txt.set_position((x, y))
            self.ax.figure.canvas.draw_idle()
        else:
            return
        
    # cursor = CursorClass(fig, x, list(df.iloc[[row[0]]].values.tolist())[0][10:])
    # cid = plt.connect('motion_notify_event', cursor.mouse_event)

# def updateLabels(fig, plotedDictionary):
    # plt.legend()
    # colorLabels = {}
    # for key in plotedDictionary.keys():
    #     c = plotedDictionary[key][0]
    #     colorLabels[key] = c._color

#############################################################################################################

#---------------------------------------------------------------------------------------------------------------------------

class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

def draw_figure_w_toolbar(canvas, fig, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)
    return figure_canvas_agg

# Layouts:

def collapse(layout, key, visible):
    # Hide or show the relevants fields.
    return sg.pin(sg.Column(layout, key=key, visible=visible))

def getLayout(frequencyList, powerList):
    # xAxis is a list of lists.
    sweepPowerCompareSection = [[sg.Push(), sg.Text("Select Repetition:"), sg.Text("Select Powers:"), sg.Push()],
    [sg.Push(), sg.Listbox(values=frequencyList, s=(14,10), enable_events=True, select_mode='single', key='_RepetitionListBoxPC_'),sg.Listbox(powerList, size=(14,10), enable_events=True, bind_return_key=True, select_mode='multiple', key='_PowerListBoxPC_'), sg.Push()]]
    sweepRepetitionCompareSection = [[sg.Push(), sg.Text("Select Powers:"), sg.Text("Select Repetition:"), sg.Push()],
    [sg.Push(), sg.Listbox(powerList, size=(14,10), enable_events=True, bind_return_key=True, select_mode='single', key='_PowerListBoxRC_'), sg.Listbox(values=frequencyList, s=(14,10), enable_events=True, select_mode='multiple', key='_RepetitionListBoxRC_'), sg.Push()]]
    beerLambertResultsSection = [[sg.Push(), sg.Text("Beer Lambert")],[sg.Text("The concentration of the substance is:")],[sg.Text(beerLambertLaw()), sg.Push()]]
    allanVarianceCompareSection = [[sg.Push(), sg.Text("Allan Variance"), sg.Push()]]
    normValue = [[sg.Push(), sg.Text("The norm frequency:"), sg.Input("1500",s=5,key="normValue"), sg.Text("[nm]"), sg.Button("OK"), sg.Push()]]
    graphMode = [[sg.Push(), sg.Text(graphStatusText), sg.Push()]]
    menu_layout = [[collapse(graphMode, 'section_graphMode', True)],[sg.Push(),sg.Checkbox(text="Normal\nsample",font='David 11',key="normCheckBox", enable_events=True, default=False), sg.Checkbox(text="Clean\nsample",font='David 11',key="cleanCheckBox",enable_events=True, default=False), sg.Checkbox(text="Substance\nsample",font='David 11',key="substanceCheckBox", enable_events=True, default=False), sg.Push()],[collapse(normValue, 'section_normValue', False)], [sg.Push(), sg.Combo(["Sweep (Power Compare)", "Sweep (Repetition Compare)","Beer Lambert", "Allan Variance"], enable_events=True, key='-PLOT_TYPE-', default_value="Sweep (Power Compare)"), sg.Push()],
    [collapse(sweepPowerCompareSection, 'section_sweepPowerCompare', True)],
    [collapse(sweepRepetitionCompareSection, 'section_sweepRepetitionCompare', False)],
    [collapse(beerLambertResultsSection, 'section_beerLambertResults', False)],
    [collapse(allanVarianceCompareSection, 'section_allanVarianceCompare', False)], [sg.Push(), sg.Text("Enter name for image:"), sg.Input("save_name",s=20,key="imageName"), sg.Push()], [sg.Push(),sg.Button("Close Graph"), sg.Button("Clear All"), sg.Button("Save Image"), sg.Push()],[sg.Push(), sg.Text(str(imageStatusText)), sg.Push()]]
    graph_layout = [
        [sg.Push(),sg.Text("Graph Space:"),sg.Push()],
        [sg.T('Controls:')],
        [sg.Canvas(key='controls_cv')],
        [sg.T('Figure:')],
        [sg.Column(
            layout=[
                [sg.Canvas(key='figCanvas',
                        # it's important that you set this size
                        size=(400 * 2, 400)
                        )]
            ],
            background_color='#DAE0E6',
            pad=(0, 0)
    )],
        ]
    Layout = [[sg.Column(menu_layout), sg.Column(graph_layout, s=GRAPH_SIZE)]]
    return Layout

def getAllanLayout(frequencyList, powerList, numIntervals):
    # xAxis is a list of lists.
    menu_layout = [[sg.Text("Select graph type:")],
                   [sg.Combo(["Raw Data","Ratio Data"], default_value="Ratio Data", key='-ALLAN_GRAPH_TYPE-', enable_events=True)],
                   [sg.Text("Select Rep and Power pair:")],
                   [sg.Listbox(values=frequencyList, s=(14,10), enable_events=True, select_mode='single', key='-ALLAN_REP-'),
                    sg.Listbox(values=powerList, s=(14,10), enable_events=True, select_mode='single', key='-ALLAN_POWER-')],
                   [sg.Button("Close", key='-ALLAN_CLOSE-')]
                   
                   ]
    graph_layout = [
        [sg.Push(),sg.Text("Graph Space:"),sg.Push()],
        [sg.T('Controls:')],
        [sg.Canvas(key='controls_cv')],
        [sg.T('Figure:')],
        [sg.Column(
            layout=[
                [sg.Canvas(key='figCanvas',
                        # it's important that you set this size
                        size=(400 * 2, 400)
                        )]
            ],
            background_color='#DAE0E6',
            pad=(0, 0)
        )],
        [sg.Text('Graphs Interval')],
        [sg.Slider(range=(min(numIntervals), max(numIntervals)), size=(60, 10),
                orientation='h', key='-SLIDER-', resolution=1/(10*len(numIntervals)))],
        [sg.Button("Hold", key="-HOLD_TRACE-"), sg.Button("Clear All", key="-ALLAN_CLEAR-"), sg.Button("Play/Pause", key="-ALLAN_PLAY-"), sg.Push()]
        ]
    Layout = [[sg.Column(menu_layout), sg.Column(graph_layout, s=GRAPH_SIZE)]]
    return Layout

# End of Layouts.

#---------------------------------------------------------------------------------------------------------------------------

# Additional functions:

def setTitels(fig, graphMode):
    fig.clear()
    if (graphMode == ""):
        return
    if ( (graphMode == "clean") or (graphMode == "substance") ):
        plt.xlabel('Wavelength [nm]')
        plt.ylabel('Power [dB]')
        plt.title("No parameters choosen")
    if (graphMode == "norm"):
        plt.xlabel('Wavelength [nm]')
        plt.ylabel('Normal Ratio')
        plt.title("No parameters choosen")
        
def changeGraph(df, fig, xAxis, rep,power,mode, graphMode = 'clean'):
    # xAxis is a list.
    # yAxis is a dictionary.
    setTitels(fig, graphMode)
    yDictionary = {}
    for r in rep:
        for p in power:
            row = (np.where((df.REP_RATE == r) & (df.POWER == int(p))))[0]
            yPlot = list(df.iloc[[row[0]]].values.tolist())[0][10:]
            if (mode == 'PowerSweep'):
                yDictionary[p] = plt.plot(xAxis, yPlot, label=p+'%')
            if (mode == 'RepetitionSweep'):
                yDictionary[r] = plt.plot(xAxis, yPlot, label=r)
    if (mode == 'PowerSweep'):
        graphTitle = rep[0]+" - Power Comparation Sweep Graph"
    if (mode == 'RepetitionSweep'):
        graphTitle = power[0]+"% - Repetition Comparation Sweep Graph"
    plt.title(graphTitle)
    plt.legend()
    return yDictionary

def checkForParameters(fig, a, b, graphMode):
    if ( (len(a) == 0) or (len(b) == 0) ):
        setTitels(fig, graphMode)
        if ( (len(a) == 0) and (len(b) == 0 ) ):
            plt.title('No parameters were choosen to show graph')
        elif (len(a) == 0):
            plt.title('No parameter/s "Repetition" choosen to show graph')
        elif (len(b) == 0):
            plt.title('No parameter/s "Power" choosen to show graph')
        return False
    else:
        return True

def resetBoxs(win):
    win.Element('_PowerListBoxPC_').update(values=[])
    win.Element('_RepetitionListBoxPC_').update(values=[])
    win.Element('_PowerListBoxRC_').update(values=[])
    win.Element('_RepetitionListBoxRC_').update(values=[])
    win.Refresh()
    return win

def updateDataframe(df,fig,graphMode,window):
    frequencyList = (df["REP_RATE"].unique())
    powerList = (df["POWER"].unique())
    powerList = [str(x) for x in powerList]
    x = []
    axis = list(df.columns.values.tolist())[10:]
    for val in axis:
        x.append(str(round(float(val), 2)))
    setTitels(fig,graphMode)
    if ( (graphMode == "clean") or (graphMode == "substance") ):
        plt.axis([ int(float(x[0])), int(float(x[-1])) , -100, 0])
    if (graphMode == "norm"):
        plt.axis([ int(float(x[0])), int(float(x[-1])) , -10, 10])
    window.Element('_PowerListBoxPC_').update(values=powerList)
    window.Element('_RepetitionListBoxPC_').update(values=frequencyList)
    window.Element('_PowerListBoxRC_').update(values=powerList)
    window.Element('_RepetitionListBoxRC_').update(values=frequencyList)
    window.Refresh()
    d1 = {}
    d2 = {}
    return x, d1, d2, window

#---------------------------------------------------------------------------------------------------------------------------

# def draw_figure(canvas, figure):
#     # This function embedded the ploted graph into the graph window.
#     figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
#     figure_canvas_agg.draw()
#     figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
#     return figure_canvas_agg

#---------------------------------------------------------------------------------------------------------------------------

# The managment function:

def interactiveGraph(csvFile):
    filesList = os.listdir(csvFile)
    for file in filesList:
        if file[:-4] == 'clean' or file[:-4] == 'substance':
            type_of_graph = 'regular'
            break
        elif file[:-4] == 'allan':
            type_of_graph = 'allan'
            break

    if type_of_graph == 'regular':
        regularSweepGraph(csvFile)
    elif type_of_graph == 'allan':
        allanVarianceGraph(csvFile)

def allanVarianceGraph(csvFile):

    colors = [name for name, hex in mcolors.CSS4_COLORS.items()
                   if np.mean(mcolors.hex2color(hex)) < 0.7]
    colors.pop(0)
    color = colors[0]

    def update_internal_graph(ax, temp_df, fig_agg, i, color):
        ax.cla()
        ax.grid()
        try:
            line1 = ax.plot(np.asarray(temp_df.columns[11:], float), temp_df.iloc[i,11:], label='{}_{}_TS_{:.2f}'.format(temp_df['REP_RATE'].iloc[i], temp_df['POWER'].iloc[i], temp_df['Interval'].iloc[i]), color = color)
            # Add a legend
            ax.legend(loc='upper right')
            fig_agg.draw()
            return line1[0]
        except:
            return False

    def add_allan_history(ax, hold_lines, fig_agg):
        for line1 in hold_lines.values():
            ax.add_line(line1)
        ax.legend(loc='upper right')
        fig_agg.draw()

    sg.theme('DarkBlue')

    try:
        allan_df = pd.read_csv(csvFile + 'allan_ratio.csv')
    except:
        print("Coudln't read "+csvFile + 'allan_ratio.csv')
        return False
    
    window2 = sg.Window("Interactive Allan Variance Graph", getAllanLayout(allan_df['REP_RATE'].unique().tolist(), allan_df['POWER'].unique().tolist(), allan_df['Interval'].unique().tolist()),finalize=True)
    interval_list = allan_df['Interval'].unique().tolist()
    # draw the initial plot in the window
    fig = plt.Figure()
    fig.set_figwidth(PLOT_SIZE[0])
    fig.set_figheight(PLOT_SIZE[1]-2)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("Power(0)/Power(t)")
    ax.grid()
    fig_agg = draw_figure_w_toolbar(window2['figCanvas'].TKCanvas, fig, window2['controls_cv'].TKCanvas)
    hold_lines = {}

    slider_elem = window2['-SLIDER-']
    window2['-SLIDER-'].bind('<ButtonRelease-1>', ' Release')
    slider_update = False
    test_selected = False
    i = 0

    while True:

        event, values = window2.read(timeout=1000)
        # Closing the graph.
        if ( (event == '-ALLAN_CLOSE-') or (event == sg.WIN_CLOSED) ):
            window2.close()
            break
        if event == '-ALLAN_PLAY-' and test_selected:
            # Start or stop auto switching
            slider_update = not slider_update
        if slider_update and  event == '__TIMEOUT__':
            # Update to next timestamp
            slider_elem.update(i)
            curr_label = '{}_{}_TS_{:.2f}'.format(temp_df['REP_RATE'].iloc[i], temp_df['POWER'].iloc[i], temp_df['Interval'].iloc[i])
            if curr_label not in hold_lines.keys():
                line1 = update_internal_graph(ax, temp_df, fig_agg, i, color)
                add_allan_history(ax, hold_lines, fig_agg)
            i = (i+1) % len(interval_list)

        if values['-ALLAN_REP-'] and values['-ALLAN_POWER-'] and not test_selected:
            # First time test selection
            temp_df = allan_df[(allan_df['REP_RATE'] == values['-ALLAN_REP-'][0]) & (allan_df['POWER'] == values['-ALLAN_POWER-'][0])]
            if len(temp_df) > 0:
                test_selected = True
                slider_update = True
                slider_elem.Update(range=(min(temp_df['Interval']), max(temp_df['Interval'])))
                interval_list = temp_df['Interval'].unique().tolist()
            else:
                test_selected = False

        if test_selected and (event == '-ALLAN_REP-' or event == '-ALLAN_POWER-'):
            # Test Update
            temp_df = allan_df[(allan_df['REP_RATE'] == values['-ALLAN_REP-'][0]) & (allan_df['POWER'] == values['-ALLAN_POWER-'][0])]
            if len(temp_df) > 0:
                test_selected = True
                slider_update = True
                slider_elem.Update(range=(min(temp_df['Interval']), max(temp_df['Interval'])))
                interval_list = temp_df['Interval'].unique().tolist()
                i = 0
            else:
                test_selected = False
        
        if event == '-SLIDER- Release':
            interval = interval_list[np.argmin([abs(values['-SLIDER-']-element) for element in interval_list])]
            i = interval
            curr_label = '{}_{}_TS_{:.2f}'.format(temp_df['REP_RATE'].iloc[i], temp_df['POWER'].iloc[i], temp_df['Interval'].iloc[i])
            if curr_label not in hold_lines.keys():
                line1 = update_internal_graph(ax, temp_df, fig_agg, i, color)
                add_allan_history(ax, hold_lines, fig_agg)

        if event == '-HOLD_TRACE-':
            if line1 != False:
                hold_lines[line1._label] = line1
                colors.remove(color)
                color = colors[0]

        if event == '-ALLAN_CLEAR-':
            ax.cla()
            ax.grid()
            fig_agg.draw()
            hold_lines = {} # deleting history
            colors = [name for name, hex in mcolors.CSS4_COLORS.items()
                   if np.mean(mcolors.hex2color(hex)) < 0.7]
            colors.pop(0)
            
        if event == '-ALLAN_GRAPH_TYPE-':
            # ["Raw Data","Ratio Data"]
            ax.cla()
            ax.grid()
            i = 0
            fig_agg.draw()
            if values['-ALLAN_GRAPH_TYPE-'] == "Ratio Data":
                try:
                    allan_df = pd.read_csv(csvFile + 'allan_ratio.csv')
                    ax.set_ylabel("Power(0)/Power(t)")
                except:
                    print("Coudln't read "+csvFile + 'allan_ratio.csv')
                    exit()
            else:
                try:
                    allan_df = pd.read_csv(csvFile + 'allan.csv')
                except:
                    print("Coudln't read "+csvFile + 'allan.csv')
                    exit()
            window2['-ALLAN_REP-'].update(allan_df['REP_RATE'].unique().tolist())
            window2['-ALLAN_POWER-'].update(allan_df['POWER'].unique().tolist())
            test_selected = False
            slider_update = False
            interval_list = allan_df['Interval'].unique().tolist()

def regularSweepGraph(csvFile):
    sg.theme('DarkBlue')
    clean = True
    substance = True
    norm = True
    graphMode = ""
    try:
        df_clean = pd.read_csv(csvFile + 'clean.csv')
    except:
        clean = False
    try:
        df_substance = pd.read_csv(csvFile + 'substance.csv')
    except:
        substance = False
    if ( (clean != True) or (substance != True) ):
        norm = False
    if ( (clean == False) and (substance == False) and (norm == False) ):
        tempEvent = sg.popup_ok_cancel("There was a problem to load the files. Press 'OK' to exit.")
        exit()
    
    yAxisPowerS_dictionary = {}
    yAxisRepS_dictionary = {}
    frequencyList = []
    powerList = []
    x = []

    window2 = sg.Window("Interactive Graph", getLayout(frequencyList, powerList),finalize=True)
    # Creating the automatic first graph:
    fig = plt.figure()
    plt.ion() 
    # fig = plt.gcf()
    fig.set_figwidth(PLOT_SIZE[0])
    fig.set_figheight(PLOT_SIZE[1])
    # draw_figure(window2['figCanvas'].TKCanvas, fig)
    draw_figure_w_toolbar(window2['figCanvas'].TKCanvas, fig, window2['controls_cv'].TKCanvas)
    plt.title('No Plot to show. Choose data...')
    # Set the x-axis
    start_f = float(df_clean.columns[10])
    stop_f = float(df_clean.columns[-1])
    
    # End of creating the graph.

    while True:

        event, values = window2.read()
        # Closing the graph.
        if ( (event == 'Close Graph') or (event == sg.WIN_CLOSED) ):
            window2.close()
            break
        # Clear the graph and the relevant parametrs.
        elif event == 'Clear All':
            if (values["-PLOT_TYPE-"] == "Sweep (Power Compare)"):

                window2['_PowerListBoxPC_'].update(set_to_index=[])
                window2['_RepetitionListBoxPC_'].update(set_to_index=[])
                yAxisPowerS_dictionary = {}
            elif (values["-PLOT_TYPE-"] == "Sweep (Repetition Compare)"):
                window2['_PowerListBoxRC_'].update(set_to_index=[])
                window2['_RepetitionListBoxRC_'].update(set_to_index=[])
                yAxisRepS_dictionary = {}
            else:
                window2['_PowerListBoxPC_'].update(set_to_index=[])
                window2['_RepetitionListBoxPC_'].update(set_to_index=[])
                window2['_PowerListBoxRC_'].update(set_to_index=[])
                window2['_RepetitionListBoxRC_'].update(set_to_index=[])
                yAxisPowerS_dictionary = {}
                yAxisRepS_dictionary = {}
            setTitels(fig,graphMode)
        elif event == '-PLOT_TYPE-':
            if (values["-PLOT_TYPE-"] == "Sweep (Power Compare)"):
                window2['section_sweepPowerCompare'].update(visible=True)
                window2['section_sweepRepetitionCompare'].update(visible=False)
                window2['section_beerLambertResults'].update(visible=False)
                window2['section_allanVarianceCompare'].update(visible=False)
                window2.Element('_PowerListBoxPC_').Update(select_mode='multiple')
                window2.Element('_RepetitionListBoxPC_').Update(select_mode='single')
                if ( checkForParameters(fig, values['_RepetitionListBoxPC_'], values['_PowerListBoxPC_'], graphMode) ):
                    yAxisPowerS_dictionary = changeGraph(df, fig, x, values['_RepetitionListBoxPC_'], values['_PowerListBoxPC_'], "PowerSweep", graphMode)
            elif (values["-PLOT_TYPE-"] == "Sweep (Repetition Compare)"):
                window2['section_sweepPowerCompare'].update(visible=False)
                window2['section_sweepRepetitionCompare'].update(visible=True)
                window2['section_beerLambertResults'].update(visible=False)
                window2['section_allanVarianceCompare'].update(visible=False)
                window2.Element('_PowerListBoxRC_').Update(select_mode='single')
                window2.Element('_RepetitionListBoxRC_').Update(select_mode='multiple')
                if ( checkForParameters(fig, values['_RepetitionListBoxRC_'], values['_PowerListBoxRC_'], graphMode) ):
                    yAxisRepS_dictionary = changeGraph(df, fig, x, values['_RepetitionListBoxRC_'], values['_PowerListBoxRC_'], "RepetitionSweep", graphMode)
            elif (values["-PLOT_TYPE-"] == "Beer Lambert"):
                window2['section_sweepPowerCompare'].update(visible=False)
                window2['section_sweepRepetitionCompare'].update(visible=False)
                window2['section_beerLambertResults'].update(visible=True)
                window2['section_allanVarianceCompare'].update(visible=False)
            elif (values["-PLOT_TYPE-"] == "Allan Variance"):
                window2['section_sweepPowerCompare'].update(visible=False)
                window2['section_sweepRepetitionCompare'].update(visible=False)
                window2['section_beerLambertResults'].update(visible=False)
                window2['section_allanVarianceCompare'].update(visible=True)  
        elif (event == '_RepetitionListBoxPC_'):
            if ( checkForParameters(fig, values['_RepetitionListBoxPC_'], values['_PowerListBoxPC_'],graphMode) ):
                # If 'True' Update/Create a new Graph:
                yAxisPowerS_dictionary = changeGraph(df, fig, x, values['_RepetitionListBoxPC_'], values['_PowerListBoxPC_'], "PowerSweep", graphMode)
            # IF 'False' - in checkForParameters function.    
        elif (event == '_PowerListBoxPC_'):
            # check for change in the list and update dictionary.
            if ( checkForParameters(fig, values['_RepetitionListBoxPC_'], values['_PowerListBoxPC_'],graphMode) ):
                # Adding the miss data from PowerListBoxPC to yAxisPowerS_dictionary:
                for key in values['_PowerListBoxPC_']:
                    if key in yAxisPowerS_dictionary.keys():
                        None # OK, don't do anything.
                    else: # Plot the data and add to the yAxisPowerS dictionary.
                        row = (np.where((df.REP_RATE == values['_RepetitionListBoxPC_'][0]) & (df.POWER == int(key))))[0]
                        yAxisPowerS_dictionary[key] = plt.plot(np.asarray(x, float), list(df.iloc[[row[0]]].values.tolist())[0][10:], label=key+'%')
                        plt.xticks(np.arange(start_f, stop_f, (start_f-stop_f)/10))
                        window2['section_graphMode'].update()
                        print("The yAxisPowerS_dictionary (Adding) is: ", yAxisPowerS_dictionary.keys())
                # Removing the chosen data from PowerListBoxPC to yAxisPowerS_dictionary:
                delList = []
                for key in yAxisPowerS_dictionary.keys():
                    if key in values['_PowerListBoxPC_']:
                        None # OK, don't do anything.
                    else: # Remove the data from plot and remove it from the yAxisPowerS dictionary.
                        (yAxisPowerS_dictionary[key])[0].remove()
                        delList.append(key)
                        print("The yAxisPowerS_dictionary (Less) is: ", yAxisPowerS_dictionary.keys())
                # deleting the relevant values from the yAxisPowerS_dictionary:
                for val in delList:
                    del yAxisPowerS_dictionary[val]
                plt.legend()
            else:
                plt.title("No Repetition was chosen.")
        elif (event == '_PowerListBoxRC_'):
            if ( checkForParameters(fig, values['_RepetitionListBoxRC_'], values['_PowerListBoxRC_'],graphMode) ):
                # If 'True' Update/Create a new Graph:
                yAxisPowerS_dictionary = changeGraph(df, fig, x, values['_RepetitionListBoxRC_'], values['_PowerListBoxRC_'], "RepetitionSweep", graphMode)
            # IF 'False' - in checkForParameters function.
        elif (event == '_RepetitionListBoxRC_'):
            # check for change in the list and update dictionary.
            if ( checkForParameters(fig, values['_RepetitionListBoxRC_'], values['_PowerListBoxRC_'],graphMode) ):
                # Adding the miss data from PowerListBoxPC to yAxisPowerS_dictionary:
                for key in values['_RepetitionListBoxRC_']:
                    if key in yAxisRepS_dictionary.keys():
                        None # OK, don't do anything.
                    else: # Plot the data and add to the yAxisPowerS dictionary.
                        row = (np.where((df.REP_RATE == key) & (df.POWER == int(values['_PowerListBoxRC_'][0]))))[0]
                        yAxisRepS_dictionary[key] = plt.plot(np.asarray(x, float), list(df.iloc[[row[0]]].values.tolist())[0][10:], label=key)
                        plt.xticks(np.arange(start_f, stop_f, (start_f-stop_f)/10))
                        window2['section_graphMode'].update()
                        print("The yAxisRepS_dictionary (Adding) is: ", yAxisRepS_dictionary.keys())
                # Removing the chosen data from PowerListBoxPC to yAxisPowerS_dictionary:
                delList = []
                for key in yAxisRepS_dictionary.keys():
                    if key in values['_RepetitionListBoxRC_']:
                        None # OK, don't do anything.
                    else: # Remove the data from plot and remove it from the yAxisPowerS dictionary.
                        (yAxisRepS_dictionary[key])[0].remove()
                        delList.append(key)
                        print("The yAxisRepS_dictionary (Less) is: ", yAxisRepS_dictionary.keys())
                # deleting the relevant values from the yAxisPowerS_dictionary:
                for val in delList:
                    del yAxisRepS_dictionary[val]
                plt.legend()
            else:
                plt.title("No Power was chosen.")
        elif (event == 'Save Image'):
            fig.savefig(csvFile+values['imageName']+'.png', dpi=200)
        elif (event == 'cleanCheckBox'):
            if (clean == True):
                if (values['cleanCheckBox'] == True):
                    values['substanceCheckBox'] = False
                    window2['substanceCheckBox'].update(False)
                    values['normCheckBox'] = False
                    window2['normCheckBox'].update(False)
                    window2['section_normValue'].update(False)
                    df = df_clean
                    graphMode = "clean"
                    x, yAxisPowerS_dictionary, yAxisRepS_dictionary, window2 = updateDataframe(df,fig,graphMode,window2)
                    graphStatusText = "Mode: Clean.csv graph"
                    window2.Element('section_graphMode').update(visible=True)
                else:
                    setTitels(fig,"")
                    window2 = resetBoxs(window2)
            else:
                values['cleanCheckBox'] = False
                window2['cleanCheckBox'].update(False)
                graphStatusText = "No clean.csv file was found."
                window2['section_graphMode'].update()
        elif (event == 'substanceCheckBox'):
            if (substance == True):
                if (values['substanceCheckBox'] == True):
                    values['cleanCheckBox'] = False
                    window2['cleanCheckBox'].update(False)
                    values['normCheckBox'] = False
                    window2['normCheckBox'].update(False)
                    window2['section_normValue'].update(False)
                    df = df_substance
                    graphMode = "substance"
                    x, yAxisPowerS_dictionary, yAxisRepS_dictionary, window2 = updateDataframe(df,fig,graphMode,window2)
                    graphStatusText = "Mode: Substance.csv graph"
                    window2['section_graphMode'].update()
                else:
                    setTitels(fig,"")
                    window2 = resetBoxs(window2)
            else:
                values['substanceCheckBox'] = False
                window2['substanceCheckBox'].update(False)
                graphStatusText = "No substance.csv file was found."
                window2['section_graphMode'].update()
        elif (event == 'normCheckBox'):
            if (norm == True):
                if (values['normCheckBox'] == True):
                    window2['section_normValue'].update(True)
                    normValue = "Frequency to normal are between"+list(df_clean.columns.values.tolist())[10]+" nm to "+list(df_clean.columns.values.tolist())[-1]+" nm."
                    window2['section_normValue'].update()
                else:
                    setTitels(fig,"")
                    window2 = resetBoxs(window2)
            if (norm == False):
                values['normCheckBox'] = False
                window2['normCheckBox'].update(False)
                graphStatusText = "No norm.csv file was found."
                window2['section_graphMode'].update()
        elif (event == 'OK'):
                try:
                    getNormlizedByCustomFreq(csvFile, values["normValue"])
                    df_norm = pd.read_csv(csvFile + 'norm.csv')
                    df = df_norm
                    graphMode = "norm"
                    x, yAxisPowerS_dictionary, yAxisRepS_dictionary, window2 = updateDataframe(df,fig,graphMode,window2)
                    graphStatusText = "Mode: Normal.csv graph"
                    window2['section_graphMode'].update()
                    normValue = "Normelaized frequency: " + normValue + "MHz."
                    window2['section_normValue'].update()
                    values['cleanCheckBox'] = False
                    values['substanceCheckBox'] = False
                    window2['cleanCheckBox'].Update(False)
                    window2['substanceCheckBox'].Update(False)
                except:
                    graphMode = ""
                    values['normCheckBox'] = False
                    window2.Element('normCheckBox').update(False)
                    graphStatusText = "Problem loading norm.CSV file"
                    window2['section_normValue'].update(False)

####################################################

if __name__ == '__main__':
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Plot graphs')

    # Add arguments
    parser.add_argument('--csv_name', type=str)

    # Parse the arguments
    args = parser.parse_args()

    if args.csv_name == None:
        args.csv_name = "C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements-1\\Results\\2023_04_02_16_50_53_859012_allan\\"
    interactiveGraph(args.csv_name)
