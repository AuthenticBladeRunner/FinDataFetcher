'''
Created on 2017年7月13日

@author: tiany
'''

from queue import Queue
import time
from threading import Thread
from UtilFunc import *

class TaskDispatcher:
    # Declaring a variable outside of __init__ is declaring a class-level variable, which is shared by all instances.
    #qTask = Queue()
    def __init__(self, sTaskFile):
        self.dTask = readTuplesToDict(sTaskFile, sType='ListDict')
        self.lsSent = []
        self.qTask = Queue()
        self.startTaskGenThread()
    
    def startTaskGenThread(self):
        # https://docs.python.org/3.6/library/threading.html#threading.Thread
        # Daemon threads are killed automatically when program quits.
        self.thrdTaskGen = Thread(target = self.genTask, daemon = True)
        self.thrdTaskGen.start()
    
    def genTask(self):
        while True:
            sHms = time.strftime('%H%M%S')
            sHm = sHms[:4]
            if sHm in self.dTask:
                self.qTask.put((sHms, self.dTask[sHm]))
                self.lsSent.append((sHm, self.dTask.pop(sHm)))
            time.sleep(5)
    #end def
    
    def getTask(self):
        # https://docs.python.org/3.6/library/queue.html
        return self.qTask.get()     # block is True by default
    #end def
    
    def addTask(self, sHm, sTask, iPos = None):
        if iPos is None:
            self.dTask[sHm].append(sTask)
        else:
            self.dTask[sHm].insert(iPos, sTask)
    #end def
    
    def updateTasks(self, dNewTask):
        self.dTask.update(dNewTask)
    #end def
            
if __name__ == '__main__':
    pass