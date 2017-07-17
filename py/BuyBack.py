'''
查询国债逆回购行情，计算国债逆回购实际利率
Created on 2017年6月29日
@author: tiany
'''

from Ticker import Ticker
import pandas as pd

class BuyBack:
    # 回购代码列表
    dBbCodes = {'sh204001': 1, 'sh204002': 2, 'sh204003': 3, 
                'sh204004': 4, 'sh204007': 7, 'sh204014': 14, 
                'sh204028': 28, 'sh204091': 91, 'sh204182': 182,
                'sz131810': 1, 'sz131811': 2, 'sz131800': 3, 
                'sz131809': 4, 'sz131801': 7, 'sz131802': 14, 
                'sz131803': 28, 'sz131805': 91, 'sz131806': 182}
    
    # Nominal days: How much fee (RMB) every 100000 yuan
    dBbFees = {1: 1, 2: 2, 3: 3, 4: 4, 7: 5, 14: 10, 28: 20, 91: 30, 182: 30}
    
    dCurEfN = {}    # effective natural days between Borrow Date and Buyback Date (two clearing dates)
    dCurOcp = {}    # natural days of money occupied (natural days between first and second settlement)
    dCurEfT = {}    # effective trade days in between two clearing dates
    
    ticker = None
    dBbTicker = {}
    dfBbTicker = None
    
    fMaxSzRateIn7d = 0.0
    sMaxSzCodeIn7d = ''
    fMaxShRateIn7d = 0.0
    sMaxShCodeIn7d = ''
    
    def __init__(self, odTrdCal, sDate, ticker = None):
        self.odTrdCal = odTrdCal      # 交易日历
        if ticker:
            self.ticker = ticker
        else:
            self.ticker = Ticker(self.dBbCodes.keys())
        self.calcEffectDays(sDate)
    
    # 生成指定日期范围内每种逆回购的真实有效天数.
    # 逆回购实行T+0日清算、T+1日交收制度。注意清算日一定是交易日，而交收日一定是清算日的下一个交易日。
    # 2017年5月22日之前，使用「回购天数」作为计息天数。所谓「回购天数」，是指，n天期回购的回购天数就是n。
    # 2017年5月22日之后，使用「实际占款天数」作为计息天数。所谓「实际占款天数」，是指两个交收日之间的自然日天数。
    def calcEffectDays(self, sDate):
        slDates = list(self.odTrdCal.keys())
        # 找到最近交易日的位置
        def findClosestTrdIdx(i):
            sResDate = slDates[i]
            while not self.odTrdCal[sResDate]['can_trd']:
                i += 1
                sResDate = slDates[i]
            #end while
            return i
        
        iNtlBgn = slDates.index(sDate)      # Begin natural date index
        iClrBgn = iNtlBgn                   # Begin clearing date index (assume sDate is trade day)
        iSetBgn = findClosestTrdIdx(iClrBgn + 1)
        
        # 为每个 名义回购天数 计算 其 实际回购天数
        for n in set(self.dBbCodes.values()):
            iNtlEnd = iNtlBgn + n           # 到期自然日索引
            iClrEnd = findClosestTrdIdx(iNtlEnd)
            iSetEnd = findClosestTrdIdx(iClrEnd + 1)
            
            self.dCurEfN[n] = iClrEnd - iClrBgn
            self.dCurOcp[n] = iSetEnd - iSetBgn
            
            nTrd = 0
            for i in range(iClrBgn, iClrEnd):
                if self.odTrdCal[slDates[i]]['can_trd']:
                    nTrd += 1
            self.dCurEfT[n] = nTrd
        #end for
        
        for sCode, nNmnl in self.dBbCodes.items():
            self.dBbTicker[sCode] = {'nominal':nNmnl, 'effective':self.dCurEfN[nNmnl], 
                                    'occupied':self.dCurOcp[nNmnl], 'effct_trade':self.dCurEfT[nNmnl]}
        
        #self.dfBbCodes = pd.DataFrame(self.dBbCodes).T
    #end def
    
    def printEffectRates(self):
        self.dfBbTicker = pd.DataFrame(self.dBbTicker).T
        self.dfBbTicker = self.dfBbTicker.sort_values(['effct_rate'], ascending=[False])
        print(self.dfBbTicker)
    
    def refreshTicker(self):
        self.ticker.refreshQuotes()
        self.updateBbTicker()
        return self.dBbTicker
    
    def updateBbTicker(self):
        self.fMaxSzRateIn7d = 0.0
        self.fMaxShRateIn7d = 0.0
        #self.sMaxSzCodeIn7d = ''
        for sCode, dQt in self.ticker.dTicker.items():
            dBbQuote = self.dBbTicker[sCode]
            dBbQuote['bid']    = dQt['bid']
            dBbQuote['bsize1'] = dQt['bsize1']
            nNmnl = dBbQuote['nominal']
            nEffN = dBbQuote['effective']   # effective natural days between two clearing dates
            fEffRate = dQt['bid'] * dBbQuote['occupied'] / nEffN - self.dBbFees[nNmnl] / nEffN * 0.365
            dBbQuote['effct_rate'] = fEffRate
            if nEffN <= 7:
                if sCode[:2] == 'sz' and fEffRate > self.fMaxSzRateIn7d:
                    self.fMaxSzRateIn7d = fEffRate
                    self.sMaxSzCodeIn7d = sCode
                if sCode[:2] == 'sh' and fEffRate > self.fMaxShRateIn7d:
                    self.fMaxShRateIn7d = fEffRate
                    self.sMaxShCodeIn7d = sCode
    #end def


if __name__ == '__main__':
    from UtilFunc import *
    import time
    od = readTuplesToDict('../params/TrdCalCn.txt', sType = 'OrderedDict')
    #bb = BuyBack(od, time.strftime('%Y%m%d'))
    bb = BuyBack(od, '20170630')
    bb.printEffectRates()
    #print(bb.refreshTicker())