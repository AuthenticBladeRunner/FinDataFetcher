'''
Should install pdfminer3k first
Created on 2017年7月18日

@author: tiany
'''

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTRect, LTChar, LTLine

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from collections import defaultdict

# 检测一维坐标轴上两个线段是否有重合 (重合长度小于1不算)
def checkSegOverlap(lower_bound, upper_bound, f_small, f_big, iMinOvl = 1):
    if f_big < lower_bound + iMinOvl or f_small > upper_bound - iMinOvl:
        return False
    return True
#end def

# 计算 重合区域面积
def getOverlapArea(r1, r2):
    x1, y1, x2, y2 = r1
    a1, b1, a2, b2 = r2
    if (x2<a1 or a2<x1 or y2<b1 or b2<y1):
        return 0
    
    l = max(x1, a1)   # left
    b = max(y1, b1)   # bottom
    r = min(x2, a2)   # right
    t = min(y2, b2)   # top
    
    return (r-l) * (t-b)
#end def

# 返回 重合区域 在 r1、r2 的百分比位置
def getOverlapPctPos(r1, r2):
    x1, y1, x2, y2 = r1
    a1, b1, a2, b2 = r2
    if (x2<a1 or a2<x1 or y2<b1 or b2<y1):
        return None
    
    l = max(x1, a1)   # left
    b = max(y1, b1)   # bottom
    r = min(x2, a2)   # right
    t = min(y2, b2)   # top
    
    w1 = x2 - x1    # width of r1
    h2 = b2 - b1    # height of r2
    
    l = (l - x1) / w1  # percentage position of left line in r1
    r = (r - x1) / w1
    b = (b - b1) / h2  # percentage position of bottom line in r2
    t = (t - b1) / h2
    
    return (l, r, b, t)
#end def

class PdfRipper:
    def __init__(self):
        self.fMaxDev = 4      # 可以容忍的最大误差
        self.fExtend = 2        # 把线段向外伸展的长度

    def toText(self, sPdfPath, sTxtPath):
        self.initDoc(sPdfPath)
        
        with open(sTxtPath, 'w', encoding='utf-8') as flTxt:
            for layout in self.lsLayout:
                self.layout = layout
                lsPageLines = self.getPageTextLines()
                for sLine in lsPageLines:
                    flTxt.write(sLine + '\n')
                flTxt.write('\n')       # add a newline for each page end
        #end with
    #end def

    def drawPageRects(self, sPdfPath, iPage):
        self.initDoc(sPdfPath)
        self.layout = self.lsLayout[iPage-1]

        self.genRects()

        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111, aspect='equal')  # 111: nrows, ncols, plot_number
        ax1.set_xlim(self.layout.x0, self.layout.x1)
        ax1.set_ylim(self.layout.y0, self.layout.y1)
        for x0, y0, x1, y1 in self.lsRects:
            ax1.add_patch(
                patches.Rectangle(
                    (x0, y0),       # (x,y)
                    x1 - x0,        # width
                    y1 - y0,        # height
                    fill=False      # no background
                )
            )
        plt.show()
    #end def

    def drawRectsWithTexts(self, sPdfPath, iPage):
        from matplotlib.font_manager import FontProperties
        font = FontProperties(fname=r"C:\Windows\Fonts\msyhl.ttc")  # , size=11

        self.initDoc(sPdfPath)
        self.layout = self.lsLayout[iPage-1]

        self.genRects()

        #plt.rcParams['font.sans-serif'] = ['simhei']    #用来正常显示中文
        #plt.rcParams['axes.unicode_minus'] = False      #用来正常显示负号

        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111, aspect='equal')  # 111: nrows, ncols, plot_number
        ax1.set_xlim(self.layout.x0, self.layout.x1)
        ax1.set_ylim(self.layout.y0, self.layout.y1)
        for x0, y0, x1, y1 in self.lsRects:
            ax1.add_patch(
                patches.Rectangle(
                    (x0, y0),       # (x,y)
                    x1 - x0,        # width
                    y1 - y0,        # height
                    fill=False      # no background
                )
            )
        
        for lt_obj in self.layout:
            if not isinstance(lt_obj, LTTextBox):
                continue
            for xx in lt_obj:
                if not isinstance(xx, LTTextLine):
                    continue
                #dAreaTxt[xx.bbox] = xx.get_text().rstrip('\n')   # 勿使用 strip(), 因为前后的空格有占位的作用
                x0, y0, x1, y1 = xx.bbox
                ax1.add_patch(
                    patches.Rectangle(
                        (x0, y0),       # (x,y)
                        x1 - x0,        # width
                        y1 - y0,        # height
                        fill=False,     # no background
                        color='dimgray'
                    )
                )
                ax1.text(x0, y0, xx.get_text(), fontproperties=font)
        #end for

        plt.show()
    #end def
    
    def drawPageLines(self, sPdfPath, iPage):
        self.initDoc(sPdfPath)
        self.layout = self.lsLayout[iPage-1]

        self.getHVLines()

        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111, aspect='equal')  # 111: nrows, ncols, plot_number
        ax1.set_xlim(self.layout.x0, self.layout.x1)
        ax1.set_ylim(self.layout.y0, self.layout.y1)
        for y, x0, x1 in self.lsHLines:
            plt.plot((x0, x1), (y, y))
        for x, y0, y1 in self.lsVLines:
            plt.plot((x, x), (y0, y1))
        plt.show()
    #end def

    # Generate a list of page layouts
    def initDoc(self, sPdfPath):
        # Open a PDF file.
        fp = open(sPdfPath, 'rb')
        
        # Create a PDF parser object associated with the file object.
        parser = PDFParser(fp)
        doc = PDFDocument()
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize('')
        fp.close()
        
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        self.lsLayout = []
        for page in doc.get_pages():
            interpreter.process_page(page)
            self.lsLayout.append(device.get_result())
        #end for
    #end def
    
    def getPageTextLines(self):
        #self.genLineGroups(self.layout)
        #self.genCornerInfo(self.dX, self.dY)
        #self.genRects(self.dCornerInfo, self.dHCorners, self.dVCorners)
        self.genRects()
        self.reallocTextToRect(self.layout, self.lsRects)
        return self.sortTexts(self.dRectTxt)
    #end def
    
    # 生成当前页面的 横线组 和 竖线组 （延长线段的长度防止它们不相交）
    def getHVLines(self):
        self.lsHLines = []       # 横线
        self.lsVLines = []       # 竖线
        for obj in self.layout:
            # This is very strange: the LTRect objects are actually lines (i.e. very slim or very thin rectangles).
            # The actual rectangles are formed by these lines. Moreover, there are no LTLine objects, all lines are LTRect objects.
            if not isinstance(obj, LTRect):
                continue
            if obj.width < 1 and obj.height < 1:    # Just a dot, ignore it.
                continue

            if obj.height < 1:      # horizontal line 横线
                self.appendLine(self.lsHLines, ((obj.y0 + obj.y1) / 2, obj.x0 - self.fExtend, obj.x1 + self.fExtend) )
            elif obj.width < 1:     # vertical line 竖线
                self.appendLine(self.lsVLines, ((obj.x0 + obj.x1) / 2, obj.y0 - self.fExtend, obj.y1 + self.fExtend) )
        #end for
    #end def

    def appendLine(self, lsLines, tLine):
        y, x0, x1 = tLine
        tJoined = None
        for i in range(0, len(lsLines)):
            b, a0, a1 = lsLines[i]
            if b == y and checkSegOverlap(a0, a1, x0, x1, 0):
                tJoined = (y, min(a0, x0), max(a1, x1))
                break
        #end for
        if tJoined:
            lsLines.pop(i)
            lsLines.append(tJoined)
        else:
            lsLines.append(tLine)
    #end def

    def genCrosses(self):
        self.getHVLines()

        # 交点信息。{ (x,y): {'hline':(y,x0,x1), 'vline':(x,y0,y1)} }。由于之前线段做过合并，因此每个交点只对应两条线段。
        self.dCrosses = {}
        # 各条横线上的交点。{(y,x0,x1): [x_1, x_2, x_3, ...]}
        self.dHlCrs = defaultdict(list)
        # 各条竖线上的交点。{(x,y0,y1): [y_1, y_2, y_3, ...]}
        self.dVlCrs = defaultdict(list)
        
        # 遍历所有横线
        for y, x0, x1 in self.lsHLines:
            # 为每条横线检查一遍所有竖线，看有没有与之相交的
            for x, y0, y1 in self.lsVLines:
                if (x < x0) or (x > x1):
                    continue    # 如果竖线在横线的左边或右边，则不可能相交，跳过
                if (y < y0) or (y > y1):
                    continue    # 如果横线在竖线的下方或上方，则不可能相交，跳过
                # 记录交点信息
                self.dCrosses[(x,y)] = {'hline':(y,x0,x1), 'vline':(x,y0,y1)}
                self.dHlCrs[(y,x0,x1)].append(x)
                self.dVlCrs[(x,y0,y1)].append(y)
            #end for
        #end for

        # 各条线上的交点按顺序排列
        for t, ls in self.dHlCrs.items():
            self.dHlCrs[t] = sorted(ls)
        for t, ls in self.dVlCrs.items():
            self.dVlCrs[t] = sorted(ls)
    #end def

    def genRects(self):
        self.genCrosses()

        self.lsRects = []
        for t in self.dCrosses:
            tRect = self.findRect(t)
            if tRect:
                self.lsRects.append(tRect)
        #end for
    #end def

    # 找到以指定点为左下角的最小矩形
    def findRect(self, tLowerLeft):
        tRect = None
        x0, y0 = tLowerLeft              # 左下角坐标
        tLftVl = self.dCrosses[tLowerLeft]['vline']                 # 该交点所在的竖线
        lsY    = self.dVlCrs[tLftVl]     # 该横线上所有的交点
        if lsY.index(y0) >= len(lsY) - 1:   # 如果该点是竖线最上方的点
            return tRect
        tLwrHl = self.dCrosses[tLowerLeft]['hline']                 # 该交点所在的横线
        lsX    = self.dHlCrs[tLwrHl]     # 该横线上所有的交点
        # 从本交点右侧开始寻找向上的直线
        for i in range(lsX.index(x0) + 1, len(lsX)):
            x1 = lsX[i]
            tRgtVl = self.dCrosses[(x1, y0)]['vline']       # 右边的竖线
            lsR    = self.dVlCrs[tRgtVl]
            for j in range(lsR.index(y0) + 1, len(lsR)):
                y1 = lsR[j]
                tUprHl = self.dCrosses[(x1, y1)]['hline']
                lsU = self.dHlCrs[tUprHl]
                k = lsU.index(x1)
                if k > 0:       # 不是上方横线最左边的点
                    return (x0, y0, x1, y1)
            #end for
        #end for
        return tRect
    #end def
    
    # 根据文本所在单元格重新设置文本的位置
    def reallocTextToRect(self, layout, lsRects):
        # 根据页面信息 生成 文本所占区域:文本内容. 即 dAreaTxt[(x0, y0, x1, y1)] = sText
        dAreaTxt = {}
        for lt_obj in layout:
            if isinstance(lt_obj, LTTextBox):
                for xx in lt_obj:
                    if isinstance(xx, LTTextLine):
                        dAreaTxt[xx.bbox] = xx.get_text().rstrip('\n')   # 勿使用 strip(), 因为前后的空格有占位的作用
        #end for
        
        self.dRectTxt = {}
        for r1, sTxt in dAreaTxt.items():
            bFound = False
            for r2 in lsRects:
                '''
                fOvlArea = getOverlapArea(r1, r2)
                if fOvlArea > 0:
                    fTxtArea = (r1[2] - r1[0]) * (r1[3] - r1[1])
                    fOvlPctg = fOvlArea/fTxtArea
                    print('"{}" is {:.2%} overlapped with area {}'.format(sTxt, fOvlArea/fTxtArea, r2))
                '''
                tOvlPos = getOverlapPctPos(r1, r2)
                if tOvlPos:    # 能找到有重合部分的表格单元格
                    bFound = True
                    l, r, b, t = tOvlPos
                    #nLen = len(sTxt)
                    #il = round(nLen * l)
                    #ir = round(nLen * r)
                    il = self.findNearSpaceIndex(sTxt, l)
                    ir = self.findNearSpaceIndex(sTxt, r)
                    #print('"{}" is {:.2%} overlapped with area {}\n\t\t\t{}'.format(sTxt, min(r-l, t-b), r2, sTxt[il:ir].strip()))
                    tInf = (b, sTxt[il:ir])   # b: 垂直位置  .strip()
                    if r2 in self.dRectTxt:
                        self.dRectTxt[r2].append( tInf )
                    else:
                        self.dRectTxt[r2] = [ tInf ]
            #end for
            
            if not bFound:    # 找不到相交的单元格，即，文本不属于表格
                self.dRectTxt[r1] = sTxt
                #pass
        #end for
        
        # 合并处于同一单元格的文本
        for r, v in self.dRectTxt.items():
            if type(v) is list:
                slTp = sorted(v, key = lambda x: x[0], reverse = True)
                sConcat = ''.join(x[1] for x in slTp)
                self.dRectTxt[r] = sConcat
    #end def
    
    # 按从左至右、从上至下的方式排列文本
    def sortTexts(self, dTxt):
        dGrp = {}    # { i: {'range': (y0, y1), 'list': [(r, sTxt), ...]} }
        iGrp = 0
        for tInf in dTxt.items():
            r, sTxt = tInf
            x0, y0, x1, y1 = r
            bFound = False
            # 找到所属行
            for iKey, dVal in dGrp.items():
                tRng = dVal['range']
                if checkSegOverlap(tRng[0], tRng[1], y0, y1, 2):
                    dVal['list'].append(tInf)
                    dVal['range'] = (min(tRng[0], y0), max(tRng[1], y1))
                    bFound = True
                    break
            #end for
            if not bFound:
                dVal = {}
                dVal['range'] = (y0, y1)
                dVal['list'] = [tInf]
                iGrp += 1
                dGrp[iGrp] = dVal
        #end for
        
        # 每行行内从左到右排列
        for dVal in dGrp.values():
            dVal['list'] = sorted(dVal['list'], key = lambda t: t[0][0])
        
        # 所有行从上到下排列
        lsLineInfo = sorted(dGrp.values(), key = lambda d: d['range'][0], reverse=True)
        
        lsLineText = []
        for dLine in lsLineInfo:
            lsCols = dLine['list']
            lsLineText.append('\t'.join(t[1] for t in lsCols))
        
        return lsLineText
    #end def
    
    # 找到字符串中离指定位置最近的 空格 字符
    def findNearSpaceIndex(self, s, fRatio):
        nLen = len(s)
        i = round(nLen * fRatio)
        if i >= nLen or i <= 0:
            return i
        if s[i] == ' ':
            return i
        # i1 往左搜寻, i2 往右搜寻
        i1 = i - 1
        i2 = i + 1
        while i1 >= 0 or i2 < nLen:
            if i1 >= 0:
                if s[i1] == ' ':
                    return i1
                i1 -= 1
            if i2 <= nLen - 1:
                if s[i2] == ' ':
                    return i2
                i2 += 1
        #end while
        return i
    #end def

#end class            

if __name__ == '__main__':
    #pdfrp = PdfRipper()
    #pdfrp.drawPageRects(r'D:\Downloads\Documents\161115.pdf', 9)
    #pdfrp.drawPageRects(r'C:\workspace\python\TradeBot\reports\2017s2\pdf\165509.pdf', 7)
    #pdfrp.drawPageLines(r'D:\Downloads\Documents\165509.pdf', 9)
    #pdfrp.drawPageLines(r'C:\workspace\python\TradeBot\reports\2017s2\pdf\161125.pdf', 11)

    #pdfrp.drawRectsWithTexts(r'D:\Downloads\Documents\161115.pdf', 9)
    #pdfrp.toText(r'D:\Downloads\Documents\161115.pdf', r'D:\Downloads\Documents\161115.txt')

    import sys
    import time

    for f in range(10):
        #delete "\r" to append instead of overwrite
        sys.stdout.write("\r")
        sys.stdout.flush()
        sys.stdout.write(str(f))
        time.sleep(1)

    '''
    import os
    sPdfDir = r'C:\workspace\python\PriceCompare\temp\2017s02\pdf'
    os.chdir(sPdfDir)
    sTxtDir = '../txt'
    pdfrp = PdfReaper()
    lsFiles = os.listdir()
    i = 0
    for sSrcFile in lsFiles:
        i += 1
        if sSrcFile[-3:].lower() != 'pdf':
            continue
        print('Converting {} {:.2%}...'.format(sSrcFile, i/len(lsFiles)))
        sPrefix = sSrcFile[:-4]
        pdfrp.toText(sSrcFile, '{}/{}.txt'.format(sTxtDir, sPrefix))
    pass
    '''