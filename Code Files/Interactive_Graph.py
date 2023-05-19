# Interactive Graph GUI:
import pandas as pd
import PySimpleGUI as sg
import time
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
import matplotlib.colors as mcolors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from Analyzer import getNormlizedByCustomFreq, getAnalyzerTransmition, beerLambert, allandevation
from datetime import datetime

# Parameters:
#SIZE = (WIDTH,LENTH):
MEKADEM = 1 # The Ratio of all.
WINDOW_SIZE = (int(1920*MEKADEM),int(1080*MEKADEM)) # The all window size.
FRAME_SIZE = (0.77*WINDOW_SIZE[0],0.7*WINDOW_SIZE[1]) # The white box of the frame.
SETTING_AREA_SIZE = (0.18*WINDOW_SIZE[0],0.55*WINDOW_SIZE[1]) # All the data in the frame.
GRAPH_SIZE_AREA = (0.8*WINDOW_SIZE[0], 0.8*WINDOW_SIZE[1]) # The area of the ploted graph.
PLOT_SIZE = (0.95/130*GRAPH_SIZE_AREA[0],0.95/135*GRAPH_SIZE_AREA[1]) # The plot area for the fig part (matplotlib).
SUBSTANCE_DATABASE_SIZE = (int(WINDOW_SIZE[0]/64),int(WINDOW_SIZE[0]/384)) # The part of the substance window.

#-------------------------------------------------------------------------------------------------

# This is for the Toolbar in the Interactive Window:
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

#-------------------------------------------------------------------------------------------------

# Layouts:

# Allowing to show and not show the layout or the section according to events while running:
def collapse(layout, key, visible):
    # Hide or show the relevants fields.
    return sg.pin(sg.Column(layout, key=key, visible=visible))

# The first layout:
def getSweepLayout(frequencyList, powerList, norm_freq_list):
    # xAxis is a list of lists. Inputs must not be empty!
    sweepCompareSection = [[sg.Push(), sg.Text("Select Repetition:"), sg.Text("Select Powers:"), sg.Push()],
                          [sg.Push(), sg.Listbox(values=frequencyList, s=(14,10), enable_events=True, select_mode='multiple', key='_RepetitionListBoxSweepG_'),sg.Listbox(powerList, size=(14,10), enable_events=True, bind_return_key=True, select_mode='multiple', key='_PowerListBoxSweepG_'), sg.Push()]]
    normValue = [[sg.Push(), sg.Checkbox("", key='-Reg_Norm_Val-'), sg.Text("Normlize results by "), sg.Input(str(norm_freq_list[0]),s=7,key="normValue"), sg.Text("[nm]"), sg.Button("Refresh", key="-Refresh-", enable_events=True), sg.Push()]]
    menu_layout = [[collapse(normValue, 'section_normValue', True)],
                  [sg.Push(), sg.Checkbox("Minus Dark", default=True, enable_events=True, key="-MINUS_DARK-"), sg.Checkbox("Logarithmic Scale", default=True, enable_events=True, key="-REG_LOG_SCALE-"), sg.Push()],
                  [sg.Push(), sg.Text("Dark Status:"), sg.Text("", key='darkStatus'), sg.Push()],
                  [sg.Push(),sg.Checkbox(text="Transition\ngraph",font='David 11',key="normCheckBox", enable_events=True, default=True), sg.Checkbox(text="Clean\nsample",font='David 11',key="cleanCheckBox",enable_events=True, default=False), sg.Checkbox(text="Substance\nsample",font='David 11',key="substanceCheckBox", enable_events=True, default=False), sg.Push()],
                  [sg.Push(), collapse(sweepCompareSection, 'section_sweepCompare', True), sg.Push()],
                  [sg.Push(), sg.Button("Clear All", key='-CLEAR_SWEEP_PLOT-', enable_events=True),
                  sg.Button("Close", key='Close Graph', enable_events=True),sg.Push()]]
    graph_layout = [
        #[sg.T('Controls:')],
        [sg.Canvas(key='controls_cv1')],
        #[sg.T('Figure:')],
        [sg.Column(layout=[[sg.Canvas(key='figCanvas1',
                        # it's important that you set this size
                        size=(400 * 2, 400))]], background_color='#DAE0E6', pad=(0, 0))]]
    Layout = [[sg.Push(), sg.Text("Sweep Graph - Comparation (Power-Repetition)", font=("David", 30, "bold")),sg.Push()], [sg.Text("")], [sg.Push(), sg.Column(menu_layout, s=SETTING_AREA_SIZE), sg.Column(graph_layout, s=GRAPH_SIZE_AREA), sg.Push()]]
    return Layout

# The seconcd layout:
def getAllanDeviationLayout(frequencyList, powerList, norm_freq_list):
    # xAxis is a list of lists. Inputs must not be empty!
    database_Layout = [[sg.Text("Select data file")],
                [sg.Listbox(getDatabases(), select_mode='LISTBOX_SELECT_MODE_SINGLE', key="_DATA_FILE_", enable_events = True, size=SUBSTANCE_DATABASE_SIZE)]]
    
    sweepCompareSection = [[sg.Push(), sg.Text("Select Repetition:"), sg.Text("Select Power:"), sg.Push()],
                          [sg.Push(), sg.Listbox(values=frequencyList, s=(14,5), enable_events=True, select_mode='single', key='_RepetitionListBoxAllanDG_'),sg.Listbox(powerList, size=(14,5), enable_events=True, bind_return_key=True, select_mode='single', key='_PowerListBoxAllanDG_'), sg.Push()]]
    normValue = [[sg.Push(), sg.Checkbox("", key='-Reg_Norm_Val-', enable_events=True), sg.Text("Normlize results by "), sg.Input(str(norm_freq_list[0]),s=7,key="normValue",enable_events=True), sg.Text("[nm]"), sg.Push()]]
    absorbance_layout = [[sg.Text("Select wavelength to calculate concentration:")],[sg.Push(), sg.Input(str(norm_freq_list[0]),s=7,key="_ABS_NM_",enable_events=True), sg.Text("[nm]"), sg.Push()]]
    menu_layout = [[collapse(normValue, 'section_normValue', True)],[sg.Checkbox("Minus Dark", default=True, enable_events=True, key="-MINUSDARK-"), sg.Text("", key="darkStatusText")],
                  [sg.Push(), collapse(database_Layout, 'section_dataBaseValue', True), sg.Push()],
                  [collapse(absorbance_layout, 'section_AbsValue', False)],
                  [sg.Push(), collapse(sweepCompareSection, 'section_sweepCompare', True), sg.Push()],
                  [sg.Push(), sg.Text("Waveguide length"), sg.Input("", s=7, key='_WAVEGUIDE_LENGTH_', enable_events=True), sg.Text("mm"), sg.Push()],
                  [sg.Push(), sg.Text("Gama Value"), sg.Input("1", s=7, key='_GAMA_', enable_events=True), sg.Push()],
                  [sg.Push(), sg.Button("Add", key='_ADD_GRAPH_', enable_events=True), sg.Button("Hold", key='_HOLD_', enable_events=True), sg.Push()],
                  [sg.Push(), sg.Button("Save to csv file", key='_CSV_', enable_events=True), sg.Input("csv file name", s=15, key='csvFileName'), sg.Push()],
                  [sg.Push(), sg.Button("Clear All", key='-CLEAR_ALLAN_PLOT-', enable_events=True), sg.Button("Close", key='Close Graph', enable_events=True),sg.Push()],[sg.Push(), sg.Text("", key='timeIntervalText') ,sg.Push()],
                  [sg.Push(), sg.Text("ppm", font='David 10'), sg.Slider(range=(0,1), orientation='h', key='-SLIDER-', resolution=1, size=(6,15), default_value = 0, enable_events=True), sg.Text("%", font='David 10'), sg.Push()]]
                  #[sg.Push(), sg.Button("ppm", key='_ppm_', enable_events=True), sg.Button("%", key='_Precents_', enable_events=True), sg.Push()]]
    graph_layout = [
        #[sg.T('Controls:')],
        [sg.Canvas(key='controls_cv2')],
        #[sg.T('Figure:')],
        [sg.Column(layout=[[sg.Canvas(key='figCanvas2',
                        # it's important that you set this size
                        size=(400 * 2, 200))]], background_color='#DAE0E6', pad=(0, 0))]]
    Layout = [[sg.Push(), sg.Text("Allan Deviation & Concentration Graphs", font=("David", 30, "bold")),sg.Push()], [sg.Text("")], [sg.Push(), sg.Column(menu_layout, s=SETTING_AREA_SIZE), sg.Column(graph_layout, s=GRAPH_SIZE_AREA), sg.Push()]]
    return Layout

# The third layout:
def getAllanSweepTimeLayout(frequencyList, powerList, interval_list):
    # xAxis is a list of lists.
    menu_layout = [[sg.Text("Select graph type:")],
                   [sg.Combo(["Raw Data","Ratio Data"], default_value="Ratio Data", key='-ALLAN_GRAPH_TYPE-', enable_events=True)],
                   [sg.Text("Select Rep and Power pair:")],
                   [sg.Listbox(values=frequencyList, s=(14,10), enable_events=True, select_mode='single', key='-ALLAN_REP-'),
                    sg.Listbox(values=powerList, s=(14,10), enable_events=True, select_mode='single', key='-ALLAN_POWER-')],
                   [sg.Button("Close", key='Close Graph')]
                   
                   ]
    graph_layout = [
        #[sg.T('Controls:')],
        [sg.Canvas(key='controls_cv3')],
        #[sg.T('Figure:')],
        [sg.Column(
            layout=[
                [sg.Canvas(key='figCanvas3',
                        # it's important that you set this size
                        size=(400 * 2, 400)
                        )]
            ],
            background_color='#DAE0E6',
            pad=(0, 0)
        )],
        [sg.Text('Graphs Interval')],
        [sg.Slider(range=(min(interval_list), max(interval_list)), size=(60, 10),
                orientation='h', key='-SLIDER-', resolution=1/(10*len(interval_list)))],
        [sg.Button("Hold", key="-HOLD_TRACE-"), sg.Button("Clear All", key="-ALLAN_CLEAR-"), sg.Button("Play/Pause", key="-ALLAN_PLAY-"), sg.Push()]
        ]
    Layout = [[sg.Push(), sg.Text("Allan Sweep Time Graph", font=("David", 30, "bold")),sg.Push()], [sg.Text("")], [sg.Push(), sg.Column(menu_layout, s=SETTING_AREA_SIZE), sg.Column(graph_layout, s=GRAPH_SIZE_AREA), sg.Push()]]
    return Layout

# End of Layouts.

#---------------------------------------------------------------------------------------------------------------------------

# Additional functions:

def getTime():
    time = str(datetime.today())
    time = time.replace('-', '_')
    time = time.replace(' ', '_')
    time = time.replace(':', '_')
    time = time.replace('.', '_')
    return time

def setTitles(ax, scale):
    ax.clear()                     
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel(scale)

def updateRegualrGraph(df_to_plot, ax, fig_agg):
    ax.cla()
    ax.grid()
    for i in range(len(df_to_plot)):
        try:
            line1 = ax.plot(np.asarray(df_to_plot.columns[10:], float), df_to_plot.iloc[i,10:], label='{}_Power_{}%'.format(df_to_plot['REP_RATE'].iloc[i], df_to_plot['POWER'].iloc[i]))
            # Add a legend
        except:
            return False
    ax.legend(loc='upper right')
    fig_agg.draw()
    return True

def add_saved_lines(lines, ax, fig_agg):
    ax.cla()
    ax.grid()
    for line in lines:
        try:
            ax.plot(line)
            # Add a legend
        except:
            return False
    ax.legend(loc='upper right')
    fig_agg.draw()
    return True

def getDatabases():
    try:
        filenames = os.listdir("..\\Databases")
    except:
        os.mkdir("..\\Databases")
        filenames = os.listdir("..\\Databases")
    filenames.sort()
    filenames = [name[:-4] for name in filenames]
    return filenames

def get_maximum(data_file):
    with open("..\\Databases\\"+data_file, mode='r') as data:
        data = data.readlines()
    if len(data) == 0:
        return False
    maximum_A = float(data[0].split('\t')[1][:-1])
    maximum_WN = float(data[0].split('\t')[0])
    for line in data:
        A = float(line.split('\t')[1][:-1])
        WN = float(line.split('\t')[0])
        if A > maximum_A:
            maximum_A = A
            maximum_WN = WN
    return str(10000000/maximum_WN) # Convertion to [nm]

def saveAllanPlots(holdAllanDeviationList, new_allandeviation_line, csvFileName, dirname):
    holdAllanDeviationList[new_allandeviation_line._label] = new_allandeviation_line
    # label = 'p{}_rr{}_c{}_wl{:.2f}'.format(values['_PowerListBoxPC_'][0], values['_RepetitionListBoxPC_'][0], values['_DATA_FILE_'][0], float(realWavelength))
    # Save deviation csv
    new_df = pd.DataFrame(columns=['Rep Rate', 'Power', 'Database file name', 'conentration wavelength [nm]', 'Waveguide Length [mm]', 'Averaging time [s]', 'Value'])
    for line in holdAllanDeviationList.values():
        temp_df = pd.DataFrame(columns=['Rep Rate', 'Power', 'Database file name', 'conentration wavelength [nm]', 'Waveguide Length [mm]', 'Averaging time [s]', 'Value'])
        label = line._label.split('_')
        rr = label[1][2:]
        p = label[0][1:]
        c = label[2][1:]
        wl = label[3][2:]
        wgl = label[4][3:]
        temp_df['Averaging time [s]'] = line.get_xdata()
        temp_df['Value'] = line.get_ydata()
        temp_df['Rep Rate'] = rr
        temp_df['Power'] = p
        temp_df['Waveguide Length [mm]'] = wgl
        temp_df['Database file name'] = c
        temp_df['conentration wavelength [nm]'] = wl
        new_df = pd.concat([new_df.loc[:],temp_df]).reset_index(drop=True)
    new_df.to_csv(dirname+getTime()+'_'+csvFileName+'.csv', index=False)

# End of additional functions.

#---------------------------------------------------------------------------------------------------------------------------

# This is the main function of the interactive graph:
def interactiveGraph(csvFile):
    
    # Functions and setting:

    # sg.theme('DarkBlue')
    sg.theme('DarkGrey2')
    
    # The sweep graph functions part:
        #None
    
    # The sweep graph functions part:
    
    def clear_plots(ax1,ax2,plotType):
        ax1.cla()
        ax2.cla()
        ax1.set_xlabel("Time [s]")
        ax2.set_xlabel("Averaging time [s]")
        if plotType == 0:
            ax1.set_title("Concentration [ppm]")
        else:
            ax1.set_title("Concentration [%]")
        ax2.set_title("Allan Deviation")
        ax1.grid()
        ax2.grid(markevery=1)

    def add_allanDeviation_history(ax_conc, ax_deviation, hold_lines_conc, hold_lines_dev, fig_agg):
        for line1 in hold_lines_conc.values():
            ax_conc.add_line(line1)
        ax_conc.legend(loc='upper right')
        for line1 in hold_lines_dev.values():
            ax_deviation.add_line(line1)
        ax_deviation.legend(loc='upper right')
        fig_agg.draw()

    # The Allan sweep time functions part:
    
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

    def add_allanTime_history(ax, hold_lines, fig_agg):
        for line1 in hold_lines.values():
            ax.add_line(line1)
        ax.legend(loc='upper right')
        fig_agg.draw()

# End of functions and setting.


# Start of parmeters:
    reread = True # If no major change selected, reread stays false
    new_concentration_line = None
    new_allandeviation_line = None
    realWavelength = None
    df_concentration = None
    lastNormValue = None
    holdConcentrationList = {}
    holdAllanDeviationList = {}
    hold_lines = {}
    interval_list = None
    sweepGraph = None
    allan_and_concentration = None
    allan_time_analyze = None
    flag_allan = True
    flag_allanTime = True
    mode = "Sweep Graph"

    #
    colors_allanDeviationConcentration = [name for name, hex in mcolors.CSS4_COLORS.items()
                   if np.mean(mcolors.hex2color(hex)) < 0.7]
    colors_allanDeviationConcentration.pop(0)
    color = colors_allanDeviationConcentration[0]
    #
    colors_timeGraph = [name for name, hex in mcolors.CSS4_COLORS.items()
                   if np.mean(mcolors.hex2color(hex)) < 0.7]
    colors_timeGraph.pop(0)
    color = colors_timeGraph[0]
    #

    scales_dict = {"LOG": {"CLEAN": "[dBm]", "SUBSTANCE": "[dBm]", "RATIO": "[dB]"}, "WATT":{"CLEAN": "[mW]", "SUBSTANCE": "[mW]", "RATIO": "Ratio"}}
    #----------------------------------------------------------------------------------------
    
    clean = True
    substance = True
    try:
        df_clean = pd.read_csv(csvFile + 'clean.csv')
    except:
        clean = False
    try:
        df_substance = pd.read_csv(csvFile + 'substance.csv')
    except:
        substance = False
    if (not (clean and substance)):
        sg.popup_ok("There was a problem reading the files.")
        exit()

    df_ratio, df_clean, df_substance, darkStatus = getNormlizedByCustomFreq(csvFile, True)
    frequencyList = df_ratio['REP_RATE'].unique().tolist()
    powerList = df_ratio['POWER'].unique().tolist()
    norm_freq_list = np.asarray(df_ratio.columns[10:].tolist(), float)
    df_plotted_full = df_ratio

    # Creating & Loading the transmition file
    # Animation while loading the database to GUI
    animation = time.time()
    future = None
    sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
    while True:
        if (time.time() - animation > 0.05):
            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
            animation = time.time()
        if future == None:
            future = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(getAnalyzerTransmition, [csvFile, False, '1550', True])
        if ( future._state != 'RUNNING' ):
            darkStatus = (future.result())[1]
            sg.PopupAnimated(None)
            future = None
            break
    try:
        df_transmittance = pd.read_csv(csvFile + 'transmittance.csv')
    except:
        sg.popup_ok("There was a problem reading the files.")
        exit()
    try:
        allan_df = pd.read_csv(csvFile + 'allan_ratio.csv')
    except:
        print("Coudln't read "+csvFile + 'allan_ratio.csv')
        sg.popup_ok("Coudln't read "+csvFile + 'allan_ratio.csv')
        flag_allanTime = False

    # This is the main Layout - connect all the previous layouts:
    menu = [['Click here Reset', ['Are you sure? (Yes, Reset)']]]
    sweepGraph = getSweepLayout(frequencyList, powerList, norm_freq_list)
    
    if flag_allan:
        allan_and_concentration = getAllanDeviationLayout(frequencyList, powerList, norm_freq_list) 
    else:
        allan_and_concentration = [
            [sg.Push(), sg.Text("Allan Deviation & Concentration Graphs", font=("David", 20, "bold")),sg.Push()],
            [sg.Push(), sg.Text('There was a problem to read the correct file!'), sg.Push()]
            ]

    if flag_allanTime:
        interval_list = allan_df['Interval'].unique().tolist()
        allan_time_analyze = getAllanSweepTimeLayout(frequencyList, powerList, interval_list)
    else:
        allan_time_analyze = [
            [sg.Push(), sg.Text("Allan Sweep Time Graph", font=("David", 20, "bold")),sg.Push()],
            [sg.Push(), sg.Text('There was a problem to read the correct file!'), sg.Push()]
            ]
    
    layout = [
    [sg.Frame("Sweep Graph", sweepGraph, visible=True, key='section_sweepGraph', size=(FRAME_SIZE[0], FRAME_SIZE[1]))],
    [sg.Frame("Allan Deviation & Concentration", allan_and_concentration, visible=True, key='section_Allan_Concentration', size=(FRAME_SIZE[0], FRAME_SIZE[1]))],
    [sg.Frame("Allan Time Swep", allan_time_analyze, visible=True, key='section_TimeAnalyze', size=(FRAME_SIZE[0], FRAME_SIZE[1]))]]
    
    main_Layout = [
    [sg.Menu(menu, key='MENU', font='22')],
    [sg.Push(), sg.Text('Results of: '+csvFile, justification='center', background_color='#424f5e', expand_x=False, font=("David", 15, "bold")), sg.Push()],
    [sg.Column(layout, scrollable=True, vertical_scroll_only=True, key='COLUMN')]]
    
    window = sg.Window("Interactive Graph", main_Layout, size=(WINDOW_SIZE[0], WINDOW_SIZE[1]), finalize=True)
    #window = sg.Window("Interactive Graph", main_Layout, size=(3860, 2160), finalize=True)
    #window = sg.Window("Interactive Graph", main_Layout, size=(WINDOW_SIZE[0], WINDOW_SIZE[1]))
    

    # Parameters for the functions:
    fig = None
    fig1 = None
    fig2 = None
    fig3 = None
    fig_agg1 = None
    fig_agg2 = None
    fig_agg3 = None
    scales = None
    scale = None
    hold_lines = None
    slider_elem = None
    slider_update = None
    test_selected = None
    i = None
    ax = None
    ax_conc = None
    ax_deviation =None
    # End of Parameters for the functions.

    # Sweep Graph - Start:
    def drawSweepGraph(fig1, ax, fig_agg1,scales,scale):
        # Creating the automatic first graph:
        plt.ioff()
        fig1 = plt.figure()
        plt.ion() 
        fig1.set_figwidth(PLOT_SIZE[0])
        fig1.set_figheight(PLOT_SIZE[1])
        ax = fig1.add_subplot(111)
        ax.set_xlabel("Wavelength [nm]")
        ax.grid()
        fig_agg1 = draw_figure_w_toolbar(window['figCanvas1'].TKCanvas, fig1, window['controls_cv1'].TKCanvas)
        plt.title('No Plot to show. Choose data...')
        scales = scales_dict["LOG"]
        scale = "[dB]"
        if darkStatus:
            window['darkStatus'].update("OK")
        else:
            window['darkStatus'].update("'dark.csv' not Found")
        return fig1, ax, fig_agg1,scales,scale
    # Sweep Graph - End.

    # Allan Deviation - Start:
    def drawAllanDeviationGraph(fig2, ax_conc, ax_deviation, fig_agg2):
        # Creating the automatic first graph:
        plt.ioff()
        fig2 = plt.figure()
        plt.ion()
        fig2.set_figwidth(PLOT_SIZE[0])
        fig2.set_figheight(PLOT_SIZE[1])
        ax_deviation = fig2.add_subplot(211)
        ax_deviation.set_title("Allan Deviation")
        ax_deviation.grid(markevery=1)
        ax_conc = fig2.add_subplot(212)
        ax_conc.set_xlabel("Time [s]")
        ax_deviation.set_xlabel("Averaging time [s]")
        ax_conc.set_title("Concentration [ppm]")
        ax_conc.grid()
        fig_agg2 = draw_figure_w_toolbar(window['figCanvas2'].TKCanvas, fig2, window['controls_cv2'].TKCanvas)
        fig2.tight_layout(pad=5.0)
        return fig2, ax_conc, ax_deviation, fig_agg2
        # End of creating the graph.
    # Allan Deviation - End.

    # Allan Time - start:
    def drawAllanSweepTime(fig3, ax, fig_agg3, hold_lines,slider_elem,slider_update,test_selected,i):
        # draw the initial plot in the window
        plt.ioff()
        fig3 = plt.Figure()
        plt.ion()
        fig3.set_figwidth(PLOT_SIZE[0])
        fig3.set_figheight(PLOT_SIZE[1]-2)
        ax = fig3.add_subplot(111)
        ax.set_xlabel("Wavelength [nm]")
        ax.set_ylabel("Power(0)/Power(t)")
        ax.grid()
        fig_agg3 = draw_figure_w_toolbar(window['figCanvas3'].TKCanvas, fig3, window['controls_cv3'].TKCanvas)
        hold_lines = {}
        slider_elem = window['-SLIDER-']
        window['-SLIDER-'].bind('<ButtonRelease-1>', ' Release')
        slider_update = False
        test_selected = False
        i = 0
        return fig3, ax, fig_agg3, hold_lines,slider_elem,slider_update,test_selected,i
    # Allan Time - End.

    # First Start:
    fig1, ax, fig_agg1,scales,scale = drawSweepGraph(fig1, ax, fig_agg1,scales,scale)
    if flag_allan:
        fig2, ax_conc, ax_deviation, fig_agg2 = drawAllanDeviationGraph(fig2, ax_conc, ax_deviation, fig_agg2)
    if flag_allanTime:
        fig3, ax, fig_agg3, hold_lines,slider_elem,slider_update,test_selected,i = drawAllanSweepTime(fig3, ax, fig_agg3, hold_lines,slider_elem,slider_update,test_selected,i)

    # Start checking the events:
    while True:

        event, values = window.read()

        # Closing the graph.
        if ( (event == 'Close Graph') or (event == sg.WIN_CLOSED) ):
            window.close()
            break

        # Reset all and clear all:
        elif event == 'Are you sure? (Yes, Reset)':
            window['_PowerListBoxSweepG_'].update(set_to_index=[])
            window['_RepetitionListBoxSweepG_'].update(set_to_index=[])
            ax.cla()
            if flag_allan:
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=True)
                window['_PowerListBoxAllanDG_'].update(set_to_index=[])
                window['_RepetitionListBoxAllanDG_'].update(set_to_index=[])
                clear_plots(ax_conc, ax_deviation, values['-SLIDER-'])
                new_concentration_line = None
                new_allandeviation_line = None
                holdConcentrationList = {}
                holdAllanDeviationList = {}
                colors_allanDeviationConcentration = [name for name, hex in mcolors.CSS4_COLORS.items()
                    if np.mean(mcolors.hex2color(hex)) < 0.7]
                colors_allanDeviationConcentration.pop(0)
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=False)
            if flag_allanTime:
                ax.cla()
                ax.grid()
                fig_agg3.draw()
                hold_lines = {} # deleting history
                colors_timeGraph = [name for name, hex in mcolors.CSS4_COLORS.items()
                    if np.mean(mcolors.hex2color(hex)) < 0.7]
                colors_timeGraph.pop(0)
            #
            fig1, ax, fig_agg1,scales,scale = drawSweepGraph(fig1, ax, fig_agg1,scales,scale)
            if flag_allan:
                fig2, ax_conc, ax_deviation, fig_agg2 = drawAllanDeviationGraph(fig2, ax_conc, ax_deviation, fig_agg2)
            if flag_allanTime:
                fig3, ax, fig_agg3, hold_lines,slider_elem,slider_update,test_selected,i = drawAllanSweepTime(fig3, ax, fig_agg3, hold_lines,slider_elem,slider_update,test_selected,i)
        # End of Reset.

    # This part is for the sweep graph:
            
        # Clear the graph and the relevant parametrs.
        if event == '-CLEAR_SWEEP_PLOT-':
            window['_PowerListBoxSweepG_'].update(set_to_index=[])
            window['_RepetitionListBoxSweepG_'].update(set_to_index=[])
            ax.cla()

        elif ( (event == '-Refresh-') or (event == '-MINUS_DARK-') ):
            window3 = sg.Window("Processing...", [[sg.Text("Renormalzing results, please wait...")]], finalize=True)
            df_ratio, df_clean, df_substance, darkStatus = getNormlizedByCustomFreq(csvFile, values['-MINUS_DARK-'], values["normValue"], to_norm=values['-Reg_Norm_Val-'])
            if values['cleanCheckBox']:
                df_plotted_full = df_clean
            elif values['substanceCheckBox']:
                df_plotted_full = df_substance
            elif values['normCheckBox']:
                df_plotted_full = df_ratio
            else:
                window3.close()
                continue
            df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
            if len(df_plotted) < 0:
                window3.close()
                continue
            updateRegualrGraph(df_plotted, ax, fig_agg1)
            window3.close()
            if values['-MINUS_DARK-'] and darkStatus:
                window['darkStatus'].update("OK")
            elif values['-MINUS_DARK-'] and (darkStatus == False):
                window['darkStatus'].update("'dark.csv' not Found")
            elif values['-MINUS_DARK-']==False and (darkStatus == False):
                window['darkStatus'].update("Calculation ignoring dark measurment")
            elif values['-MINUS_DARK-']==False and (darkStatus == True):
                window['darkStatus'].update("No way! No sense")
        
        elif (event == '_RepetitionListBoxSweepG_') or (event == '_PowerListBoxSweepG_'):
            df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
            if len(df_plotted) < 0:
                continue
            updateRegualrGraph(df_plotted, ax, fig_agg1)
        
        elif (event == '-REG_LOG_SCALE-'):
            window3 = sg.Window("Processing...", [[sg.Text("Changing graph scale, please wait...")]], finalize=True)
            if values['-REG_LOG_SCALE-']:
                scales = scales_dict["LOG"]
                if scale == '[mW]':
                    scale = '[dBm]'
                    df_plotted.iloc[:,10:] = df_plotted.iloc[:,10:].apply(lambda val : 10*np.log10(val/(10**(-3))))
                    df_clean.iloc[:,10:] = df_clean.iloc[:,10:].apply(lambda val : 10*np.log10(val/(10**(-3))))
                    df_substance.iloc[:,10:] = df_substance.iloc[:,10:].apply(lambda val : 10*np.log10(val/(10**(-3))))
                    df_ratio.iloc[:,10:] = df_ratio.iloc[:,10:].apply(lambda val : 10*np.log10(val/(10**(-3))))
                    df_plotted_full.iloc[:,10:] = df_plotted_full.iloc[:,10:].apply(lambda val : 10*np.log10(val/(10**(-3))))
                else:
                    scale = '[dB]'
                    df_plotted.iloc[:,10:] = df_plotted.iloc[:,10:].apply(lambda val : 10*np.log10(val))
                    df_clean.iloc[:,10:] = df_clean.iloc[:,10:].apply(lambda val : 10*np.log10(val))
                    df_substance.iloc[:,10:] = df_substance.iloc[:,10:].apply(lambda val : 10*np.log10(val))
                    df_ratio.iloc[:,10:] = df_ratio.iloc[:,10:].apply(lambda val : 10*np.log10(val))
                    df_plotted_full.iloc[:,10:] = df_plotted_full.iloc[:,10:].apply(lambda val : 10*np.log10(val))
            else:
                scales = scales_dict["WATT"]
                if scale == '[dB]':
                    scale = 'Ratio'
                    df_plotted.iloc[:,10:] = df_plotted.iloc[:,10:].apply(lambda val : 10**(val/10))
                    df_clean.iloc[:,10:] = df_clean.iloc[:,10:].apply(lambda val : 10**(val/10))
                    df_substance.iloc[:,10:] = df_substance.iloc[:,10:].apply(lambda val : 10**(val/10))
                    df_ratio.iloc[:,10:] = df_ratio.iloc[:,10:].apply(lambda val : 10**(val/10))
                    df_plotted_full.iloc[:,10:] = df_plotted_full.iloc[:,10:].apply(lambda val : 10**(val/10))
                else:
                    scale = '[mW]'
                    df_plotted.iloc[:,10:] = df_plotted.iloc[:,10:].apply(lambda val : (10**(-3))*10**(val/10))
                    df_clean.iloc[:,10:] = df_clean.iloc[:,10:].apply(lambda val : (10**(-3))*10**(val/10))
                    df_substance.iloc[:,10:] = df_substance.iloc[:,10:].apply(lambda val : (10**(-3))*10**(val/10))
                    df_ratio.iloc[:,10:] = df_ratio.iloc[:,10:].apply(lambda val : (10**(-3))*10**(val/10))
                    df_plotted_full.iloc[:,10:] = df_plotted_full.iloc[:,10:].apply(lambda val : (10**(-3))*10**(val/10))
            updateRegualrGraph(df_plotted,ax,fig_agg1)
            window3.close()

        elif (event == 'cleanCheckBox'):
            ax.cla()
            ax.grid()
            scale = scales["CLEAN"]
            if (values['cleanCheckBox']):
                df_plotted_full = df_clean
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
                if len(df_plotted) < 0:
                    continue
                updateRegualrGraph(df_plotted, ax, fig_agg1)
                values['substanceCheckBox'] = False
                values['normCheckBox'] = False                                      
                window['substanceCheckBox'].update(False)
                window['normCheckBox'].update(False)
        
        elif (event == 'substanceCheckBox'):
            ax.cla()
            ax.grid()
            scale = scales["SUBSTANCE"]
            if (values['substanceCheckBox']):
                df_plotted_full = df_substance
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
                if len(df_plotted) < 0:
                    continue
                updateRegualrGraph(df_plotted, ax, fig_agg1)
                values['cleanCheckBox'] = False
                values['normCheckBox'] = False
                window['cleanCheckBox'].update(False)                              
                window['normCheckBox'].update(False)
        
        elif (event == 'normCheckBox'):
            ax.cla()
            ax.grid()
            scale = scales["RATIO"]
            if (values['normCheckBox']):
                df_plotted_full = df_ratio
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
                if len(df_plotted) < 0:
                    continue
                updateRegualrGraph(df_plotted, ax, fig_agg1)
                values['cleanCheckBox'] = False                                      
                values['substanceCheckBox'] = False
                window['cleanCheckBox'].update(False)
                window['substanceCheckBox'].update(False)

        # Always execute:
        if values['-Reg_Norm_Val-']:
            if values['-REG_LOG_SCALE-']:
                scale = '[dB]'
            else:
                scale = 'Ratio'
        plt.ylabel(scale)
        plt.xlabel("Wavelength [nm]")
    # End of sweep graph.

    # This part is for allan deviation & concentration part:

        if flag_allan:
        
            # Clear the graph and the relevant parametrs.
            if event == '-CLEAR_ALLAN_PLOT-':
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=True)
                window['_PowerListBoxAllanDG_'].update(set_to_index=[])
                window['_RepetitionListBoxAllanDG_'].update(set_to_index=[])
                clear_plots(ax_conc, ax_deviation, values['-SLIDER-'])
                new_concentration_line = None
                new_allandeviation_line = None
                holdConcentrationList = {}
                holdAllanDeviationList = {}
                colors_allanDeviationConcentration = [name for name, hex in mcolors.CSS4_COLORS.items()
                    if np.mean(mcolors.hex2color(hex)) < 0.7]
                colors_allanDeviationConcentration.pop(0)
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=False)
            
            elif event == '_ADD_GRAPH_':
                if (len(values['_RepetitionListBoxAllanDG_']) > 0) and (len(values['_PowerListBoxAllanDG_']) > 0)  and (len(values['_DATA_FILE_']) > 0) and (values['_WAVEGUIDE_LENGTH_'] != ''):####### to add protection to the length try: float except ->float
                    # All the logic of working Animation is starting:
                    window['_ADD_GRAPH_'].update(disabled=True)
                    window['_HOLD_'].update(disabled=True)
                    window['_CSV_'].update(disabled=True)
                    window['-CLEAR_ALLAN_PLOT-'].update(disabled=True)
                    window['Close Graph'].update(disabled=True)
                    future1 = None
                    future2 = None
                    future3 = None
                    startOperation = True
                    SecondaryOperation = True
                    animation = time.time()
                    start_time = time.time()
                    sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                    while True:
                        if (time.time() - animation > 0.05):
                            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                            animation = time.time()
                        #
                        if reread and startOperation:
                            # get concentration
                            # normalzation of clean and analyzer is required before concentration calculations
                            if ( values['-Reg_Norm_Val-'] == True):
                                if (lastNormValue != values['normValue']):
                                    if future1 == None:
                                        future1 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(getAnalyzerTransmition, [csvFile, values['-Reg_Norm_Val-'], values['normValue'],values['-MINUSDARK-']])
                                    lastNormValue = values['normValue']
                            else:
                                if future1 == None:
                                    future1 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(getAnalyzerTransmition, [csvFile, False, values['normValue'], values['-MINUSDARK-']])
                            startOperation = False
                            SecondaryOperation = False
                        #
                        if ( (SecondaryOperation or future1 != None) and (time.time()-start_time>0.1) ):
                            if ( SecondaryOperation or future1._state != 'RUNNING' ):
                                try:
                                    darkStatus = (future1.result())[1]
                                except:
                                    None
                                # filter selection
                                if future2 == None:
                                    future2 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(beerLambert, [csvFile, "..\\Databases\\"+values['_DATA_FILE_'][0]+'.txt', float(values['_ABS_NM_']), float(values['_WAVEGUIDE_LENGTH_']), values['_GAMA_']])
                                SecondaryOperation = False
                                future1 = None
                        #
                        if ( (future2 != None) and (time.time()-start_time>0.1) ):
                            if (future2._state != 'RUNNING'):
                                future2 = future2.result()
                                df_concentration = future2[0]
                                realWavelength = future2[1]
                                df_plotted = df_concentration[df_concentration['REP_RATE'].isin(values['_RepetitionListBoxAllanDG_']) & df_concentration['POWER'].isin(values['_PowerListBoxAllanDG_'])]
                                label = 'p{}_rr{}_c{}_wl{:.2f}_wgl{:.2f}'.format(values['_PowerListBoxAllanDG_'][0], values['_RepetitionListBoxAllanDG_'][0], values['_DATA_FILE_'][0].replace('_','-'), float(realWavelength), float(values['_WAVEGUIDE_LENGTH_']))
                                if values['-Reg_Norm_Val-'] == True:
                                    label = label + '_norm' + values['normValue']
                                if values['-MINUSDARK-'] and darkStatus == True:
                                    label = label + '_minudark'
                                if future3 == None:
                                    future3 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(allandevation, df_plotted)
                                future2 = None
                        #
                        if ( (future3 != None) and (time.time()-start_time>0.1) ):
                            if ( future3._state != 'RUNNING'):
                                sg.PopupAnimated(None)
                                break
                    future3 = future3.result()
                    tau = future3[0] # Everytime is calculating.
                    adev = future3[1] # Everytime is calculating.
                    mean_interval = future3[2]
                    # End of the logic of working Animation.
                    clear_plots(ax_conc, ax_deviation, values['-SLIDER-'])
                    add_allanDeviation_history(ax_conc,ax_deviation,holdConcentrationList,holdAllanDeviationList,fig_agg2)
                    new_allandeviation_line = ax_deviation.loglog(tau, adev, label=label, color = color)
                    if (values['-SLIDER-'] == 0):
                        new_concentration_line = ax_conc.plot(df_plotted['Interval'], np.asarray(df_plotted['Concentration [ppm]'], float), label=label, color = color)
                    else:
                        new_concentration_line = ax_conc.plot(df_plotted['Interval'], np.asarray(df_plotted['Concentration [%]'], float), label=label, color = color)
                    ax_deviation.grid(which='minor', alpha=0.2, linestyle='--')
                    ax_deviation.grid(which='major', alpha=1, linestyle='-')
                    ax_conc.grid(which='minor', alpha=0.2)
                    ax_conc.grid(which='major', alpha=1)
                    ax_deviation.legend(loc='upper right')
                    ax_conc.legend('', frameon=False)
                    timeIntervalT = "The avarage Time Interval is: "+str("{:.3f}".format(mean_interval))+" seconds."
                    window['timeIntervalText'].update(timeIntervalT)
                    new_concentration_line = new_concentration_line[0]
                    new_allandeviation_line = new_allandeviation_line[0]
                    # Show the two Graphs:
                    fig_agg2.draw()
                    reread = False
                else:
                    sg.popup_ok("Make sure the parameters are chosen correctly")
                window['_ADD_GRAPH_'].update(disabled=False)
                window['_HOLD_'].update(disabled=False)
                window['_CSV_'].update(disabled=False)
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=False)
                window['Close Graph'].update(disabled=False)
                window['-MINUSDARK-'].update(darkStatus)
                if darkStatus:
                    window['darkStatusText'].update("OK")
                else:
                    window['darkStatusText'].update("'dark.csv' not Found")
                        
            elif event == '_HOLD_':
                window['_HOLD_'].update(disabled=True)
                if (new_concentration_line != None) and (new_allandeviation_line != None):
                    if ((new_concentration_line._label in holdConcentrationList) or (new_allandeviation_line._label in holdAllanDeviationList) ):
                        sg.popup_auto_close("The graph already exist in database.", title="Graph Exist", auto_close_duration=2)
                    else:
                        holdConcentrationList[new_concentration_line._label] = new_concentration_line
                        holdAllanDeviationList[new_allandeviation_line._label] = new_allandeviation_line
                        colors_allanDeviationConcentration.remove(color)
                        color = colors_allanDeviationConcentration[0]
                        new_concentration_line = None
                        new_allandeviation_line = None
                        # Site link: https://www.tutorialspoint.com/pysimplegui/pysimplegui_popup_windows.htm
                        sg.popup_auto_close("The selected graph was added.", title="Graph was added", auto_close_duration=1)
                else:
                    sg.popup_auto_close("The selected graph was already added.", title="Already added", auto_close_duration=2)
                window['_HOLD_'].update(disabled=False)

            elif event == '_CSV_':
                window['_CSV_'].update(disabled=True)
                saveAllanPlots(holdAllanDeviationList, new_allandeviation_line, values['csvFileName'], csvFile)
                csvFileWasSaved = '\'' + values['csvFileName'] + '.csv\' file was saved'
                window['csvFileName'].update("csv file name")
                sg.popup_auto_close(csvFileWasSaved, title="CSV File Saved", auto_close_duration=2)
                window['_CSV_'].update(disabled=False)

            elif event == '_DATA_FILE_':
                if len(values['_DATA_FILE_']) > 0:
                    wavelength = get_maximum(values['_DATA_FILE_'][0]+'.txt')
                    window['section_AbsValue'].update(visible=True)
                    window['_ABS_NM_'].update(wavelength)
                else:
                    window['section_AbsValue'].update(visible=False)
                reread = True
            
            elif event == '-Reg_Norm_Val-' or event == 'normValue' or event == '_WAVEGUIDE_LENGTH_' or event == '_ABS_NM_' or event =="-MINUSDARK-":
                reread = True

            elif event == '-SLIDER-':
                #print(values['-SLIDER-'])
                if values['-SLIDER-'] == 0: # ppm mode
                    None
                elif values['-SLIDER-'] == 1: # '%'' mode
                    None
    # End of allan deviation & concentration graph.

    # Allan time stemp:
    
        if flag_allanTime:

            if event == '-ALLAN_PLAY-' and test_selected:
                # Start or stop auto switching
                slider_update = not slider_update
            
            if slider_update and event == '__TIMEOUT__': ########################### Problem
                # Update to next timestamp
                slider_elem.update(i)
                curr_label = '{}_{}_TS_{:.2f}'.format(temp_df['REP_RATE'].iloc[i], temp_df['POWER'].iloc[i], temp_df['Interval'].iloc[i])
                if curr_label not in hold_lines.keys():
                    line1 = update_internal_graph(ax, temp_df, fig_agg3, i, color)
                    add_allanTime_history(ax, hold_lines, fig_agg3)
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
            
            if event == '-SLIDER- Release': ########################### Problem
                interval = interval_list[np.argmin([abs(values['-SLIDER-']-element) for element in interval_list])]
                i = interval
                curr_label = '{}_{}_TS_{:.2f}'.format(temp_df['REP_RATE'].iloc[i], temp_df['POWER'].iloc[i], temp_df['Interval'].iloc[i])
                if curr_label not in hold_lines.keys():
                    line1 = update_internal_graph(ax, temp_df, fig_agg3, i, color)
                    add_allanTime_history(ax, hold_lines, fig_agg3)

            if event == '-HOLD_TRACE-':
                if line1 != False:
                    hold_lines[line1._label] = line1
                    colors_timeGraph.remove(color)
                    color = colors_timeGraph[0]

            if event == '-ALLAN_CLEAR-':
                ax.cla()
                ax.grid()
                fig_agg3.draw()
                hold_lines = {} # deleting history
                colors_timeGraph = [name for name, hex in mcolors.CSS4_COLORS.items()
                    if np.mean(mcolors.hex2color(hex)) < 0.7]
                colors_timeGraph.pop(0)
                
            if event == '-ALLAN_GRAPH_TYPE-':
                # ["Raw Data","Ratio Data"]
                ax.cla()
                ax.grid()
                i = 0
                fig_agg3.draw()
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
                window['-ALLAN_REP-'].update(allan_df['REP_RATE'].unique().tolist())
                window['-ALLAN_POWER-'].update(allan_df['POWER'].unique().tolist())
                test_selected = False
                slider_update = False
                interval_list = allan_df['Interval'].unique().tolist()
    # End of allan time  sweep

# End of main while.

# End of interactiveGraph function.

# End of File.

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------
# For our checking:
if __name__ == '__main__':
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Plot graphs')

    # Add arguments
    parser.add_argument('--csv_name', type=str)
    parser.add_argument('--analyzer_substance', type=bool)

    # Parse the arguments
    args = parser.parse_args()

    if args.csv_name == None:
        dirname='C:\BGUProject\Automation-of-spectral-measurements\Results\\2023_05_04_12_54_02_685629___longer_analyzer_empty__\\'
        #dirname = "..\\Results\\Uzziels_Theoretical_Measurements\\"
        args.csv_name = dirname
        args.analyzer_substance = False
        #"C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\Simulation\\"
        #"C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\Analyzer_Test\\"
        # args.csv_name = "C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\2023_04_19_16_49_58_336962_Real Test\\"
    interactiveGraph(args.csv_name)
    # interactiveGraph(args.csv_name, analyzer_substance=args.analyzer_substance)

