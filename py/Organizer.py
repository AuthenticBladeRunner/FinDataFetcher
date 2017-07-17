'''
Created on 2017年7月12日

@author: tianyuan.chen
'''

from TaskDispatcher import TaskDispatcher
from _asyncio import Task

class Organizer:
    # Declaring a variable outside of __init__ is declaring a class-level variable, which is shared by all instances.
    
    def __init__(self):
        self.taskPutter = TaskDispatcher("../params/DailySched.txt")
    
    def run(self):
        wannaQuit = False
        while not wannaQuit:
            tTask = self.taskPutter.getTask()
            sSendTime, lsTasks = tTask
            print('Got task {} sent at {}'.format(lsTasks, sSendTime))
            print('Sent items: {}'.format(self.taskPutter.lsSent))
            for sTaskName in lsTasks:
                if sTaskName.lower() == 'quit':
                    wannaQuit = True
                    #break
            #end for
    #end def
    
    def doTask(self, sTask):
        pass
    #end def

if __name__ == '__main__':
    orgnz = Organizer()
    orgnz.run()