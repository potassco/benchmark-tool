"""
Created on Apr 14, 2025

@author: Tom Schmidt
"""

import re
from typing import TYPE_CHECKING, Any, Optional, no_type_check

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

    def __str__(self) -> str:
        s = self.formula_string
        # remove leading '='
        if s.startswith("="):
            s = s[1:]
        # wrap references
        s = re.sub(r"([\w\.]*[$A-Z]+[$0-9]+(:[\w\.]*[$A-Z]+[$0-9]+)?)", r"[\1]", s)
        # add '.' before references if necessary
        s = re.sub(r"(?<!\.)([$A-Z]+[$0-9]+)(?!\()", r".\1", s)
        return f"of:={s}"


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


def get_cell_index(col: int, row: int, abs_col: bool = False, abs_row: bool = False) -> str:
    """
    Calculate ODS cell index.

    Keyword arguments:
    col     - Column index
    row     - Row index
    abs_col  - Set '$' for column
    abs_row  - Set '$' for row
    """
    radix = ord("Z") - ord("A") + 1
    ret = ""
    while col >= 0:
        rem = col % radix
        ret = chr(rem + ord("A")) + ret
        col = col // radix - 1
    if abs_col:
        pre_col = "$"
    else:
        pre_col = ""
    if abs_row:
        pre_row = "$"
    else:
        pre_row = ""
    return pre_col + ret + pre_row + str(row + 1)


class ODSDoc:
    """
    Class representing ODS document.
    """

    def __init__(self, benchmark: "result.BenchmarkMerge", measures: Any):
        """
        Setup Instance and Class sheet.

        Keyword arguments:
        benchmark - BenchmarkMerge object
        measures - Measures to be displayed
        """
        self.inst_sheet = Sheet(benchmark, measures, "Instances")
        self.class_sheet = Sheet(benchmark, measures, "Classes", self.inst_sheet)

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Keyword arguments:
        runspec - Run specification
        """
        self.inst_sheet.add_runspec(runspec)
        self.class_sheet.add_runspec(runspec)

    def finish(self) -> None:
        """
        Complete sheets by adding formulas and summaries.
        """
        self.inst_sheet.finish()
        self.class_sheet.finish()

    def make_ods(self, out: str) -> None:
        """
        Write ODS file.

        Keyword arguments:
        out - Name of the generated ODS file
        """
        # replace all undefined cells with None (empty cell)
        self.inst_sheet.content = self.inst_sheet.content.fillna(np.nan).replace([np.nan], [None])
        self.class_sheet.content = self.class_sheet.content.fillna(np.nan).replace([np.nan], [None])

        with ods.writer(open(out, "wb")) as odsfile:
            inst_sheet = odsfile.new_sheet("Instances")
            for line in range(len(self.inst_sheet.content.index)):
                inst_sheet.writerow(list(self.inst_sheet.content.iloc[line]))
            class_sheet = odsfile.new_sheet("Classes")
            for line in range(len(self.class_sheet.content.index)):
                class_sheet.writerow(list(self.class_sheet.content.iloc[line]))


# pylint: disable=too-many-instance-attributes
class Sheet:
    """
    Class representing an ODS sheet.
    """

    def __init__(
        self, benchmark: "result.BenchmarkMerge", measures: Any, name: str, ref_sheet: Optional["Sheet"] = None
    ):
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
        self.system_blocks: dict[tuple[Any, Any], SystemBlock] = {}
        # types of measures
        self.types: dict[str, str] = {}
        # measures to be displayed
        self.measures = measures
        # machines
        self.machines: set["result.Machine"] = set()
        # sheet for references
        self.ref_sheet = ref_sheet
        # references for summary generation
        self.summary_refs: dict[str, Any] = {}

        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        if self.ref_sheet is None:
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

        self.result_offset = row
        self.content.loc[self.result_offset + 1] = "SUM"
        self.content.loc[self.result_offset + 2] = "AVG"
        self.content.loc[self.result_offset + 3] = "DEV"
        self.content.loc[self.result_offset + 4] = "DST"
        self.content.loc[self.result_offset + 5] = "BEST"
        self.content.loc[self.result_offset + 6] = "BETTER"
        self.content.loc[self.result_offset + 7] = "WORSE"
        self.content.loc[self.result_offset + 8] = "WORST"
        # fill missing rows
        self.content = self.content.reindex(list(range(self.content.index.max() + 1)))

    # pylint: disable=too-many-nested-blocks, too-many-branches
    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add results to the their respective blocks.

        Keyword arguments:
        runspec - Run specification
        """
        key = (runspec.setting, runspec.machine)
        if key not in self.system_blocks:
            self.system_blocks[key] = SystemBlock(runspec.setting, runspec.machine)
        block = self.system_blocks[key]
        if block.machine:
            self.machines.add(block.machine)
        for classresult in runspec:
            class_sum: dict[str, Any] = {}
            for instresult in classresult:
                for run in instresult:
                    for name, value_type, value in run.iter(self.measures):
                        if value_type == "int":
                            value_type = "float"
                        elif value_type != "float":
                            value_type = "string"
                        if self.ref_sheet is None:
                            if value_type == "float":
                                value = float(value)
                            block.add_cell(instresult.instance.line + run.number - 1, name, value_type, value)
                        elif value_type == "float":
                            if not name in class_sum:
                                class_sum[name] = (0.0, 0)
                            class_sum[name] = (float(value) + class_sum[name][0], 1 + class_sum[name][1])
                        else:
                            if not name in class_sum:
                                class_sum[name] = None
            # classSheet
            if self.ref_sheet:
                for name, value in class_sum.items():
                    if not value is None:
                        temp_res = value[0] / value[1]
                        if name == "timeout":
                            temp_res = value[0]
                        block.add_cell(
                            classresult.benchclass.line, name, "classresult", (classresult.benchclass, temp_res)
                        )
                    else:
                        block.add_cell(classresult.benchclass.line, name, "empty", np.nan)

    def finish(self) -> None:
        """
        Finish ODS content.
        """
        col = 1
        # join results of different blocks
        for block in sorted(self.system_blocks.values()):
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, col] = block.gen_name(len(self.machines) > 1)
            for m in block.columns:
                self.types[m] = block.columns[m]
            col += len(block.columns)

        # get columns used for summary calculations
        # add formulas for results of classSheet
        float_occur: dict[str, set[Any]] = {}
        for column in self.content:
            name = self.content.at[1, column]
            if self.types.get(name, "") == "classresult":
                for row in range(2, self.result_offset):
                    op = "AVERAGE"
                    if name == "timeout":
                        op = "SUM"
                    self.content.at[row, column] = Formula(
                        ""
                        + op
                        + "(Instances.{0}:Instances.{1})".format(
                            get_cell_index(column, self.content.at[2, column][0].instStart + 2),
                            get_cell_index(column, self.content.at[2, column][0].instEnd + 2),
                        )
                    )
            if self.types.get(name, "") in ["float", "classresult"]:
                if not name in float_occur:
                    float_occur[name] = set()
                float_occur[name].add(column)

        # add summaries
        self.add_row_summary(float_occur, col)
        self.add_col_summary()

    def add_row_summary(self, float_occur: dict[str, set[Any]], offset: int) -> None:
        """
        Add row summary (min, max, median).
        Keyword arguments:
        floatOccur  - Dict containing column references of float columns
        offset      - Column offset
        """
        col = offset
        for col_name in ["min", "median", "max"]:
            block = SystemBlock(None, None)
            block.offset = col
            self.summary_refs[col_name] = {"col": col}
            measures: list[str]
            if self.measures == "":
                measures = sorted(float_occur.keys())
            else:
                measures = list(map(lambda x: x[0], self.measures))
            for name in measures:
                if name in float_occur:
                    for row in range(self.result_offset - 2):
                        ref_range = ""
                        for col_ref in sorted(float_occur[name]):
                            if ref_range != "":
                                ref_range += ";"
                            ref_range += get_cell_index(col_ref, row + 2, True)
                        block.add_cell(row, name, "formular", Formula("{1}({0})".format(ref_range, col_name.upper())))
                    self.summary_refs[col_name][name] = "{0}:{1}".format(
                        get_cell_index(col, 2, True), get_cell_index(col, self.result_offset - 1, True)
                    )
                    col += 1
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, block.offset] = col_name

    def add_col_summary(self) -> None:
        """
        Add column summary if applicable to column type.
        """
        for col in self.content:
            name = self.content.at[1, col]
            if self.types.get(name, "") in ["float", "classresult"]:
                res_value = "{0}:{1}".format(
                    get_cell_index(col, 2, True), get_cell_index(col, self.result_offset - 1, True)
                )
                self.content.at[self.result_offset + 1, col] = Formula("SUM({0})".format(res_value))
                self.content.at[self.result_offset + 2, col] = Formula("AVERAGE({0})".format(res_value))
                self.content.at[self.result_offset + 3, col] = Formula("STDEV({0})".format(res_value))
                if col < self.summary_refs["min"]["col"]:
                    self.content.at[self.result_offset + 4, col] = Formula(
                        "SUMPRODUCT(--({0}-{1})^2)^0.5".format(res_value, self.summary_refs["min"][name])
                    )
                    self.content.at[self.result_offset + 5, col] = Formula(
                        "SUMPRODUCT(--({0}={1}))".format(res_value, self.summary_refs["min"][name])
                    )
                    self.content.at[self.result_offset + 6, col] = Formula(
                        "SUMPRODUCT(--({0}<{1}))".format(res_value, self.summary_refs["median"][name])
                    )
                    self.content.at[self.result_offset + 7, col] = Formula(
                        "SUMPRODUCT(--({0}>{1}))".format(res_value, self.summary_refs["median"][name])
                    )
                    self.content.at[self.result_offset + 8, col] = Formula(
                        "SUMPRODUCT(--({0}={1}))".format(res_value, self.summary_refs["max"][name])
                    )


class SystemBlock(Sortable):
    """
    Dataframe containing results for system.
    """

    def __init__(self, setting: Optional["result.Setting"], machine: Optional["result.Machine"]):
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

    def gen_name(self, add_machine: bool) -> str:
        """
        Generate name of the block.

        Keyword arguments:
        addMachine - Whether to include the machine name in the name
        """
        res: str = ""
        if self.setting:
            res = self.setting.system.name + "-" + self.setting.system.version + "/" + self.setting.name
            if add_machine and self.machine:
                res += " ({0})".format(self.machine.name)
        return res

    @no_type_check
    def __cmp__(self, other: "SystemBlock") -> int:
        if self.setting and self.machine:
            return cmp(
                (self.setting.system.order, self.setting.order, self.machine.name),
                (other.setting.system.order, other.setting.order, other.machine.name),
            )
        return 0

    def __hash__(self) -> int:
        return hash((self.setting, self.machine))

    def add_cell(self, row: int, name: str, value_type: str, value: Any) -> None:
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
        self.columns[name] = value_type
        # leave space for header
        self.content.at[row + 2, name] = value
