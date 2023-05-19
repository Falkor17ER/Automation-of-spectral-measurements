import PySimpleGUI as sg

def Text(size):
    return sg.Text('', size=size, relief=sg.RELIEF_RAISED)

def frame():
    return [
        [sg.Text('OK:'),         sg.Push(), Text(10)],
        [sg.Text('NG:'),         sg.Push(), Text(10)],
        [sg.Text('Yield Rate:'), sg.Push(), Text(15)],
        [sg.Text('Total:'),      sg.Push(), Text(15)],
    ]

font = ('Courier New', 11)
sg.theme('DarkBlue3')
sg.set_options(font=font)

column = [
    [sg.Frame(f'AI-{i}', frame(), pad=(0, 0), key=f'FRAME {i}')]
        for i in range(1, 11)
]

layout = [
    [sg.Text('RESULT', justification='center', background_color='#424f5e', expand_x=True)],
    [sg.Column(column, scrollable=True, vertical_scroll_only=True,
        size=(270+16, 129*3), key='COLUMN')],     # width of scrollbar is 16 pixels
]

window = sg.Window('Matplotlib', layout, finalize=True)
print(window['FRAME 1'].get_size())              # get frame size in pixels (270, 129)
window.read(close=True)



















# import PySimpleGUI as sg

# MODE  = "Hello"
# menu_def = [['Choose Layout: ', ['Layout1', 'Layout2']], [MODE]]

# font = ('Courier New', 11)
# sg.set_options(font=font)

# layout1 = [[sg.Text("Layout 1 text!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")]]
# layout2 = [[sg.Text("Layout 2 text")]]

# layout = [
#     [sg.Menu(menu_def, key='MENU')],
#     [sg.Column(layout1, key='COL1Sweep'),
#      sg.Column(layout2, key='COL2Allan', visible=False)],
# ]
# window = sg.Window("Title", layout, finalize=True)

# col, col1, col2 = 1, window['COL1Sweep'], window['COL2Allan']

# while True:

#     event, values = window.read()

#     if event == sg.WIN_CLOSED:
#         break
#     print(event, values)
#     if event == 'Layout1' and col != 1:
#         col = 1
#         MODE = "Layout1"
#         window.Refresh()
#         col1.update(visible=True)
#         col2.update(visible=False)
#     elif event == 'Layout2' and col != 2:
#         col = 2
#         MODE = "Layout 2"
#         window.Refresh()
#         col2.update(visible=True)
#         col1.update(visible=False)
