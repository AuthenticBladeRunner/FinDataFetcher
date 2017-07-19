'''
Utility method set
Created on 2017年6月29日
@author: tiany
'''

import ast
import requests
from collections import OrderedDict, defaultdict
from pprint import saferepr

def addDashToDate(s, sDash = '-'):
    return s[:4] + sDash + s[4:6] + sDash + s[6:8]

def getWebContent(sUrl, sEncoding=None, dParam=None, **kwargs):
    # http://docs.python-requests.org/en/master/api/#main-interface
    r = requests.get(sUrl, dParam, **kwargs)
    if sEncoding:
        r.encoding = sEncoding
    return r.text
#end def

# 把每行的 (XX, YY) 作为 key, value 对加入到 dict 中去
def readTuplesToDict(sFileName, sEncoding = 'utf-8', sType = 'dict'):
    ls = []
    with open(sFileName, 'r', encoding = sEncoding, errors = 'ignore') as fl:
        for s in fl.readlines():
            s = s.strip()
            if s == '': continue
            if s[0] == '#': continue    # Ignore comments
            t = ast.literal_eval(s)
            ls.append(t)
        #end for
    #end with

    if sType == 'OrderedDict':
        return OrderedDict(ls)
    elif sType == 'ListDict':
        return defaultdict(list, ls)
    elif sType == 'DictDict':
        return defaultdict(dict, ls)
    else:
        return dict(ls)
#def

def writeTupleDict(d, sFileName, sEncoding = 'utf-8', bReverse = False):
    ls = sorted(d.items(), key = lambda t:t[0], reverse = bReverse)
    with open(sFileName, 'w', encoding = sEncoding, errors = 'ignore') as fl:
        for item in ls:
            #sLine = repr(item)
            sLine = saferepr(item)
            print(sLine, file = fl)
        #end for
    #end with
#def

# Test codes:
if __name__ == '__main__':
    sUrl = 'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code=519888&page=1&per=5000&sdate=2017-06-25&edate=2017-07-11'
    print(getWebContent(sUrl))
    