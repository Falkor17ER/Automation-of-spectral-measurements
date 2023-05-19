
import PySimpleGUI as sg

MODE  = "Hello"
menu_def = [['Choose Layout: ', ['Layout1', 'Layout2']], [MODE]]

font = ('Courier New', 11)
sg.set_options(font=font)

layout1 = [[sg.Text("Layout 1 text!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")]]
layout2 = [[sg.Text("Layout 2 text")]]

layout = [
    [sg.Menu(menu_def, key='MENU')],
    [sg.Column(layout1, key='COL1Sweep'),
     sg.Column(layout2, key='COL2Allan', visible=False)],
]
window = sg.Window("Title", layout, finalize=True)

col, col1, col2 = 1, window['COL1Sweep'], window['COL2Allan']

while True:

    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break
    print(event, values)
    if event == 'Layout1' and col != 1:
        col = 1
        MODE = "Layout1"
        window.Refresh()
        col1.update(visible=True)
        col2.update(visible=False)
    elif event == 'Layout2' and col != 2:
        col = 2
        MODE = "Layout 2"
        window.Refresh()
        col2.update(visible=True)
        col1.update(visible=False)
