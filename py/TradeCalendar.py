'''
Created on 2017年7月18日

@author: tianyuan.chen
'''

import UtilFunc as util
from datetime import datetime, timedelta

class TradeCalendar:
    def __init__(self, sCalFile):
        # An OrderedDict mapping date to its index: {'20180222': {'ntl_idx': 329, 'trd_idx': 219}, ...}
        self.odTrdCal = util.readTuplesToDict(sCalFile, sType = 'OrderedDict')
        self.slDates = list(self.odTrdCal.keys())    # Sorted list of dates
        self.dIdxNtl = {}
        self.dIdxTrd = {}
        for sDate, dInfo in self.odTrdCal.items():
            self.dIdxNtl[dInfo['ntl_idx']] = sDate
            iTrdIdx = dInfo['trd_idx']
            if iTrdIdx:
                self.dIdxTrd[iTrdIdx] = sDate
        #end for
        self.dtToday = datetime.today()
        self.sToday = self.dtToday.strftime('%Y%m%d')
    #end def
    
    def getTodayStr(self):
        return self.sToday
    #end def
    
    # Get trade date not smaller than the given date
    def closestTrdDate(self, sDate):
        if self.odTrdCal[sDate]['trd_idx']:
            return sDate
        iNtlIdx = self.odTrdCal[sDate]['ntl_idx']
        for i in range(30):
            iNtlIdx += 1
            sDate = self.dIdxNtl[iNtlIdx]
            if self.odTrdCal[sDate]['trd_idx']:
                return sDate
        return None
    #end def

    def trdDateAdd(self, sTrdDate, iDelta):
        return self.dIdxTrd[self.odTrdCal[sTrdDate]['trd_idx'] + iDelta]
    #end def

    def ntlDateAdd(self, sDate, iDelta):
        return self.dIdxNtl[self.odTrdCal[sDate]['ntl_idx'] + iDelta]
    #end def
    
    def trdDateDelta(self, sTrdDate1, sTrdDate2):
        return self.odTrdCal[sTrdDate1]['trd_idx'] - self.odTrdCal[sTrdDate2]['trd_idx']
    #end def

    def ntlDateDelta(self, sDate1, sDate2):
        return self.odTrdCal[sDate1]['ntl_idx'] - self.odTrdCal[sDate2]['ntl_idx']
    #end def
        
    
#end class

if __name__ == '__main__':
    pass