'''
Should install pdfminer3k first
Created on 2017年7月18日

@author: tiany
'''

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTRect, LTChar

# 检测一维坐标轴上两个线段是否有重合 (重合长度小于1不算)
def checkSegOverlap(lower_bound, upper_bound, f_small, f_big):
    iMinOvl = 1
    if f_big <= lower_bound + iMinOvl or f_small >= upper_bound - iMinOvl:
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

class PdfReaper:
    def toText(self, sPdfPath, sTxtPath):
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
        
        with open(sTxtPath, 'w', encoding='utf-8') as flTxt:
            i = 0
            for page in doc.get_pages():
                i += 1
                interpreter.process_page(page)
                self.layout = device.get_result()
                lsPageLines = self.getPageTextLines()
                for sLine in lsPageLines:
                    flTxt.write(sLine + '\n')
                flTxt.write('\n')       # add a newline for each page end
        #end with
    #end def
    
    def getPageTextLines(self):
        self.genLineGroups(self.layout)
        self.genCornerInfo(self.dX, self.dY)
        self.genRects(self.dCornerInfo, self.dHCorners, self.dVCorners)
        self.reallocTextToRect(self.layout, self.lsRects)
        return self.sortTexts(self.dRectTxt)
    
    # 根据页面信息 生成 按照 x 坐标分类的 横线, 以及 按照 y 坐标分类的 竖线
    def genLineGroups(self, layout):
        i = 0
        self.dX = {}    # 按照 x 坐标分类的 横线
        self.dY = {}    # 按照 y 坐标分类的 竖线
        lsX = []    # 所有可能的x坐标
        lsY = []
        #lsVLines = []
        #lsHLines = []
        #lsRects = []
        #dCorners = {}
        for lt_obj in layout:
            #print(type(lt_obj))
            if isinstance(lt_obj, LTRect):
                if lt_obj.width < 1 and lt_obj.height < 1:
                    continue
                i += 1
                #print(lt_obj.width, lt_obj.height)
                #x0 = getNearbyNumber(lsX, lt_obj.x0)
                #y0 = getNearbyNumber(lsY, lt_obj.y0)
                if lt_obj.width < 1:      # vertical line 竖线
                    #y1 = getNearbyNumber(lsY, lt_obj.y1)
                    #lsVLines.append( (x0, y0, x0, y1) )
                    #addCornerInfo(dCorners, (x0, y0, x0, y1))
                    self.addStdLineToGroup( self.dX, self.getNearbyNumber(lsX, lt_obj.x0), 
                                            self.getNearbyNumber(lsY, lt_obj.y0), self.getNearbyNumber(lsY, lt_obj.y1) )
                elif lt_obj.height < 1:   # horizontal line
                    #x1 = getNearbyNumber(lsX, lt_obj.x1)
                    #lsHLines.append( (x0, y0, x1, y0) )
                    #addCornerInfo(dCorners, (x0, y0, x1, y0))
                    self.addStdLineToGroup( self.dY, self.getNearbyNumber(lsY, lt_obj.y0), 
                                            self.getNearbyNumber(lsX, lt_obj.x0), self.getNearbyNumber(lsX, lt_obj.x1) )
                else:
                    #x1 = getNearbyNumber(lsX, lt_obj.x1)
                    #y1 = getNearbyNumber(lsY, lt_obj.y1)
                    #lsRects.append( (x0, y0, x1, y1) )
                    pass
        #end for
    #end def
    
    # 根据横竖线列表 生成所有交点信息
    def genCornerInfo(self, dX, dY):
        self.dCornerInfo = {}  # 交点的相交信息
        self.dHCorners = {}    # 按横线（y坐标）归类的交点
        self.dVCorners = {}    # 按竖线（x坐标）归类的交点
        # 遍历所有横线
        for y, lsH in dY.items():
            for x0, x1 in lsH:
                # 遍历所有竖线
                for x, lsV in dX.items():
                    if (x < x0) or (x > x1):
                        if x > x0-1 and x < x1 + 1:
                            print(x, x0, x1)
                        continue    # 如果竖线的 x 坐标不在横线范围内，则不可能相交
                    for y0, y1 in lsV:
                        if (y < y0) or (y > y1):
                            continue    # 如果横线的 y 坐标不在竖线范围内，则不可能相交
                        
                        stCrosses = set()
                        
                        if y < y1:
                            stCrosses.add('u')
                        if y > y0:
                            stCrosses.add('d')
                        if x < x1:
                            stCrosses.add('r')
                        if x > x0:
                            stCrosses.add('l')
                        
                        self.addCornerInfo(self.dCornerInfo, (x, y), stCrosses)
                        self.addCorner(self.dHCorners, y, x)
                        self.addCorner(self.dVCorners, x, y)
                        
        #end for
        
        # 给按横（纵）坐标归类的交点进行组内排序
        for y in self.dHCorners:
            self.dHCorners[y] = sorted(self.dHCorners[y])
        for x in self.dVCorners:
            self.dVCorners[x] = sorted(self.dVCorners[x])
    #end def
    
    # 根据所有交点信息 生成所有(最小)矩形列表
    def genRects(self, dCornerInfo, dHCorners, dVCorners):
        self.lsRects = []
        for tPoint, stCrosses in dCornerInfo.items():
            # 从左下角开始形成矩形
            if ('u' in stCrosses) and ('r' in stCrosses):
                x0, y0 = tPoint
                # 先往右找到右下角顶点
                lsH = dHCorners[y0]
                bFound = False
                for i in range(lsH.index(x0)+1, len(lsH)):
                    x1 = lsH[i]
                    stCrs = dCornerInfo[(x1, y0)]
                    if 'l' not in stCrs:
                        break    # 横线中间有断裂
                    if ('l' in stCrs) and ('u' in stCrs):
                        bFound = True
                        break
                if bFound:    # 找到了右下角的顶点
                    # 接着往上找右上角顶点
                    lsV = dVCorners[x1]
                    bFound = False
                    for i in range(lsV.index(y0)+1, len(lsV)):
                        y1 = lsV[i]
                        stCrs = dCornerInfo[(x1, y1)]
                        if 'd' not in stCrs:
                            break    # 竖线中间有断裂
                        if ('d' in stCrs) and ('l' in stCrs):
                            bFound = True
                            break
                if bFound:    # 找到了右上角的顶点
                    self.lsRects.append( (x0, y0, x1, y1) )
        #end for
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
                    tInf = (b, sTxt[il:ir].strip())   # b: 垂直位置
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
                if checkSegOverlap(tRng[0], tRng[1], y0, y1):
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
    
    # Find a nearby number in a list. 如果找不到相近的，那就增加一个新的到列表中去
    def getNearbyNumber(self, lsX, x):
        for xi in lsX:
            # 如果误差在 1 内，则认为是相近的点
            if x > xi - 1 and x < xi + 1:
                return xi
    
        # 如果找不到相近的，那就增加一个新的到列表中去
        lsX.append(x)    
        return x
    #end def

    # 把(标准化后的)竖线加到相应的 x 坐标组去 (或把横线加到相应的 y 坐标组中去)
    def addStdLineToGroup(self, dX, x, y0, y1):
        if x in dX:
            dX[x].append( (y0, y1) )
        else:
            dX[x] = [ (y0, y1) ]
    #end def
    
    # 新增交点信息
    def addCornerInfo(self, dCornerInfo, tPoint, stCrosses):
        if tPoint in dCornerInfo:
            dCornerInfo[tPoint].update(stCrosses)
        else:
            dCornerInfo[tPoint] = stCrosses
    #end def
    
    # 把交点 x 坐标加入到按 y 坐标分类的字典中 (或 把交点 y 坐标 加入到按 x 坐标分类的字典中)
    def addCorner(self, dH, y, x):
        if y in dH:
            dH[y].add(x)
        else:
            dH[y] = {x}
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
    import os
    sPdfDir = r'C:\workspace\python\PriceCompare\temp\2017s02\pdf'
    os.chdir(sPdfDir)
    sTxtDir = '../txt'
    pdfrp = PdfReaper()
    for sSrcFile in os.listdir():
        if sSrcFile[-3:].lower() != 'pdf':
            continue
        print('Converting {}...'.format(sSrcFile))
        sPrefix = sSrcFile[:-4]
        pdfrp.toText(sSrcFile, '{}/{}.txt'.format(sTxtDir, sPrefix))
    pass