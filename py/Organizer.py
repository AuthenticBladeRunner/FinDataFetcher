'''
Created on 2017年7月12日

@author: tianyuan.chen
'''

from TradeCalendar import TradeCalendar
from TaskDispatcher import TaskDispatcher
from Ticker import Ticker
from BuyBack import BuyBack

class Organizer:
    # Declaring a variable outside of __init__ is declaring a class-level variable, which is shared by all instances.
    
    def __init__(self):
        self.trdCal = TradeCalendar('../params/TrdCalCn.txt')
        self.taskPutter = TaskDispatcher("../params/DailySched.txt")
        self.ticker = Ticker()
        self.bbk = BuyBack(self.trdCal)
    #end def
    
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
                self.doTask(sTaskName)
            #end for
    #end def
    
    def doTask(self, sTask):
        sTask = sTask.lower()
        if sTask == 'buyback':
            self.bbk.genOppties()
            pass
    #end def

if __name__ == '__main__':
    orgnz = Organizer()
    orgnz.run()