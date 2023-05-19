# Interactive Graph GUI:
import pandas as pd
import PySimpleGUI as sg
import time
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
import tkthread
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.colors as mcolors
from Analyzer import getNormlizedByCustomFreq, getAnalyzerTransmition, beerLambert, allandevation
import argparse
import os
from datetime import datetime

GRAPH_SIZE = (1280,1024)
PLOT_SIZE = (12,7)
ALLAN_DEVIATION_SIZE = (12,7)
DATABASE_SIZE = (30,5)

graphStatusText = "Choose graph type"

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

def getLayout(frequencyList, powerList, norm_freq_list):
    # xAxis is a list of lists.
    # inputs must not be empty!
    sweepCompareSection = [[sg.Push(), sg.Text("Select Repetition:"), sg.Text("Select Powers:"), sg.Push()],
                          [sg.Push(), sg.Listbox(values=frequencyList, s=(14,10), enable_events=True, select_mode='multiple', key='_RepetitionListBoxPC_'),sg.Listbox(powerList, size=(14,10), enable_events=True, bind_return_key=True, select_mode='multiple', key='_PowerListBoxPC_'), sg.Push()]]
    normValue = [[sg.Push(), sg.Checkbox("", key='-Reg_Norm_Val-'), sg.Text("Normlize results by "), sg.Input(str(norm_freq_list[0]),s=7,key="normValue"), sg.Text("[nm]"), sg.Button("Refresh", key="-Refresh-", enable_events=True), sg.Push()]]
    menu_layout = [[collapse(normValue, 'section_normValue', True)],
                  [sg.Push(), sg.Checkbox("Minus Dark", default=True, enable_events=True, key="-MINUS_DARK-"), sg.Checkbox("Logarithmic Scale", default=True, enable_events=True, key="-REG_LOG_SCALE-"), sg.Push()],
                  [sg.Push(), sg.Text("Dark Status:"), sg.Text("", key='darkStatus'), sg.Push()],
                  [sg.Push(),sg.Checkbox(text="Transition\ngraph",font='David 11',key="normCheckBox", enable_events=True, default=True), sg.Checkbox(text="Clean\nsample",font='David 11',key="cleanCheckBox",enable_events=True, default=False), sg.Checkbox(text="Substance\nsample",font='David 11',key="substanceCheckBox", enable_events=True, default=False), sg.Push()],
                  [sg.Push(), collapse(sweepCompareSection, 'section_sweepCompare', True), sg.Push()],
                  [sg.Push(), sg.Button("Clear All", key='-CLEAR_PLOT-', enable_events=True),
                  sg.Button("Close", key='Close Graph', enable_events=True),sg.Push()]]
    graph_layout = [[sg.Push(),sg.Text("Graph Space"),sg.Push()],
        [sg.T('Controls:')], [sg.Canvas(key='controls_cv')], [sg.T('Figure:')],
        [sg.Column(layout=[[sg.Canvas(key='figCanvas',
                        # it's important that you set this size
                        size=(400 * 2, 400))]], background_color='#DAE0E6', pad=(0, 0))]]
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

def getAllanDeviationLayout(frequencyList, powerList, norm_freq_list):
    # xAxis is a list of lists.
    # inputs must not be empty!
    database_Layout = [[sg.Text("Select data file")],
                [sg.Listbox(getDatabases(), select_mode='LISTBOX_SELECT_MODE_SINGLE', key="_DATA_FILE_", enable_events = True, size=DATABASE_SIZE)]]
    
    sweepCompareSection = [[sg.Push(), sg.Text("Select Repetition:"), sg.Text("Select Power:"), sg.Push()],
                          [sg.Push(), sg.Listbox(values=frequencyList, s=(14,5), enable_events=True, select_mode='single', key='_RepetitionListBoxPC_'),sg.Listbox(powerList, size=(14,5), enable_events=True, bind_return_key=True, select_mode='single', key='_PowerListBoxPC_'), sg.Push()]]
    normValue = [[sg.Push(), sg.Checkbox("", key='-Reg_Norm_Val-', enable_events=True), sg.Text("Normlize results by "), sg.Input(str(norm_freq_list[0]),s=7,key="normValue",enable_events=True), sg.Text("[nm]"), sg.Push()]]
    absorbance_layout = [[sg.Text("Select wavelength to calculate concentration:")],[sg.Push(), sg.Input(str(norm_freq_list[0]),s=7,key="_ABS_NM_",enable_events=True), sg.Text("[nm]"), sg.Push()]]
    menu_layout = [[collapse(normValue, 'section_normValue', True)],[sg.Checkbox("Minus Dark", default=True, enable_events=True, key="-MINUSDARK-"), sg.Text("", key="darkStatusText")],
                  [sg.Push(), collapse(database_Layout, 'section_dataBaseValue', True), sg.Push()],
                  [collapse(absorbance_layout, 'section_AbsValue', False)],
                  [sg.Push(), collapse(sweepCompareSection, 'section_sweepCompare', True), sg.Push()],
                  [sg.Push(), sg.Text("Waveguide length"), sg.Input("", s=7, key='_WAVEGUIDE_LENGTH_', enable_events=True), sg.Text("mm"), sg.Push()],
                  [sg.Push(), sg.Text("Gama Value"), sg.Input("1", s=7, key='_GAMA_', enable_events=True), sg.Push()],
                  [sg.Push(), sg.Button("Add", key='_ADD_GRAPH_', enable_events=True), sg.Button("Hold", key='_HOLD_', enable_events=True), sg.Push()],
                  [sg.Push(), sg.Button("Save to csv file", key='_CSV_', enable_events=True), sg.Input("csv file name", s=15, key='csvFileName'), sg.Push()], [sg.Text("")],
                  [sg.Push(), sg.Button("Clear All", key='-CLEAR_PLOT-', enable_events=True), sg.Button("Close", key='Close Graph', enable_events=True),sg.Push()],[sg.Text("")],[sg.Push(), sg.Text("", key='timeIntervalText') ,sg.Push()], [sg.Text("")],
                  [sg.Push(), sg.Text("ppm", font='David 10'), sg.Slider(range=(0,1), orientation='h', key='-SLIDER-', resolution=1, size=(6,15), default_value = 0, enable_events=True), sg.Text("%", font='David 10'), sg.Push()]]
                  #[sg.Push(), sg.Button("ppm", key='_ppm_', enable_events=True), sg.Button("%", key='_Precents_', enable_events=True), sg.Push()]]
    graph_layout = [[sg.Push(),sg.Text("Graph Space"),sg.Push()],
        [sg.T('Controls:')], [sg.Canvas(key='controls_cv')], [sg.T('Figure:')],
        [sg.Column(layout=[[sg.Canvas(key='figCanvas',
                        # it's important that you set this size
                        size=(400 * 2, 200))]], background_color='#DAE0E6', pad=(0, 0))]]
    Layout = [[sg.Column(menu_layout), sg.Column(graph_layout , s=GRAPH_SIZE)]]
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

def get_minimum(data_file):
    with open("..\\Databases\\"+data_file, mode='r') as data:
        data = data.readlines()
    if len(data) == 0:
        return False
    minimum_A = float(data[0].split('\t')[1][:-1])
    minimum_WN = float(data[0].split('\t')[0])
    for line in data:
        A = float(line.split('\t')[1][:-1])
        WN = float(line.split('\t')[0])
        if A < minimum_A:
            minimum_A = A
            minimum_WN = WN
    return str(10000000/minimum_WN) # Convertion to [nm]

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

        



#---------------------------------------------------------------------------------------------------------------------------

# The managment function:

def interactiveGraph(csvFile, analyzer_substance=False):
    #csvFile = val_list[0]
    #analyzer_substance = val_list[1]
    filesList = os.listdir(csvFile)
    filesList = [name[:-4] for name in filesList]
    if 'analyzer' in filesList:
        if analyzer_substance:
            type_of_graph = 'regular'
        else:
            type_of_graph = 'analyzer'
    elif 'substance' in filesList:
        type_of_graph = 'regular'
    else:
        type_of_graph = 'allan'


    if type_of_graph == 'regular':
        regularSweepGraph(csvFile)
    elif type_of_graph == 'allan':
        timeSweepGraph(csvFile)
    elif type_of_graph == 'analyzer':
        analyzerGraph(csvFile)
        #tkthread.call_nosync(analyzerGraph(csvFile))


def analyzerGraph(csvFile):

    colors = [name for name, hex in mcolors.CSS4_COLORS.items()
                   if np.mean(mcolors.hex2color(hex)) < 0.7]
    colors.pop(0)
    color = colors[0]

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

    def add_allan_history(ax_conc, ax_deviation, hold_lines_conc, hold_lines_dev, fig_agg):
        for line1 in hold_lines_conc.values():
            ax_conc.add_line(line1)
        ax_conc.legend(loc='upper right')
        for line1 in hold_lines_dev.values():
            ax_deviation.add_line(line1)
        ax_deviation.legend(loc='upper right')
        fig_agg.draw()
        
    sg.theme('DarkBlue')
    
    # Animation while loading the database to GUI:
    animation = time.time()
    future = None
    sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
    #tkthread.call_nosync(sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50))
    while True:
        if (time.time() - animation > 0.05):
            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
            #tkthread.call_nosync(sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50))
            animation = time.time()
        if future == None:
            future = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(getAnalyzerTransmition, [csvFile, False, '1550', True])
        if ( future._state != 'RUNNING' ):
            darkStatus = (future.result())[1]
            sg.PopupAnimated(None)
            future = None
            break
    #clean = True
    #analyzer = True
    #transmittance = True
    try:
        df_clean = pd.read_csv(csvFile + 'clean.csv')
        # df_analyzer = pd.read_csv(csvFile + 'analyzer.csv')
        df_transmittance = pd.read_csv(csvFile + 'transmittance.csv')
    except:
        sg.popup_ok("There was a problem reading the files.")
        exit()

    #yAxisPowerS_dictionary = {}
    #yAxisRepS_dictionary = {}
    frequencyList = df_transmittance['REP_RATE'].unique().tolist()
    powerList = df_transmittance['POWER'].unique().tolist()
    # x = []

    window2 = sg.Window("Allan Deviation", getAllanDeviationLayout(frequencyList, powerList, np.asarray(df_transmittance.columns[10:].tolist(), float)),finalize=True)
    # Creating the automatic first graph:
    fig = plt.figure()
    plt.ion()
    fig.set_figwidth(ALLAN_DEVIATION_SIZE[0])
    fig.set_figheight(ALLAN_DEVIATION_SIZE[1])
    ax_deviation = fig.add_subplot(211)
    ax_deviation.set_title("Allan Deviation")
    ax_deviation.grid(markevery=1)
    ax_conc = fig.add_subplot(212)
    ax_conc.set_xlabel("Time [s]")
    ax_deviation.set_xlabel("Averaging time [s]")
    ax_conc.set_title("Concentration [ppm]")
    ax_conc.grid()
    fig_agg = draw_figure_w_toolbar(window2['figCanvas'].TKCanvas, fig, window2['controls_cv'].TKCanvas)
    fig.tight_layout(pad=5.0)
    # Set the x-axis
    start_f = float(df_clean.columns[10])
    stop_f = float(df_clean.columns[-1])
    # End of creating the graph.
    reread = True #if no major change selected, reread stays false
    new_concentration_line = None
    new_allandeviation_line = None
    realWavelength = None
    df_concentration = None
    lastNormValue = None
    holdConcentrationList = {}
    holdAllanDeviationList = {}
    max_x_conc = 0
    min_y_conc = 0
    max_y_conc = 0
    max_x_deviation = 0
    min_y_deviation = 0
    max_y_deviation = 0

    while True:
    
        event, values = window2.read()
        # Closing the graph.
        if ( (event == 'Close Graph') or (event == sg.WIN_CLOSED) ):
            window2.close()
            break
        
        # Clear the graph and the relevant parametrs.
        elif event == '-CLEAR_PLOT-':
            window2['-CLEAR_PLOT-'].update(disabled=True)
            window2['_PowerListBoxPC_'].update(set_to_index=[])
            window2['_RepetitionListBoxPC_'].update(set_to_index=[])
            clear_plots(ax_conc, ax_deviation, values['-SLIDER-'])
            new_concentration_line = None
            new_allandeviation_line = None
            holdConcentrationList = {}
            holdAllanDeviationList = {}
            colors = [name for name, hex in mcolors.CSS4_COLORS.items()
                   if np.mean(mcolors.hex2color(hex)) < 0.7]
            colors.pop(0)
            window2['-CLEAR_PLOT-'].update(disabled=False)
        
        elif event == '_ADD_GRAPH_':
            # add_saved_lines(lines, ax_conc, fig_agg)
            #sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=100)
            #sg.Window("",[[sg.Text("Calculating...")]])
            if (len(values['_RepetitionListBoxPC_']) > 0) and (len(values['_PowerListBoxPC_']) > 0)  and (len(values['_DATA_FILE_']) > 0) and (values['_WAVEGUIDE_LENGTH_'] != ''):
                # All the logic of working Animation is starting:
                window2['_ADD_GRAPH_'].update(disabled=True)
                window2['_HOLD_'].update(disabled=True)
                window2['_CSV_'].update(disabled=True)
                window2['-CLEAR_PLOT-'].update(disabled=True)
                window2['Close Graph'].update(disabled=True)
                #window2['-SLIDER-'].update(disable=True)
                #window2['_ppm_'].update(disabled=True)
                #window2['_Precents_'].update(disabled=True)
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
                                    future1 = concurrent.futures.ThreadPoolExecutor().submit(getAnalyzerTransmition, [csvFile, values['-Reg_Norm_Val-'], values['normValue'],values['-MINUSDARK-']])
                                lastNormValue = values['normValue']
                        else:
                            if future1 == None:
                                future1 = concurrent.futures.ThreadPoolExecutor().submit(getAnalyzerTransmition, [csvFile, False, values['normValue'], values['-MINUSDARK-']])
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
                                future2 = concurrent.futures.ThreadPoolExecutor().submit(beerLambert, [csvFile, "..\\Databases\\"+values['_DATA_FILE_'][0]+'.txt', float(values['_ABS_NM_']), float(values['_WAVEGUIDE_LENGTH_']), values['_GAMA_']])
                            SecondaryOperation = False
                            future1 = None
                    #
                    if ( (future2 != None) and (time.time()-start_time>0.1) ):
                        if (future2._state != 'RUNNING'):
                            future2 = future2.result() # Take to much time!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                            df_concentration = future2[0]
                            realWavelength = future2[1]
                            df_plotted = df_concentration[df_concentration['REP_RATE'].isin(values['_RepetitionListBoxPC_']) & df_concentration['POWER'].isin(values['_PowerListBoxPC_'])]
                            label = 'p{}_rr{}_c{}_wl{:.2f}_wgl{:.2f}'.format(values['_PowerListBoxPC_'][0], values['_RepetitionListBoxPC_'][0], values['_DATA_FILE_'][0].replace('_','-'), float(realWavelength), float(values['_WAVEGUIDE_LENGTH_']))
                            if values['-Reg_Norm_Val-'] == True:
                                label = label + '_norm' + values['normValue']
                            if values['-MINUSDARK-'] and darkStatus == True:
                                label = label + '_minudark'
                            if future3 == None:
                                future3 = concurrent.futures.ThreadPoolExecutor().submit(allandevation, df_plotted)
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
                #
                # Grid:
                # ax_conc - Major ticks every 20, minor ticks every 5:
                # if (df_plotted['Interval'].tolist())[-1] > max_x_conc:
                #     max_x_conc = (df_plotted['Interval'].tolist())[-1]
                # if min(df_plotted['Concentration [ppm]'].tolist()) < min_y_conc:
                #     min_y_conc = min(df_plotted['Concentration [ppm]'].tolist())
                # if max(df_plotted['Concentration [ppm]'].tolist()) > max_y_conc:
                #     max_y_conc = max(df_plotted['Concentration [ppm]'].tolist())
                # try:
                #     major_ticks = np.arange(0, max_x_conc, 20)
                #     minor_ticks = np.arange(0, max_x_conc, 5)
                #     ax_conc.set_xticks(major_ticks)
                #     ax_conc.set_xticks(minor_ticks, minor=True)
                # except:
                #     None
                # grid_y_range = max(df_plotted['Concentration [ppm]'].tolist())
                # try:
                #     major_ticks = np.arange(min_y_conc, max_y_conc, grid_y_range/5)
                #     minor_ticks = np.arange(min_y_conc, max_y_conc, grid_y_range/20)
                #     ax_conc.set_yticks(major_ticks)
                #     ax_conc.set_yticks(minor_ticks, minor=True)
                # except:
                #     None
                # new_concentration_line = ax_conc.plot(df_plotted['Interval'], np.asarray(df_plotted['Concentration [ppm]'], float), label=label, color = color)
                # ax_conc.grid(which='minor', alpha=0.2)
                # ax_conc.grid(which='major', alpha=1)
                # # ax_deviation - Major ticks every 20, minor ticks every 5:
                # if np.log10(tau[-1]) > max_x_deviation:
                #     max_x_deviation = np.log10(tau[-1])
                # if np.log10(min(adev)) < min_y_deviation:
                #     min_y_deviation = np.log10(min(adev))
                # if np.log10(max(adev)) > max_y_deviation:
                #     max_y_deviation = np.log10(max(adev))
                # try:
                #     major_ticks = np.logspace(0, max_x_deviation, num=10, base=10.0)
                #     minor_ticks = np.logspace(0, max_x_deviation, num=10, base=10.0)
                #     ax_deviation.set_xticks(major_ticks)
                #     ax_deviation.set_xticks(minor_ticks, minor=True)
                # except:
                #     None
                # try:
                #     major_ticks = np.logspace(min_y_deviation, max_y_deviation, num=10, base=10.0)
                #     minor_ticks = np.logspace(min_y_deviation, max_y_deviation, num=10, base=10.0)
                #     ax_deviation.set_yticks(major_ticks)
                #     ax_deviation.set_yticks(minor_ticks, minor=True)
                # except:
                #     None
                # Add to both plots
                # new_allandeviation_line = ax_deviation.loglog(tau, adev, label=label, color = color)
                # ax_deviation.grid(which='minor', alpha=0.2, linestyle='--')
                # ax_deviation.grid(which='major', alpha=1, linestyle='-')
                # # Add to both plots
                # ax_deviation.legend(loc='upper right')
                clear_plots(ax_conc, ax_deviation, values['-SLIDER-'])
                add_allan_history(ax_conc,ax_deviation,holdConcentrationList,holdAllanDeviationList,fig_agg)
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
                #timeIntervalT = "The avarage Time Interval\nbetween the samples in the\nallan deviation is:\n"+str("{:.3f}".format(float(tau[0])))+" seconds."
                timeIntervalT = "The avarage Time Interval is: "+str("{:.3f}".format(mean_interval))+" seconds."
                window2['timeIntervalText'].update(timeIntervalT)
                new_concentration_line = new_concentration_line[0]
                new_allandeviation_line = new_allandeviation_line[0]
                # Show the two Graphs:
                fig_agg.draw()
                reread = False
            else:
                sg.popup_ok("Make sure the parameters are chosen correctly")
            window2['_ADD_GRAPH_'].update(disabled=False)
            window2['_HOLD_'].update(disabled=False)
            window2['_CSV_'].update(disabled=False)
            window2['-CLEAR_PLOT-'].update(disabled=False)
            window2['Close Graph'].update(disabled=False)
            window2['-MINUSDARK-'].update(darkStatus)
            if darkStatus:
                window2['darkStatusText'].update("OK")
            else:
                window2['darkStatusText'].update("'dark.csv' not Found")
            #window2['-SLIDER-'].update(disable=False)
            #window2['_ppm_'].update(disabled=False)
            #window2['_Precents_'].update(disabled=False)
            # updateRegualrGraph(df_plotted, ax, fig_agg)
        
        elif event == '_HOLD_':
            window2['_HOLD_'].update(disabled=True)
            if (new_concentration_line != None) and (new_allandeviation_line != None):
                if ((new_concentration_line._label in holdConcentrationList) or (new_allandeviation_line._label in holdAllanDeviationList) ):
                    sg.popup_auto_close("The graph already exist in database.", title="Graph Exist", auto_close_duration=2)
                else:
                    holdConcentrationList[new_concentration_line._label] = new_concentration_line
                    holdAllanDeviationList[new_allandeviation_line._label] = new_allandeviation_line
                    colors.remove(color)
                    color = colors[0]
                    new_concentration_line = None
                    new_allandeviation_line = None
                    # Site link: https://www.tutorialspoint.com/pysimplegui/pysimplegui_popup_windows.htm
                    sg.popup_auto_close("The selected graph was added.", title="Graph was added", auto_close_duration=1)
            else:
                sg.popup_auto_close("The selected graph was already added.", title="Already added", auto_close_duration=2)
            window2['_HOLD_'].update(disabled=False)

        elif event == '_CSV_':
            window2['_CSV_'].update(disabled=True)
            # df_TOSAVE.to_csv(dirname + '\\' + values['csvFileName'] + '.csv', index=False, encoding='utf-8')
            saveAllanPlots(holdAllanDeviationList, new_allandeviation_line, values['csvFileName'], csvFile)
            csvFileWasSaved = '\'' + values['csvFileName'] + '.csv\' file was saved'
            window2['csvFileName'].update("csv file name")
            sg.popup_auto_close(csvFileWasSaved, title="CSV File Saved", auto_close_duration=2)
            window2['_CSV_'].update(disabled=False)

        elif event == '_DATA_FILE_':
            if len(values['_DATA_FILE_']) > 0:
                wavelength = get_minimum(values['_DATA_FILE_'][0]+'.txt')
                window2['section_AbsValue'].update(visible=True)
                window2['_ABS_NM_'].update(wavelength)
            else:
                window2['section_AbsValue'].update(visible=False)
            reread = True
        
        elif event == '-Reg_Norm_Val-' or event == 'normValue' or event == '_WAVEGUIDE_LENGTH_' or event == '_ABS_NM_' or event =="-MINUSDARK-":
            reread = True

        elif event == '-SLIDER-':
            #print(values['-SLIDER-'])
            if values['-SLIDER-'] == 0: # ppm mode
                None
            elif values['-SLIDER-'] == 1: # '%'' mode
                None
            
    # End of interactive.

def timeSweepGraph(csvFile):

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
    if (not (clean and substance)):
        sg.popup_ok("There was a problem reading the files.")
        exit()
    
    df_ratio, df_clean, df_substance, darkStatus = getNormlizedByCustomFreq(csvFile, True)

    # yAxisPowerS_dictionary = {}
    # yAxisRepS_dictionary = {}
    frequencyList = df_ratio['REP_RATE'].unique().tolist()
    powerList = df_ratio['POWER'].unique().tolist()
    # x = []

    window2 = sg.Window("Interactive Graph", getLayout(frequencyList, powerList, np.asarray(df_ratio.columns[10:].tolist(), float)),finalize=True)
    # Creating the automatic first graph:
    fig = plt.figure()
    plt.ion() 
    # fig = plt.gcf()
    fig.set_figwidth(PLOT_SIZE[0])
    fig.set_figheight(PLOT_SIZE[1])
    # draw_figure(window2['figCanvas'].TKCanvas, fig)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Wavelength [nm]")
    ax.grid()
    fig_agg = draw_figure_w_toolbar(window2['figCanvas'].TKCanvas, fig, window2['controls_cv'].TKCanvas)
    plt.title('No Plot to show. Choose data...')
    # Set the x-axis
    start_f = float(df_clean.columns[10])
    stop_f = float(df_clean.columns[-1])
    # End of creating the graph.
    
    df_plotted_full = df_ratio
    scales_dict = {"LOG": {"CLEAN": "[dBm]",
                           "SUBSTANCE": "[dBm]",
                           "RATIO": "[dB]"
                           },
                    "WATT":{"CLEAN": "[mW]",
                           "SUBSTANCE": "[mW]",
                           "RATIO": "Ratio"
                           }
    }
    scales = scales_dict["LOG"]
    scale = "[dB]"
    if darkStatus:
        window2['darkStatus'].update("OK")
    else:
        window2['darkStatus'].update("'dark.csv' not Found")
    #
    while True:
    
        event, values = window2.read()
        # Closing the graph.
        if ( (event == 'Close Graph') or (event == sg.WIN_CLOSED) ):
            window2.close()
            break
        
        # Clear the graph and the relevant parametrs.
        elif event == '-CLEAR_PLOT-':
            window2['_PowerListBoxPC_'].update(set_to_index=[])
            window2['_RepetitionListBoxPC_'].update(set_to_index=[])
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
            df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxPC_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxPC_'])]
            if len(df_plotted) < 0:
                window3.close()
                continue
            updateRegualrGraph(df_plotted, ax, fig_agg)
            window3.close()
            if values['-MINUS_DARK-'] and darkStatus:
                window2['darkStatus'].update("OK")
            elif values['-MINUS_DARK-'] and (darkStatus == False):
                window2['darkStatus'].update("'dark.csv' not Found")
            elif values['-MINUS_DARK-']==False and (darkStatus == False):
                window2['darkStatus'].update("Calculation ignoring dark measurment")
            elif values['-MINUS_DARK-']==False and (darkStatus == True):
                window2['darkStatus'].update("No way! No sense")
        
        elif (event == '_RepetitionListBoxPC_') or (event == '_PowerListBoxPC_'):
            df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxPC_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxPC_'])]
            if len(df_plotted) < 0:
                #ax.cla()
                #ax.grid()
                continue
            updateRegualrGraph(df_plotted, ax, fig_agg)
        
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
            updateRegualrGraph(df_plotted,ax,fig_agg)
            window3.close()

        elif (event == 'cleanCheckBox'):
            ax.cla()
            ax.grid()
            scale = scales["CLEAN"]
            if (values['cleanCheckBox']):
                df_plotted_full = df_clean
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxPC_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxPC_'])]
                if len(df_plotted) < 0:
                    continue
                updateRegualrGraph(df_plotted, ax, fig_agg)
                values['substanceCheckBox'] = False
                values['normCheckBox'] = False                                      
                window2['substanceCheckBox'].update(False)
                window2['normCheckBox'].update(False)
        
        elif (event == 'substanceCheckBox'):
            ax.cla()
            ax.grid()
            scale = scales["SUBSTANCE"]
            if (values['substanceCheckBox']):
                df_plotted_full = df_substance
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxPC_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxPC_'])]
                if len(df_plotted) < 0:
                    continue
                updateRegualrGraph(df_plotted, ax, fig_agg)
                values['cleanCheckBox'] = False
                values['normCheckBox'] = False
                window2['cleanCheckBox'].update(False)                              
                window2['normCheckBox'].update(False)
        
        elif (event == 'normCheckBox'):
            ax.cla()
            ax.grid()
            scale = scales["RATIO"]
            if (values['normCheckBox']):
                df_plotted_full = df_ratio
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxPC_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxPC_'])]
                if len(df_plotted) < 0:
                    continue
                updateRegualrGraph(df_plotted, ax, fig_agg)
                values['cleanCheckBox'] = False                                      
                values['substanceCheckBox'] = False
                window2['cleanCheckBox'].update(False)
                window2['substanceCheckBox'].update(False)

        # Always execute:
        if values['-Reg_Norm_Val-']:
            if values['-REG_LOG_SCALE-']:
                scale = '[dB]'
            else:
                scale = 'Ratio'
        plt.ylabel(scale)
        plt.xlabel("Wavelength [nm]")
####################################################
if __name__ == '__main__':
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Plot graphs')

    # Add arguments
    parser.add_argument('--csv_name', type=str)
    parser.add_argument('--analyzer_substance', type=bool)

    # Parse the arguments
    args = parser.parse_args()

    if args.csv_name == None:
        # dirname = 'C:\BGUProject\Automation-of-spectral-measurements\Results\\2023_05_04_12_54_02_685629___longer_analyzer_empty__\\'
        dirname = 'C:\BGUProject\Automation-of-spectral-measurements\Results\\2023_05_15_19_12_36_782780_Test_sample1_CF=1500_Span=50_analyzer=False\\'
        #dirname = 'C:\BGUProject\Automation-of-spectral-measurements\Results\\2023_05_04_12_54_02_685629___longer_analyzer_empty__\\'
        # dirname = "C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\2023_05_04_12_54_02_685629___longer_analyzer_empty___CF=1600nm, Span=50nm, NPoints=Auto, sens=MID, res=2nm (1_643nm), analyzer=True\\"
        args.csv_name = dirname
        args.analyzer_substance = False
        #"C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\Simulation\\"
        #"C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\Analyzer_Test\\"
        # args.csv_name = "C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\2023_04_19_16_49_58_336962_Real Test\\"
    interactiveGraph(args.csv_name, analyzer_substance=args.analyzer_substance)

###########################################
# if __name__ == '__main__':
#     # Create the argument parser
#     parser = argparse.ArgumentParser(description='Plot graphs')

#     # Add arguments
#     parser.add_argument('--csv_name', type=str)
#     parser.add_argument('--analyzer_substance', type=bool)

#     # Parse the arguments
#     args = parser.parse_args()

#     if args.csv_name == None:
#         dirname = 'C:\BGUProject\Automation-of-spectral-measurements\Results\\2023_05_04_12_54_02_685629___longer_analyzer_empty__\\'
#         # dirname = "C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\2023_05_04_12_54_02_685629___longer_analyzer_empty___CF=1600nm, Span=50nm, NPoints=Auto, sens=MID, res=2nm (1_643nm), analyzer=True\\"
#         args.csv_name = dirname
#         args.analyzer_substance = True
#         #"C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\Simulation\\"
#         #"C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\Analyzer_Test\\"
#         # args.csv_name = "C:\\Users\\2lick\\OneDrive - post.bgu.ac.il\\Documents\\Final BSC Project\\Code\\Automation-of-spectral-measurements\\Results\\2023_04_19_16_49_58_336962_Real Test\\"
#     interactiveGraph(args.csv_name, analyzer_substance=args.analyzer_substance)
