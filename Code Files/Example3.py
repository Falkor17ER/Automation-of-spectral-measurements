import PySimpleGUI as sg
import time
from time import sleep

while True:
    start = time.time()
    animation = time.time()
    while True:
        if (time.time() - start > 10):
            sg.PopupAnimated(None)
            sleep(3)
            start = time.time()
            while time.time()-start <10:
                if (time.time() - animation > 0.05):
                    sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                    animation = time.time()
            break
        if (time.time() - animation > 0.05):
            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
            animation = time.time()
    print("End of while_1")
    sleep(3)
    start = time.time()
    animation = time.time()
    while True:
        if (time.time() - start > 10):
            sg.PopupAnimated(None)
            break
        if (time.time() - animation > 0.05):
            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
            animation = time.time()
    print("End of while_2")
    break
print("End of mission")

#import concurrent.futures
#future = concurrent.futures.ThreadPoolExecutor().submit(test, ["Hello", "Shalom"])
#result = future.result()   
