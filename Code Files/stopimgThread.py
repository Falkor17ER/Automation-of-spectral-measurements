import threading
import queue

def worker(q):
    # do some work here
    result = 42

    # put the result on the queue
    q.put(result)

q = queue.Queue()
t = threading.Thread(target=worker, args=(q,))
t.start()

# wait for the thread to finish and get the result
result = q.get()
t.join()

print(result)



# import threading
# import time

# class theTest(threading.Thread):
#     def __init__(self):
#         threading.Thread.__init__(self)
#         self.stop_event = threading.Event()

#     def run(self):
#         print("before calling the function")
#         time.sleep(2)
#         if self.stop_event.is_set():
#             return
#         print("Now calling to 'check' function")
#         check(self)

#     def stop(self):
#         self.stop_event.set()

# def check(a):
#     while not a.stop_event.is_set():
#         print("Inside the 'check' function")
#         time.sleep(1)
#         pass

# t = theTest()
# t.start()

# time.sleep(4)
# # stop the thread
# t.stop()
# print("Finish the program")


# #---------------------------------

# import threading

# class WorkerThread(threading.Thread):
#     def __init__(self, arg1, arg2):
#         threading.Thread.__init__(self)
#         self.arg1 = arg1
#         self.arg2 = arg2
#         self.stop_event = threading.Event()

#     def run(self):
#         while not self.stop_event.is_set():
#             # do some work here with self.arg1 and self.arg2
#             pass

#     def stop(self):
#         self.stop_event.set()

# t = WorkerThread(arg1, arg2)
# t.start()
# # stop the thread
# t.stop()






























# # import threading
# # import time

# # def worker(event):
# #     while True:
# #         print("Now in the thread")
# #         event.wait()

# # event = threading.Event()
# # t = threading.Thread(target=worker, args=(event,))
# # t.start()

# # # stop the thread
# # time.sleep(3)
# # event.set()
# # print("End the program")




# # t.join()




# # # import threading
# # # import time

# # # class WorkerThread(threading.Thread):
# # #     def __init__(self):
# # #         threading.Thread.__init__(self)
# # #         self.stop_event = threading.Event()

# # #     def run(self):
# # #         while not self.stop_event.is_set():
# # #             print("Working...")
# # #             time.sleep(1)

# # #     def stop(self):
# # #         self.stop_event.set()

# # # def worker(toPrint):
# # #     while True:
# # #         print("Working..." + toPrint)
# # #         time.sleep(1)

# # # ##################################
# # # t = threading.Thread(target=worker, args=("now inside the thread",))
# # # a = WorkerThread(worker)
# # # a.start()

# # # time.sleep(5)
# # # t.stop()





# # # # def endThread():
# # # #     print("Thread stopped, and finished.")

# # # # t = threading.Thread(target=worker)
# # # # t.start()

# # # # time.sleep(3)
# # # # t.do_run = False

# # # # t = threading.Thread(target=endThread)
# # # # t.start()

# # # # #t.join()
