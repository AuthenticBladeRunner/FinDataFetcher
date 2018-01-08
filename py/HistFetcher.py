'''
Historical quotes/NAVs, etc...
Created on 2017年7月11日

@author: tiany
'''

import re
from UtilFunc import *

# 获取历史净值也可以从这儿获取：http://www.cninfo.com.cn/information/fund/netvalue/163113.html
# 从TTJJ获取基金的历史净值和涨跌幅（%）。返回历史净值字典
def getFundHisNavChg(sFundCode, sFromDate = '', sToDate = ''):
    if len(sFromDate) == 8:
        sFromDate = addDashToDate(sFromDate)
    #end if
    if len(sToDate) == 8:
        sToDate = addDashToDate(sToDate)
    #end if
    # Monetary fund example: http://fund.eastmoney.com/f10/jjjz_519888.html
    # per后面是指一页显示多少条数据
    sUrl = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={}&page=1&per=5000&sdate={}&edate={}'.format(
            sFundCode, sFromDate, sToDate)
    sCont = getWebContent(sUrl)
    
    # The returned data is like:
    #     var apidata={ content:"<table class='w782 comm lsjz'> ... </table>",records:15,pages:1,curpage:1};
    rexHeader = re.compile('>([^<]*?)</th>')
    rexRow  = re.compile('<tr>(.*?)</tr>')
    rexCol  = re.compile('<td.*?>(.*?)</td>')
    
    # 列名
    lsHeader = rexHeader.findall(sCont)
    nHeaderNum = len(lsHeader)
    
    lsRows = rexRow.findall(sCont)
    dHisNav = {}
    for sRowSrc in lsRows:
        lsCols = rexCol.findall(sRowSrc)
        nColNum = len(lsCols)
        if nColNum < 2: continue
        nColNum = min(nColNum, nHeaderNum)
        dRow = {}
        sNavDate = ''
        for i in range(0, nColNum):
            sHeader = lsHeader[i]
            val = lsCols[i]
            
            if '日期' in sHeader:
                sNavDate = val.replace('-', '')
            elif '份收益' in sHeader:     # 每(百)万份收益
                sHeader = '每万元收益'
                val = float(val)
            elif '日年化收益率' in sHeader:
                sHeader = '七日年化收益率'
                val = float(val.replace('%', ''))
            elif ('单位净值' in sHeader) or ('累计净值' in sHeader):
                val = float(val)
            elif '日增长率' in sHeader:
                val = float(val.replace('%', ''))
            
            dRow[sHeader] = val
        #end for
        dHisNav[(sNavDate, sFundCode)] = dRow
    #end for
    return dHisNav
#end def

def getCnHisQuoteFromTuShare(sSinaCode, start = '', end = '', adj = True):
    import tushare as ts
    sCode = sSinaCode[-6:]
    if adj:
        return ts.get_h_data(sCode, start, end)
    else:
        return ts.get_k_data(sCode, start, end)
#end def


if __name__ == '__main__':
    print(getFundHisNavChg('502010', '2017-07-07', '2017-07-11'))
    