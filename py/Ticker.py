'''
# 一个通用的实时行情获取类
# 行情数据源默认为新浪
# 代码采用新浪代码的表达方式

@author: tiany
'''

import requests
#import types
#from collections import defaultdict



class Ticker:
    sEngine = 'sina'
    lsSymbols = []
    sSymbols = ''
    dTicker = {}   # defaultdict(dict)
    
    def __init__(self, lsSymbols = None):
        if lsSymbols:
            self.lsSymbols = list(lsSymbols)
            self.sSymbols = ','.join(self.lsSymbols)
    
    def genQuoteDict(self, lsColStr, lsColDef):
        nCols = min(len(lsColStr), len(lsColDef))
        dQuote = {}
        for i in range(0, nCols):
            sColName, sColType = lsColDef[i]
            sColStr = lsColStr[i]
            if sColType == 'float':
                try:
                    dQuote[sColName] = float(sColStr)
                except Exception:
                    dQuote[sColName] = None
            else:
                dQuote[sColName] = sColStr
        #end for
        return dQuote
    #end def
    
    def refreshQuotes(self):
        if self.sEngine == 'sina':
            self.refreshSinaQuotes()
    
    def refreshSinaQuotes(self):
        self.updateQuotesFromSina(self.sSymbols)
    
    def refreshTicker(self, symbols):
        if self.sEngine == 'sina':
            self.updateQuotesFromSina(symbols)
    
    def updateQuotesFromSina(self, symbols):
        # Use 'isinstance' to check if obj is an instance of str or any subclass of str.
        # Use 'type(obj) is str' to check if the type of obj is exactly str.
        if not isinstance(symbols, str):
            symbols = ','.join(symbols)
        sUrl = 'http://hq.sinajs.cn/list={}'.format(symbols)
        
        resp = requests.get(sUrl)
        lsLines = resp.text.split('\n')

        
        for sLine in lsLines:
            sLine = sLine.strip()
            if len(sLine) == 0:
                continue
            iBgn  = sLine.find('hq_str_') + 7
            iEnd  = sLine.find('=')
            sCode = sLine[iBgn:iEnd]
            
            iBgn  = sLine.find('"') + 1
            iEnd  = sLine.rfind('"')
            sInfo = sLine[iBgn:iEnd]
            lsCols = sInfo.split(',')
            #nCols = len(lsCols)

            #if lsCols[-1] == '':
            #    lsCols.pop()
            
            lsColDef = []
            if sCode[:2] in ['sh', 'sz']:    # A股
                # 0名称 1今开 2昨收(前复权) 3现价 4最高 5最低 6买一价 7卖一价 8成交数(股) 9成交额(元)
                # 10(买i申请股数、买i报价)i=1~5  20(卖i申请股数、卖i报价)i=1~5  30日期(yyyy-mm-dd)  31时间(HH:MM:SS)
                # 32状态： "00": "", "01": "临停1H", "02": "停牌", "03": "停牌", "04": "临停",
                #          "05": "停1/2", "07": "暂停", "-1": "无记录", "-2": "未上市", "-3": "退市"
                #lsColNames = ['name', 'open', 'prv_cls', 'now', 'high', 'low', 'bid', 'ask', 'qty', 'amt',
                #              'bsize1', 'bid1', 'bsize2', 'bid2', 'bsize3', 'bid3', 'bsize4', 'bid4', 'bsize5', 'bid5',
                #              'asize1', 'ask1', 'asize2', 'ask2', 'asize3', 'ask3', 'asize4', 'ask4', 'asize5', 'ask5',
                #              'date', 'time', 'status']
                lsColDef = [
                    ('name', 'str'), ('open', 'float'), ('prv_cls', 'float'), ('now', 'float'), ('high', 'float'), 
                    ('low', 'float'), ('bid', 'float'), ('ask', 'float'), ('qty', 'float'), ('amt', 'float'),
                    ('bsize1', 'float'), ('bid1', 'float'), ('bsize2', 'float'), ('bid2', 'float'), ('bsize3', 'float'), 
                    ('bid3', 'float'), ('bsize4', 'float'), ('bid4', 'float'), ('bsize5', 'float'), ('bid5', 'float'),
                    ('asize1', 'float'), ('ask1', 'float'), ('asize2', 'float'), ('ask2', 'float'), ('asize3', 'float'), 
                    ('ask3', 'float'), ('asize4', 'float'), ('ask4', 'float'), ('asize5', 'float'), ('ask5', 'float'),
                    ('date', 'str'), ('time', 'str'), ('status', 'str')
                ]
            elif sCode[:6] == 'CON_OP':    # 期权行情 (e.g. 'CON_OP_10000727')
                # 0.买量 1.买价 2.最新价 3.卖价 4.卖量 5.持仓量 6.涨跌幅(%) 7.行权价 8.昨收价 9.开盘价 10.涨停价 11.跌停价 
                # 12.申卖价五 13.申卖量五 14.申卖价四 15.申卖量四 16.申卖价三 17.申卖量三 18.申卖价二 19.申卖量二 20.申卖价一 21.申卖量一 
                # 22.申买价一 23.申买量一 24.申买价二 25.申买量二 26.申买价三 27.申买量三 28.申买价四 29.申买量四 30.申买价五 31.申买量五 
                # 32.行情时间(yyyy-mm-dd HH:MM:SS) 33.主力合约标识(是1, 否0) 34.状态码(E01, ...) 35.标的证券类型(EBS, ...) 
                # 36.标的股票 37.期权合约简称 38.振幅(%) 39.最高价 40.最低价 41.成交量 42.成交额 43.调整标志(M, A, B, ...)
                lsColDef = [
                    ('bsize', 'float'), ('bid', 'float'), ('now', 'float'), ('ask', 'float'), ('asize', 'float'), ('oi', 'float'), 
                    ('chgp', 'float'), ('strike', 'float'), ('prv_cls', 'float'), ('open', 'float'), ('up_lim', 'float'), ('lo_lim', 'float'),
                    ('ask5', 'float'), ('asize5', 'float'), ('ask4', 'float'), ('asize4', 'float'), ('ask3', 'float'), 
                    ('asize3', 'float'), ('ask2', 'float'), ('asize2', 'float'), ('ask1', 'float'), ('asize1', 'float'),
                    ('bid1', 'float'), ('bsize1', 'float'), ('bid2', 'float'), ('bsize2', 'float'), ('bid3', 'float'), 
                    ('bsize3', 'float'), ('bid4', 'float'), ('bsize4', 'float'), ('bid5', 'float'), ('bsize5', 'float'),
                    ('time', 'str'), ('is_main', 'str'), ('status', 'str'), ('ul_type', 'str'), ('ul_code', 'str'), ('name', 'str'), 
                    ('amp', 'float'), ('high', 'float'), ('low', 'float'), ('qty', 'float'), ('amt', 'float'), ('adj','str')
                ]
            elif sCode[:6] == 'CON_SO':    # 期权扩展行情 (e.g. 'CON_SO_10000727')
                # 0.期权合约简称 1.实值/虚值 2.内在价值 3.时间价值 4.成交量 5.Delta 6.Gamma 7.Theta 8.Vega 9.隐含波动率 
                # 10.最高价 11.最低价 12.交易代码 13.行权价 14.现价 15.理论价值 16.调整标志(M, A, B, ...)
                lsColDef = [
                    ('name', 'float'), ('in_the_money', 'str'), ('intrinsic_value', 'float'), ('time_value', 'float'), 
                    ('qty', 'float'), ('delta', 'float'), ('gamma', 'float'), ('theta', 'float'), ('vega', 'float'), 
                    ('implied_volatility', 'float'), ('high', 'float'), ('low', 'float'), ('trd_code', 'str'), 
                    ('strike', 'float'), ('now', 'float'), ('theory_value', 'float'), ('adj', 'str')
                ]
            #end if
            
            if lsColDef:
                self.dTicker[sCode] = self.genQuoteDict(lsCols, lsColDef)
            else:
                print('Column definition cannot be found for {}'.format(sLine))
        #end for
