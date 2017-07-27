'''
查询国债逆回购行情，计算国债逆回购实际利率
Created on 2017年6月29日
@author: tiany
'''

from Ticker import Ticker
import pandas as pd
import time

class BuyBack:
    # Variables defined here are class variables (will be the same to all instances)
    # 回购代码列表
    dBbCodes = {'sh204001': 1, 'sh204002': 2, 'sh204003': 3, 
                'sh204004': 4, 'sh204007': 7, 'sh204014': 14, 
                'sh204028': 28, 'sh204091': 91, 'sh204182': 182,
                'sz131810': 1, 'sz131811': 2, 'sz131800': 3, 
                'sz131809': 4, 'sz131801': 7, 'sz131802': 14, 
                'sz131803': 28, 'sz131805': 91, 'sz131806': 182}
    
    # Nominal days: How much fee (RMB) every 100000 yuan
    dBbFees = {1: 1, 2: 2, 3: 3, 4: 4, 7: 5, 14: 10, 28: 20, 91: 30, 182: 30}
    
    
    
    ticker = None
    dBbTicker = {}
    dfBbTicker = None
    
    fMaxSzRateIn7d = 0.0
    sMaxSzCodeIn7d = ''
    fMaxShRateIn7d = 0.0
    sMaxShCodeIn7d = ''
    
    def __init__(self, trdCal, ticker = None, sDate = None):
        self.trdCal = trdCal      # 交易日历

        if ticker:
            self.ticker = ticker
        else:
            self.ticker = Ticker(self.dBbCodes.keys())
        
        if sDate:
            self.sCurDate = sDate
        else:
            self.sCurDate = trdCal.getTodayStr()
        
        self.calcEffectDays(self.sCurDate)
    #end def
    
    # 生成指定日期范围内每种逆回购的真实有效天数.
    # 逆回购实行T+0日清算、T+1日交收制度。注意清算日一定是交易日，而交收日一定是清算日的下一个交易日。
    # 2017年5月22日之前，使用「回购天数」作为计息天数。所谓「回购天数」，是指，n天期回购的回购天数就是n。
    # 2017年5月22日之后，使用「实际占款天数」作为计息天数。所谓「实际占款天数」，是指两个交收日之间的自然日天数。
    def calcEffectDays(self, sDate):
        self.dAccrual = {}    # 计息天数; natural days of money occupied (natural days between first and second settlement)
        self.dUsableN = {}    # 资金可用所需自然日; effective natural days between Borrow Date and Buyback Date (two clearing dates)
        self.dUsableT = {}    # 资金可用所需交易日; effective trade days in between two clearing dates

        # 为每个 名义回购天数 计算 其 计息天数 (两个交收日之间的自然日天数)、资金可用所需自然日 (两个清算日之间的自然日天数)、资金可用所需交易日(两个清算日之间的交易日天数)
        for n in set(self.dBbCodes.values()):
            sClrDate1 = sDate                               # 首次清算日 = T+0 日
            sSetDate1 = trdCal.trdDateAdd(sClrDate1, 1)     # 首次交收日 = 首次清算日的下一个交易日
            sNomnlExp = trdCal.ntlDateAdd(sDate, n)         # 名义到期日 = 首次交易日 + 名义回购天数 (自然日)
            sEffctExp = trdCal.closestTrdDate(sNomnlExp)    # 实际到期日 = 不早于名义到期日的第一个交易日
            sClrDate2 = sEffctExp                           # 到期清算日 就是 实际到期日
            sSetDate2 = trdCal.trdDateAdd(sClrDate2, 1)     # 到期交收日 = 到期清算日的下一个交易日

            self.dAccrual[n] = trdCal.ntlDateDelta(sSetDate2, sSetDate1)
            self.dUsableN[n] = trdCal.ntlDateDelta(sClrDate2, sClrDate1)
            self.dUsableT[n] = trdCal.trdDateDelta(sClrDate2, sClrDate1)

            
        # 初始化 self.dBbTicker
        for sCode, nNominal in self.dBbCodes.items():
            self.dBbTicker[sCode] = {'nominal':nNominal, 'accrual':self.dAccrual[nNominal], 
                                     'usable_n':self.dUsableN[nNominal], 'usable_t':self.dUsableT[nNominal]}
        
        #self.dfBbCodes = pd.DataFrame(self.dBbCodes).T
    #end def
    
    def printEffectRates(self):
        self.refreshTicker()
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
            nNominal = dBbQuote['nominal']
            nUsableN = dBbQuote['usable_n']   # effective natural days between two clearing dates
            fEffRate = dQt['bid'] * dBbQuote['accrual'] / nUsableN - self.dBbFees[nNominal] / nUsableN * 0.365
            dBbQuote['effct_rate'] = fEffRate
            if nUsableN <= 7:
                if sCode[:2] == 'sz' and fEffRate > self.fMaxSzRateIn7d:
                    self.fMaxSzRateIn7d = fEffRate
                    self.sMaxSzCodeIn7d = sCode
                if sCode[:2] == 'sh' and fEffRate > self.fMaxShRateIn7d:
                    self.fMaxShRateIn7d = fEffRate
                    self.sMaxShCodeIn7d = sCode
    #end def

    def genTradeList(self):
        self.refreshTicker()
        # Sort effective rates from largest to smallest
        sl = sorted(self.dBbTicker.items(), key=lambda t:t[1]['effct_rate'], reverse=True)
        # Generate one SH and one SZ buyback.
        lsToTrd = []
        dFlag = {'sh': False, 'sz': False}
        for sCode, d in sl:
            if d['nominal'] > 7:
                continue
            sPfx = sCode[:2]
            if not dFlag[sPfx]:
                lsToTrd.append({'code': sCode, 'type': 'buyback', 'trade_type': 'sell', 'price': d['bid']})
                dFlag[sPfx] = True
            if dFlag['sh'] and dFlag['sz']:
                break
        #end for
        return lsToTrd
    #end def


#end class


if __name__ == '__main__':
    #import UtilFunc as util
    from TradeCalendar import TradeCalendar
    import time
    trdCal = TradeCalendar('../params/TrdCalCn.txt')
    bb = BuyBack(trdCal)        # , sDate = time.strftime('%Y%m%d')
    #bb = BuyBack(od, '20170630')
    #bb.refreshTicker()
    #bb.printEffectRates()
    print(bb.genTradeList())
#end if