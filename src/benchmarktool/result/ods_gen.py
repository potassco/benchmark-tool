"""
Created on Apr 14, 2025

@author: Tom Schmidt
"""

import re
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
import odswriter as ods  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.tools import Sortable, cmp

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage


class Formula(ods.Formula):  # type: ignore[misc]
    """
    Extending odswriter.Formula class with the ability to
    handle sheet references and some minor fixes.
    """

    def __init__(self, s: str):
        super().__init__(s)

    def __str__(self) -> str:
        s = self.formula_string
        # remove leading '='
        if s.startswith("="):
            s = s[1:]
        # wrap references
        s = re.sub(r"([\w\.]*[$A-Z]+[$0-9]+(:[\w\.]*[$A-Z]+[$0-9]+)?)", r"[\1]", s)
        # add '.' before references if necessary
        s = re.sub(r"(?<!\.)([$A-Z]+[$0-9]+)(?!\()", r".\1", s)
        return "of:={}".format(s)


def try_float(v: Any) -> Any:
    """
    Try to cast given value to float.
    Return input if not possible.

    Keyword arguments:
    v - Value tried to be cast to float
    """
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


class ODSDoc:
    """
    Class representing ODS document.

    (previously called Spreadsheet)
    """

    def __init__(self, benchmark: 'result.BenchmarkMerge', measures: Any):
        """
        Setup Instance and Class sheet.

        Keyword arguments:
        benchmark - BenchmarkMerge object
        measures - Measures to be displayed
        """
        self.instSheet = Sheet(benchmark, measures, "Instances")
        self.classSheet = Sheet(benchmark, measures, "Classes", self.instSheet)

    def addRunspec(self, runspec: 'result.Runspec') -> None:
        """
        Keyword arguments:
        runspec - Run specification
        """
        self.instSheet.addRunspec(runspec)
        self.classSheet.addRunspec(runspec)

    def finish(self) -> None:
        """
        Complete sheets by adding formulas and summaries.
        """
        self.instSheet.finish()
        self.classSheet.finish()

    def make_ods(self, out: str) -> None:
        """
        Write ODS file.

        Keyword arguments:
        out - Name of the generated ODS file
        """
        # replace all undefined cells with None (empty cell)
        self.instSheet.content = self.instSheet.content.fillna(np.nan).replace([np.nan], [None])
        self.classSheet.content = self.classSheet.content.fillna(np.nan).replace([np.nan], [None])

        with ods.writer(open(out, "wb")) as odsfile:
            instSheet = odsfile.new_sheet("Instances")
            for line in range(len(self.instSheet.content.index)):
                instSheet.writerow([v for v in self.instSheet.content.iloc[line]])
            classSheet = odsfile.new_sheet("Classes")
            for line in range(len(self.classSheet.content.index)):
                classSheet.writerow([v for v in self.classSheet.content.iloc[line]])


class Sheet:
    """
    Class representing an ODS sheet.

    (previously called Table/ResultTable)
    """

    def __init__(self, benchmark: 'result.BenchmarkMerge', measures: Any, name: str, refSheet: Optional["Sheet"] = None):
        """
        Initialize sheet.

        Keyword arguments:
        benchmark   - BenchmarkMerge object
        measures    - Measures to be displayed
        name        - Name of the sheet
        refSheet    - Reference sheet
        """
        # dataframe resembling almost final ods form
        self.content = pd.DataFrame()
        # name of the sheet
        self.name = name
        # evaluated benchmarks
        self.benchmark = benchmark
        # dataframes containing result data, use these for calculations
        self.systemBlocks: dict[tuple[Any, Any], SystemBlock] = {}
        # types of measures
        self.types: dict[str, str] = {}
        # measures to be displayed
        self.measures = measures
        # machines
        self.machines: set['result.Machine'] = set()
        # sheet for references
        self.refSheet = refSheet
        # references for summary generation
        self.summaryRefs: dict[str, Any] = {}

        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        if self.refSheet is None:
            row = 2
            for benchclass in benchmark:
                for instance in benchclass:
                    self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                    row += instance.maxRuns
        else:
            row = 2
            for benchclass in benchmark:
                self.content.loc[row] = benchclass.name
                row += 1

        self.resultOffset = row
        self.content.loc[self.resultOffset + 1] = "SUM"
        self.content.loc[self.resultOffset + 2] = "AVG"
        self.content.loc[self.resultOffset + 3] = "DEV"
        self.content.loc[self.resultOffset + 4] = "DST"
        self.content.loc[self.resultOffset + 5] = "BEST"
        self.content.loc[self.resultOffset + 6] = "BETTER"
        self.content.loc[self.resultOffset + 7] = "WORSE"
        self.content.loc[self.resultOffset + 8] = "WORST"
        # fill missing rows
        self.content = self.content.reindex(list(range(self.content.index.max() + 1)))

    def addRunspec(self, runspec: 'result.Runspec') -> None:
        """
        Add results to the their respective blocks.

        Keyword arguments:
        runspec - Run specification
        """
        key = (runspec.setting, runspec.machine)
        if not key in self.systemBlocks:
            self.systemBlocks[key] = SystemBlock(runspec.setting, runspec.machine)
        block = self.systemBlocks[key]
        if block.machine:
            self.machines.add(block.machine)
        for classresult in runspec:
            classSum: dict[str, Any] = {}
            for instresult in classresult:
                for run in instresult:
                    for name, valueType, value in run.iter(self.measures):
                        if valueType == "int":
                            valueType = "float"
                        elif valueType != "float":
                            valueType = "string"
                        if self.refSheet is None:
                            if valueType == "float": value = float(value) 
                            block.addCell(instresult.instance.line + run.number - 1, name, valueType, value)
                        elif valueType == "float":
                            if not name in classSum:
                                classSum[name] = (0.0, 0)
                            classSum[name] = (float(value) + classSum[name][0], 1 + classSum[name][1])
                        else:
                            if not name in classSum:
                                classSum[name] = None
            # classSheet
            if self.refSheet:
                for name, value in classSum.items():
                    if not value is None:
                        resTemp = value[0] / value[1]
                        if name == "timeout":
                            resTemp = value[0]
                        block.addCell(
                            classresult.benchclass.line, name, "classresult", (classresult.benchclass, resTemp)
                        )
                    else:
                        block.addCell(classresult.benchclass.line, name, "empty", np.nan)

    def finish(self) -> None:
        """
        Finish ODS content.
        """
        col = 1
        # join results of different blocks
        for block in sorted(self.systemBlocks.values()):
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, col] = block.genName(len(self.machines) > 1)
            for m in block.columns:
                self.types[m] = block.columns[m]
            col += len(block.columns)

        # get columns used for summary calculations
        # add formulas for results of classSheet
        floatOccur: dict[str, set[Any]] = {}
        for column in self.content:
            name = self.content.at[1, column]
            if self.types.get(name, "") == "classresult":
                for row in range(2, self.resultOffset):
                    op = "AVERAGE"
                    if name == "timeout":
                        op = "SUM"
                    self.content.at[row, column] = Formula(
                        ""
                        + op
                        + "(Instances.{0}:Instances.{1})".format(
                            self.cellIndex(column, self.content.at[2, column][0].instStart + 2),
                            self.cellIndex(column, self.content.at[2, column][0].instEnd + 2),
                        )
                    )
            if self.types.get(name, "") in ["float", "classresult"]:
                if not name in floatOccur:
                    floatOccur[name] = set()
                floatOccur[name].add(column)

        # create dataframe containing evaluated formulas
        # self.contentEval = self.content.copy()

        # create formulas for min, median and max
        for colName in ["min", "median", "max"]:
            block = SystemBlock(None, None)
            block.offset = col
            self.summaryRefs[colName] = {"col": col}
            measures: list[str]
            if self.measures == "":
                measures = sorted(floatOccur.keys())
            else:
                measures = list(map(lambda x: x[0], self.measures))
            for name in measures:
                if name in floatOccur:
                    for row in range(self.resultOffset - 2):
                        minRange = ""
                        for colRef in sorted(floatOccur[name]):
                            if minRange != "":
                                minRange += ";"
                            minRange += self.cellIndex(colRef, row + 2, True)
                        block.addCell(row, name, "formular", Formula("{1}({0})".format(minRange, colName.upper())))
                        # if colName == "min":
                        #    self.contentEval.at[row, name+"_"+colName] = float(self.content.loc[row+ 2,sorted(floatOccur[name])].astype(float).min())
                        # elif colName == "median":
                        #    self.contentEval.at[row, name+"_"+colName] = float(self.content.loc[row+ 2,sorted(floatOccur[name])].astype(float).median())
                        # elif colName == "max":
                        #    self.contentEval.at[row, name+"_"+colName] = float(self.content.loc[row+ 2,sorted(floatOccur[name])].astype(float).max())
                    self.summaryRefs[colName][name] = "{0}:{1}".format(
                        self.cellIndex(col, 2, True), self.cellIndex(col, self.resultOffset - 1, True)
                    )
                    col += 1
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, block.offset] = colName
        self.add_summary()

    def add_summary(self) -> None:
        """
        Add summary rows if applicable to column type.
        """
        for col in self.content:
            name = self.content.at[1, col]
            if self.types.get(name, "") in ["float", "classresult"]:
                resValues = "{0}:{1}".format(
                    self.cellIndex(col, 2, True), self.cellIndex(col, self.resultOffset - 1, True)
                )
                self.content.at[self.resultOffset + 1, col] = Formula("SUM({0})".format(resValues))
                self.content.at[self.resultOffset + 2, col] = Formula("AVERAGE({0})".format(resValues))
                self.content.at[self.resultOffset + 3, col] = Formula("STDEV({0})".format(resValues))
                if col < self.summaryRefs["min"]["col"]:
                    self.content.at[self.resultOffset + 4, col] = Formula(
                        "SUMPRODUCT(--({0}-{1})^2)^0.5".format(resValues, self.summaryRefs["min"][name])
                    )
                    self.content.at[self.resultOffset + 5, col] = Formula(
                        "SUMPRODUCT(--({0}={1}))".format(resValues, self.summaryRefs["min"][name])
                    )
                    self.content.at[self.resultOffset + 6, col] = Formula(
                        "SUMPRODUCT(--({0}<{1}))".format(resValues, self.summaryRefs["median"][name])
                    )
                    self.content.at[self.resultOffset + 7, col] = Formula(
                        "SUMPRODUCT(--({0}>{1}))".format(resValues, self.summaryRefs["median"][name])
                    )
                    self.content.at[self.resultOffset + 8, col] = Formula(
                        "SUMPRODUCT(--({0}={1}))".format(resValues, self.summaryRefs["max"][name])
                    )

    def cellIndex(self, col: int, row: int, absCol: bool = False, absRow: bool = False) -> str:
        """
        Calculate ODS cell index.

        Keyword arguments:
        col     - Column index
        row     - Row index
        absCol  - Set '$' for column
        absRow  - Set '$' for row
        """
        radix = ord("Z") - ord("A") + 1
        ret = ""
        while col >= 0:
            rem = col % radix
            ret = chr(rem + ord("A")) + ret
            col = col // radix - 1
        if absCol:
            preCol = "$"
        else:
            preCol = ""
        if absRow:
            preRow = "$"
        else:
            preRow = ""
        return preCol + ret + preRow + str(row + 1)


class SystemBlock(Sortable):
    """
    Dataframe containing results for system.
    """

    def __init__(self, setting: Optional['result.Setting'], machine: Optional['result.Machine']):
        """
        Initialize system block for given setting and machine.

        Keyword arguments:
        setting - Benchmark setting
        machine - Machine
        """
        self.setting = setting
        self.machine = machine
        self.content = pd.DataFrame()
        self.columns: dict[str, Any] = {}
        self.offset: Optional[int] = None

    def genName(self, addMachine: bool) -> str:
        """
        Generate name of the block.

        Keyword arguments:
        addMachine - Whether to include the machine name in the name
        """
        res: str = ""
        if self.setting:
            res = self.setting.system.name + "-" + self.setting.system.version + "/" + self.setting.name
            if addMachine and self.machine:
                res += " ({0})".format(self.machine.name)
        return res

    def __cmp__(self, other: "SystemBlock") -> int:
        if self.setting and self.machine:
            return cmp((self.setting.system.order, self.setting.order, self.machine.name), (other.setting.system.order, other.setting.order, other.machine.name))  # type: ignore[union-attr]
        return 0

    def __hash__(self) -> int:
        return hash((self.setting, self.machine))

    def addCell(self, row: int, name: str, valueType: str, value: Any) -> None:
        """
        Add cell to dataframe.

        Keyword arguments:
        row         - Row of the new cell
        name        - Name of the column of the new cell (in most cases the measure)
        valueType   - Data type of the new cell
        value       - Value of the new cell
        """
        if name not in self.columns:
            self.content.at[1, name] = name
        self.columns[name] = valueType
        # leave space for header
        self.content.at[row + 2, name] = value
