'''
Created on Jan 20, 2010

@author: Roland Kaminski
'''

from zipfile import ZipFile
from StringIO import StringIO
import __builtin__
import math
from benchmarktool import tools 

class Spreadsheet:
    def __init__(self, benchmark, columns, measures):
        self.instSheet  = InstanceTable(benchmark, columns, measures, "ta1")
        self.classSheet = None
        
    def finish(self):
        self.instSheet.finish()
        self.classSheet = self.instSheet.classTable()
        
    def printSheet(self, out):
        zipFile = ZipFile(out, "w")
        out = StringIO()
        
        out.write('''\
<?xml version="1.0" encoding="UTF-8"?>\
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" xmlns:math="http://www.w3.org/1998/Math/MathML" xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" xmlns:ooo="http://openoffice.org/2004/office" xmlns:ooow="http://openoffice.org/2004/writer" xmlns:oooc="http://openoffice.org/2004/calc" xmlns:dom="http://www.w3.org/2001/xml-events" xmlns:xforms="http://www.w3.org/2002/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:rpt="http://openoffice.org/2005/report" xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" xmlns:rdfa="http://docs.oasis-open.org/opendocument/meta/rdfa#" xmlns:field="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:field:1.0" xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" office:version="1.2">\
<office:scripts/>\
<office:font-face-decls>\
<style:font-face style:name="Liberation Sans" svg:font-family="'Liberation Sans'" style:font-family-generic="swiss" style:font-pitch="variable"/>\
<style:font-face style:name="DejaVu Sans" svg:font-family="'DejaVu Sans'" style:font-family-generic="system" style:font-pitch="variable"/>\
</office:font-face-decls>\
<office:automatic-styles>\
''')
        for sheet in [self.instSheet, self.classSheet]:
            for i in range(0, len(sheet.cowidth)):
                out.write('''\
<style:style style:name="{0}co{1}" style:family="table-column">\
<style:table-column-properties fo:break-before="auto" style:column-width="{2}in"/>\
</style:style>\
'''.format(sheet.name, i + 1, sheet.cowidth[i]))

        out.write('''\
<style:style style:name="ro1" style:family="table-row">\
<style:table-row-properties style:row-height="0.178in" fo:break-before="auto" style:use-optimal-row-height="true"/>\
</style:style>\
<style:style style:name="ta1" style:family="table" style:master-page-name="Default">\
<style:table-properties table:display="true" style:writing-mode="lr-tb"/>\
</style:style>\
</office:automatic-styles>\
<office:body>\
<office:spreadsheet>''')
        
        self.instSheet.printSheet(out, "Instances")
        self.classSheet.printSheet(out, "Classes")
        out.write('''</office:spreadsheet></office:body></office:document-content>''')
        zipFile.writestr("mimetype", '''application/vnd.oasis.opendocument.spreadsheet''')
        zipFile.writestr("content.xml", out.getvalue())
        zipFile.writestr("META-INF/manifest.xml", '''\
<?xml version="1.0" encoding="UTF-8"?>\
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">\
<manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.spreadsheet" manifest:version="1.2" manifest:full-path="/"/>\
<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>\
<manifest:file-entry manifest:media-type="text/xml" manifest:full-path="styles.xml"/>\
</manifest:manifest>\
''')

        zipFile.writestr("styles.xml", '''\
<?xml version="1.0" encoding="UTF-8"?>\
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" xmlns:math="http://www.w3.org/1998/Math/MathML" xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" xmlns:ooo="http://openoffice.org/2004/office" xmlns:ooow="http://openoffice.org/2004/writer" xmlns:oooc="http://openoffice.org/2004/calc" xmlns:dom="http://www.w3.org/2001/xml-events" xmlns:rpt="http://openoffice.org/2005/report" xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" xmlns:rdfa="http://docs.oasis-open.org/opendocument/meta/rdfa#" office:version="1.2">\
<office:styles>\
<style:style style:name="Default" style:family="table-cell"/>\
<style:style style:name="cellBest" style:family="table-cell" style:parent-style-name="Default">\
<style:table-cell-properties fo:background-color="#00ff00"/>\
</style:style>\
<style:style style:name="cellWorst" style:family="table-cell" style:parent-style-name="Default">\
<style:table-cell-properties fo:background-color="#ff0000"/>\
</style:style>\
</office:styles>\
</office:document-styles>\
''')
        zipFile.close()
        
    def addRunspec(self, runspec):
        self.instSheet.addRunspec(runspec)
        
class Cell:
    def __init__(self):
        self.style = None
    def protect(self, val):
        return val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class StringCell(Cell):
    def __init__(self, val):
        Cell.__init__(self)
        self.val = val
    
    def printSheet(self, out):
        out.write('<table:table-cell office:value-type="string"><text:p>{0}</text:p></table:table-cell>'.format(self.protect(self.val)))

class FloatCell(Cell):
    def __init__(self, val):
        Cell.__init__(self)
        self.val = val
    
    def printSheet(self, out):
        if self.style != None:
            style = ' table:style-name="{0}"'.format(self.style)
        else:
            style = ""
        out.write('<table:table-cell{1} office:value-type="float" office:value="{0}"/>'.format(self.val, style))

class FormulaCell(Cell):
    def __init__(self, val, arrayForm = False):
        Cell.__init__(self)
        self.val       = val
        self.arrayForm = arrayForm
    
    def printSheet(self, out):
        extra = ""
        if self.style != None:
            extra += ' table:style-name="{0}"'.format(self.style)
        if self.arrayForm:
            extra += ' table:number-matrix-columns-spanned="1" table:number-matrix-rows-spanned="1"'
        out.write('<table:table-cell{1} table:formula="{0}" office:value-type="float"/>'.format(self.protect(self.val), extra))

class Table:
    def __init__(self, name):
        self.content = []
        self.cowidth = []
        self.name    = "ta1" 
    
    def add(self, row, col, cell):
        # estimate some "good" column width 
        while len(self.cowidth) <= col + 1:
            self.cowidth.append(0.8925)
        if cell.__class__ == StringCell:
            self.cowidth[col] = max(self.cowidth[col], len(cell.val) * 0.07)
        while len(self.content) <= row: 
            self.content.append([])
        rowRef = self.content[row]
        while len(rowRef) <= col:
            rowRef.append(None)
        rowRef[col] = cell

    def get(self, row, col):
        return self.content[row][col]
        
    def cellIndex(self, row, col, absCol = False, absRow = False):
        radix = ord("Z") - ord("A") + 1
        ret   = ""
        while col >= 0:
            rem = col % radix
            ret = chr(rem + ord("A")) + ret
            col = col / radix - 1
        if absCol: preCol = "$"
        else: preCol = ""
        if absRow: preRow = "$"
        else: preRow = ""
        return preCol + ret + preRow + str(row + 1)

    def printSheet(self, out, name):
        out.write('<table:table table:name="{0}" table:style-name="ta1" table:print="false">'.format(name))
        for i in range(0, len(self.cowidth)):
            out.write('''<table:table-column table:style-name="{0}co{1}" table:default-cell-style-name="Default"/>'''.format(self.name, i + 1))
        for row in self.content:
            out.write('<table:table-row table:style-name="ro1">')
            for cell in row:
                if cell == None:
                    out.write('<table:table-cell office:value-type="string"><text:p></text:p></table:table-cell>')
                else:
                    cell.printSheet(out)
            out.write('</table:table-row>')
        out.write('</table:table>')

class ValueRows:
    def __init__(self, highlight):
        self.highlight = highlight
        self.list      = {}
    
    def __iter__(self):
        for name, valList in self.list.items():
            if name in self.highlight:
                func = self.highlight[name]
                for line in range(0, len(valList)):
                    row = sorted(valList[line])
                    if len(row) > 1:
                        minimum = row[0][0]
                        median  = tools.medianSorted(map(lambda x: x[0], row))
                        maximum = row[-1][0]
                        green   = []
                        red     = []
                        if func == "t":
                            if maximum - minimum > 2:
                                for value, col in row:
                                    if value <= minimum and value < median:
                                        green.append(col)
                                    else:
                                        break 
                            if maximum - median > 2:
                                for value, col in reversed(row):
                                    if value >= maximum and value > median:
                                        red.append(col)
                                    else:
                                        break
                        elif func == "to":
                            if maximum - minimum > 0:
                                for value, col in row:
                                    if value <= minimum and value < median:   
                                        green.append(col)
                                    else:
                                        break 
                            for value, col in reversed(row):
                                if value > median and value >= maximum:   
                                    red.append(col)
                                else:
                                    break
                        yield name, line, green, red
   
    def add(self, name, val, line, col):
        if not name in self.list: self.list[name] = []
        valList =  self.list[name]
        while len(valList) <= line: valList.append([])  
        valList[line].append((val,col))
    
    def map(self, name, line, func):
        if not name in self.list: 
            return None
        if line >= len(self.list[name]):
            return None
        if len(self.list[name][line]) == 0:
            return None
        return func(map(lambda x: x[0], self.list[name][line]))

class InstanceTable(Table):
    def __init__(self, benchmark, columns, measures, name):
        Table.__init__(self, name)
        self.benchmark = benchmark
        self.columns   = columns
        self.results   = {}
        self.measures  = measures
        self.lines     = 0
        self.machines  = set()
        self.lastcol   = None
        row = 2
        for instance in self.benchmark.list:
            instance = instance.values()[0]
            self.add(row, 0, StringCell(instance.benchclass.name + "/" + instance.name))
            row += instance.maxRuns
            self.lines += instance.maxRuns
        
        self.resultOffset = row
        self.add(self.resultOffset + 1, 0, StringCell("SUM"))
        self.add(self.resultOffset + 2, 0, StringCell("AVG"))
        self.add(self.resultOffset + 3, 0, StringCell("DEV"))
        self.add(self.resultOffset + 4, 0, StringCell("DST"))
        self.add(self.resultOffset + 5, 0, StringCell("BEST"))
        self.add(self.resultOffset + 6, 0, StringCell("BETTER"))
        self.add(self.resultOffset + 7, 0, StringCell("WORSE"))
        self.add(self.resultOffset + 8, 0, StringCell("WORST"))
    
    def addFooter(self, col):
        self.add(self.resultOffset + 1, col, FormulaCell("of:=SUM([.{0}:.{1}])".format(self.cellIndex(2, col), self.cellIndex(self.resultOffset - 1, col))))
        self.add(self.resultOffset + 2, col, FormulaCell("of:=AVERAGE([.{0}:.{1}])".format(self.cellIndex(2, col), self.cellIndex(self.resultOffset - 1, col))))
        self.add(self.resultOffset + 3, col, FormulaCell("of:=STDEV([.{0}:.{1}])".format(self.cellIndex(2, col), self.cellIndex(self.resultOffset - 1, col))))
    
    def finish(self):
        col = 1
        floatOccur = {}
        valueRows = ValueRows(dict(self.measures))
        # generate all columns
        for column in sorted(self.columns.columns):
            if self.measures == "": 
                measures = sorted(column.width)
            else: 
                measures = map(lambda x: x[0], self.measures)
            column.offset = col
            self.add(0, col, StringCell(column.genName(len(self.machines) > 1)))
            add = 0
            for name in measures:
                if name in column.content:
                    self.add(1, column.offset + add, StringCell(name))
                    column.offsets[name] = column.offset + add
                    content = column.content[name]
                    for line in range(0, len(content)):
                        value = content[line]
                        if value.__class__ == __builtin__.float:
                            self.add(2 + line, column.offset + add, FloatCell(value))
                            valueRows.add(name, value, line, column.offset + add)
                        else:
                            self.add(2 + line, column.offset + add, StringCell(value))
                    if column.type[name] == "float":
                        if not name in floatOccur: 
                            floatOccur[name] = set() 
                        floatOccur[name].add(col + add)
                        self.addFooter(col + add)
                    add += 1
            if add == 0: add = 1    
            col += add
        
        self.lastcol  = col
        resultColumns = []
        for colName in ["min", "median", "max"]:
            column = Column(None, None)
            column .offset = col
            self.add(0, col, StringCell(colName))
            resultColumns.append(column)
            for name in measures:
                if name in floatOccur:
                    self.add(1, col, StringCell(name))
                    for row in xrange(2, self.resultOffset):
                        minRange = ""
                        for colRef in sorted(floatOccur[name]):
                            if minRange != "": 
                                minRange += ";" 
                            minRange += "[.{0}]".format(self.cellIndex(row, colRef, True))
                        self.add(row, col, FormulaCell("of:={1}({0})".format(minRange, colName.upper())))
                        self.addFooter(col)
                        if colName == "min":      column.addCell(row - 2, name, "float", valueRows.map(name, row - 2, min))
                        elif colName == "median": column.addCell(row - 2, name, "float", valueRows.map(name, row - 2, tools.median))
                        elif colName == "max":    column.addCell(row - 2, name, "float", valueRows.map(name, row - 2, max))
                    for colRef in sorted(floatOccur[name]):
                        if colName == "min":
                            self.add(
                                self.resultOffset + 4, 
                                colRef, 
                                FormulaCell(
                                    "of:=SUM(([.{0}:.{1}]-[.{2}:.{3}])^2)^0.5".format(
                                        self.cellIndex(2, colRef), 
                                        self.cellIndex(self.resultOffset - 1, colRef), 
                                        self.cellIndex(2, col, True), 
                                        self.cellIndex(self.resultOffset - 1, col, True)), 
                                    True))
                            self.add(
                                self.resultOffset + 5, 
                                colRef, 
                                FormulaCell(
                                    "of:=SUM([.{0}:.{1}]=[.{2}:.{3}])".format(
                                        self.cellIndex(2, colRef), 
                                        self.cellIndex(self.resultOffset - 1, colRef), 
                                        self.cellIndex(2, col, True), 
                                        self.cellIndex(self.resultOffset - 1, col, True)), 
                                    True))
                        elif colName == "median":
                            self.add(
                                    self.resultOffset + 6, 
                                    colRef, 
                                    FormulaCell(
                                        "of:=SUM([.{0}:.{1}]<[.{2}:.{3}])".format(
                                            self.cellIndex(2, colRef), 
                                            self.cellIndex(self.resultOffset - 1, colRef), 
                                            self.cellIndex(2, col, True), 
                                            self.cellIndex(self.resultOffset - 1, col, True)), 
                                        True))
                            self.add(
                                    self.resultOffset + 7, 
                                    colRef, 
                                    FormulaCell(
                                        "of:=SUM([.{0}:.{1}]>[.{2}:.{3}])".format(
                                            self.cellIndex(2, colRef), 
                                            self.cellIndex(self.resultOffset - 1, colRef), 
                                            self.cellIndex(2, col, True), 
                                            self.cellIndex(self.resultOffset - 1, col, True)), 
                                        True))
                        elif colName == "max":
                            self.add(
                                    self.resultOffset + 8, 
                                    colRef, 
                                    FormulaCell(
                                        "of:=SUM([.{0}:.{1}]=[.{2}:.{3}])".format(
                                            self.cellIndex(2, colRef), 
                                            self.cellIndex(self.resultOffset - 1, colRef), 
                                            self.cellIndex(2, col, True), 
                                            self.cellIndex(self.resultOffset - 1, col, True)), 
                                        True))
                    col+= 1
            column.calcSummary(self.resultOffset - 2, [])
        
        # calc values for the footers
        for column in self.columns.columns:
            column.calcSummary(self.resultOffset - 2, resultColumns)
            for name, summary in column.summary.items():
                valueRows.add(name, summary.sum, self.resultOffset - 2 + 1, column.offsets[name])
                valueRows.add(name, summary.avg, self.resultOffset - 2 + 2, column.offsets[name])
                valueRows.add(name, summary.dev, self.resultOffset - 2 + 3, column.offsets[name])
                valueRows.add(name, summary.dst, self.resultOffset - 2 + 4, column.offsets[name])
                valueRows.add(name, -summary.best, self.resultOffset - 2 + 5, column.offsets[name])
                valueRows.add(name, -summary.better, self.resultOffset - 2 + 6, column.offsets[name])
                valueRows.add(name, summary.worse, self.resultOffset - 2 + 7, column.offsets[name])
                valueRows.add(name, summary.worst, self.resultOffset - 2 + 8, column.offsets[name])

        # apply some styles to the instance sheet
        for name, line, red, green in valueRows:
            for i in red:
                cell = self.get(2 + line, i)
                cell.style = "cellBest"
            for i in green:
                cell = self.get(2 + line, i)
                cell.style = "cellWorst"
            
    def addRunspec(self, runspec):
        column = self.columns.getColumn(runspec)
        self.machines.add(column.machine)
        for classresult in runspec.classresults:
            for instresult in classresult.instresults:
                for run in instresult.runs:
                    if self.measures == "": measures = sorted(run.measures.keys())
                    else: measures = map(lambda x: x[0], self.measures)
                    for name in measures:
                        if name in run.measures:
                            valueType, value = run.measures[name]
                            if valueType != "float": valueType = "string"
                            column.addCell(instresult.instance.line + run.number - 1, name, valueType, value)
    
    def classTable(self):
        # TODO: adjust the columns
        #for column in self.columns.columns:
        table = InstanceTable(self.benchmark, self.columns, self.measures, "ta2")
        table.finish()
        return table

class Summary:
    def __init__(self):
        self.sum    = 0
        self.dev    = 0
        self.sqsum  = 0
        self.avg    = 0
        self.dst    = 0
        self.best   = 0
        self.better = 0
        self.worse  = 0
        self.worst  = 0
    
    def calc(self, n, colA, minmum, median, maximum):
        self.avg = self.sum / n
        self.dev = math.sqrt(self.sqsum / n - self.avg * self.avg)
        colA.extend([None for _ in range(0, n - len(colA))])
        # geometric distance, best
        if minmum != None:
            minmum.extend([None for _ in range(0, n - len(minmum))])
            sdsum = 0
            for a, b in zip(colA, minmum):
                if a != None:
                    if a <= b: 
                        self.best += 1
                    sdsum += (a - b) * (a - b)
            self.dst = math.sqrt(sdsum)
        # better, worse
        if median != None:
            median.extend([None for _ in range(0, n - len(median))])
            for a, b in zip(colA, median):
                if a != None:
                    if a < b:
                        self.better += 1
                    elif a > b:
                        self.worse += 1
        # worst 
        if maximum != None:
            maximum.extend([None for _ in range(0, n - len(maximum))])
            for a, b in zip(colA, maximum):
                if a != None and a >= b: 
                    self.worst += 1
        
    def add(self, val):
        self.sum   += val
        self.sqsum += val * val
        
class Column:
    def __init__(self, setting, machine):
        self.setting  = setting
        self.machine  = machine
        self.offset   = None
        self.content  = {}
        self.type     = {}
        self.summary  = {}
        self.offsets  = {}
    
    def genName(self, addMachine):
        res = self.setting.system.name + "-" + self.setting.system.version + "/" + self.setting.name
        if addMachine:
            res += " ({0})".format(self.machine.name) 
        return res         
    
    def __cmp__(self, other):
        return cmp((self.setting.system.order, self.setting.order, self.machine.name), (other.setting.system.order, other.setting.order, other.machine.name))
    
    def __hash__(self):
        return hash((self.setting, self.machine))
    
    def calcSummary(self, n, ref):
        for name, summary in self.summary.items():
            minimum = maximum = median = None  
            if len(ref) == 3:
                minimum = ref[0].content[name]
                maximum = ref[1].content[name]
                median  = ref[2].content[name]
            summary.calc(n, self.content[name], minimum, maximum, median)
    
    def addCell(self, line, name, valueType, value):
        if valueType == "float": 
            value = float(value)
            if not name in self.summary: 
                self.summary[name] = Summary() 
            self.summary[name].add(value)
        self.type[name] = valueType
        if not name in self.content: 
            self.content[name] = []
        content = self.content[name]
        while len(content) <= line: 
            content.append(None)
        content[line] = value
