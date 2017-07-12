'''
Created on 2017年7月12日

@author: tianyuan.chen
'''

from queue import Queue
import time
from threading import Thread
#class TaskGenerator:
    

class Organizer:
    # Declaring a variable outside of __init__ is declaring a class-level variable, which is shared by all instances.
    #task_queue = Queue()
    def __init__(self):
        self.task_queue = Queue()
        self.startTaskGenThread()
    
    def startTaskGenThread(self):
        # https://docs.python.org/3.6/library/threading.html#threading.Thread
        # Daemon threads are killed automatically when program quits.
        self.thrdTaskGen = Thread(target = self.genTask, daemon = True)
        self.thrdTaskGen.start()
    
    def genTask(self):
        i = 0
        while True:
            i += 1
            self.task_queue.put("Task {}".format(i))
            time.sleep(1)
    #end def
    
    def getTask(self):
        # https://docs.python.org/3.6/library/queue.html
        for i in range(0, 15):
            obj = self.task_queue.get()     # block is True by default
            print(obj)

if __name__ == '__main__':
    orgnz = Organizer()
    orgnz.getTask()