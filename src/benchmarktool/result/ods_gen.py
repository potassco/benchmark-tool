"""
Created on Apr 14, 2025

@author: Tom Schmidt
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional
from unittest import mock

import numpy as np
import odswriter as ods  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result import ods_config

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage

ods.ods_components.styles_xml = ods_config.styles_xml


def write_row(self, cells):
    """
    Method to write ods row.
    Replaces ods.Sheet.writerow
    """
    import decimal

    row = self.dom.createElement("table:table-row")
    content_cells = 0

    for cell_data in cells:
        cell = self.dom.createElement("table:table-cell")
        text = None

        if isinstance(cell_data, tuple):
            value = cell_data[0]
            style = cell_data[1]
        else:
            value = cell_data
            style = None

        if isinstance(value, bool):
            # Bool condition must be checked before numeric because:
            # isinstance(True, int): True
            # isinstance(True, bool): True
            cell.setAttribute("office:value-type", "boolean")
            cell.setAttribute("office:boolean-value", "true" if value else "false")
            cell.setAttribute("table:style-name", "cBool")
            text = "TRUE" if value else "FALSE"

        elif isinstance(value, (float, int, decimal.Decimal, int)):
            cell.setAttribute("office:value-type", "float")
            float_str = str(value)
            cell.setAttribute("office:value", float_str)
            if style is not None:
                cell.setAttribute("table:style-name", style)
            text = float_str

        elif isinstance(value, Formula):
            cell.setAttribute("table:formula", str(value))
            if style is not None:
                cell.setAttribute("table:style-name", style)

        elif value is None:
            pass  # Empty element

        else:
            # String and unknown types become string cells
            cell.setAttribute("office:value-type", "string")
            if style is not None:
                cell.setAttribute("table:style-name", style)
            text = str(value)

        if text:
            p = self.dom.createElement("text:p")
            p.appendChild(self.dom.createTextNode(text))
            cell.appendChild(p)

        row.appendChild(cell)

        content_cells += 1

    if self.cols is not None:
        if content_cells > self.cols:
            raise Exception("More cells than cols.")

        for _ in range(content_cells, self.cols):
            cell = self.dom.createElement("table:table-cell")
            row.appendChild(cell)

    self.table.appendChild(row)


class Formula(ods.Formula):  # type: ignore[misc]
    """
    Extending odswriter.Formula class with the ability to
    handle sheet references and some minor fixes.
    """

    def __str__(self) -> str:
        """
        Get ods string representation.
        """
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

    Attributes:
        v (Any): Value tried to be cast to float.
    """
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


def get_cell_index(col: int, row: int, abs_col: bool = False, abs_row: bool = False) -> str:
    """
    Calculate ODS cell index.

    Attributes:
        col (int):      Column index.
        row (int):      Row index.
        abs_col (bool): Set '$' for column.
        abs_row (bool): Set '$' for row.
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

    def __init__(self, benchmark: "result.BenchmarkMerge", measures: list[tuple[str, Any]]):
        """
        Setup Instance and Class sheet.

        Attributes:
            benchmark (BenchmarkMerge):       BenchmarkMerge object.
            measures (list[tuple[str, Any]]): Measures to be displayed.
        """
        self.inst_sheet = Sheet(benchmark, measures, "Instances")
        self.class_sheet = Sheet(benchmark, measures, "Classes", self.inst_sheet)

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Attributes:
            runspec (Runspec): Run specification.
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

        Attributes:
            out (str): Name of the generated ODS file.
        """

        with mock.patch.object(ods.Sheet, "writerow", write_row):
            with ods.writer(open(out, "wb")) as odsfile:
                inst_sheet = odsfile.new_sheet("Instances")
                for line in range(len(self.inst_sheet.content.index)):
                    # print(list(self.inst_sheet.content.iloc[line]))
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
        self,
        benchmark: "result.BenchmarkMerge",
        measures: list[tuple[str, Any]],
        name: str,
        ref_sheet: Optional["Sheet"] = None,
    ):
        """
        Initialize sheet.

        Attributes:
            benchmark (BenchmarkMerge):       Benchmark.
            measures (list[tuple[str, Any]]): Measures to be displayed.
            name (str):                       Name of the sheet.
            refSheet (Optional[Sheet]):       Reference sheet.
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
        # dataframe containing all results and stats
        self.values = pd.DataFrame()

        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        if self.ref_sheet is None:
            row = 2
            for benchclass in benchmark:
                for instance in benchclass:
                    self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                    row += instance.values["max_runs"]
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

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add results to the their respective blocks.

        Attributes:
            runspec (Runspec): Run specification
        """
        key = (runspec.setting, runspec.machine)
        if key not in self.system_blocks:
            self.system_blocks[key] = SystemBlock(runspec.setting, runspec.machine)
        block = self.system_blocks[key]
        if block.machine:
            self.machines.add(block.machine)

        for benchclass_result in runspec:
            benchclass_summary: dict[str, Any] = {}
            for instance_result in benchclass_result:
                self.add_instance_results(block, instance_result, benchclass_summary)
            # classSheet
            if self.ref_sheet:
                self.add_benchclass_summary(block, benchclass_result, benchclass_summary)

    def add_instance_results(
        self, block: "SystemBlock", instance_result: "result.InstanceResult", benchclass_summary: dict[str, Any]
    ) -> None:
        """
        Add instance results to SystemBlock and add values to summary if necessary.

        Attributes:
            block (SystemBlock):                 SystemBlock to which results are added.
            instance_result (InstanceResult):    InstanceResult.
            benchclass_summary (dict[str, Any]): Summary of benchmark class.
        """
        for run in instance_result:
            for name, value_type, value in run.iter(self.measures):
                if value_type == "int":
                    value_type = "float"
                elif value_type != "float":
                    value_type = "string"
                if self.ref_sheet is None:
                    if value_type == "float":
                        block.add_cell(
                            instance_result.instance.values["row"] + run.number - 1, name, value_type, float(value)
                        )
                    else:
                        block.add_cell(instance_result.instance.values["row"] + run.number - 1, name, value_type, value)
                elif value_type == "float":
                    if not name in benchclass_summary:
                        benchclass_summary[name] = (0.0, 0)
                    benchclass_summary[name] = (
                        float(value) + benchclass_summary[name][0],
                        1 + benchclass_summary[name][1],
                    )
                else:
                    if not name in benchclass_summary:
                        benchclass_summary[name] = None

    def add_benchclass_summary(
        self, block: "SystemBlock", benchclass_result: "result.ClassResult", benchclass_summary: dict[str, Any]
    ) -> None:
        """
        Add benchmark class summary to SystemBlock.

        Attributes:
            block (SystemBlock):                 SystemBlock to which summary is added.
            benchclass_result (ClassResult):     ClassResult.
            benchclass_summary (dict[str, Any]): Summary of benchmark class.
        """
        for name, value in benchclass_summary.items():
            if not value is None:
                temp_res = value[0] / value[1]
                if name == "timeout":
                    temp_res = value[0]
                block.add_cell(
                    benchclass_result.benchclass.values["row"],
                    name,
                    "classresult",
                    (benchclass_result.benchclass, temp_res),
                )
            else:
                block.add_cell(benchclass_result.benchclass.values["row"], name, "empty", np.nan)

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
                    self.values.at[row, column] = self.content.at[row, column][1]
                    self.content.at[row, column] = Formula(
                        ""
                        + op
                        + "(Instances.{0}:Instances.{1})".format(
                            get_cell_index(column, self.content.at[2, column][0].values["inst_start"] + 2),
                            get_cell_index(column, self.content.at[2, column][0].values["inst_end"] + 2),
                        )
                    )
            if self.types.get(name, "") in ["float", "classresult"]:
                if not name in float_occur:
                    float_occur[name] = set()
                float_occur[name].add(column)

        self.values = (
            self.content.iloc[2 : self.result_offset - 1, 1:].combine_first(self.values).combine_first(self.content)
        )

        # add summaries
        self.add_row_summary(float_occur, col)
        self.add_col_summary()

        # color cells
        self.add_styles(float_occur)

        # replace all undefined cells with None (empty cell)
        self.content = self.content.fillna(np.nan).replace([np.nan], [None])

    def add_row_summary(self, float_occur: dict[str, set[Any]], offset: int) -> None:
        """
        Add row summary (min, max, median).

        Attributes:
            float_occur (dict[str, set[Any]]): Dict containing column references of float columns.
            offset (int):                      Column offset.
        """
        col = offset
        for col_name in ["min", "median", "max"]:
            block = SystemBlock(None, None)
            block.offset = col
            self.summary_refs[col_name] = {"col": col}
            measures: list[str]
            if len(self.measures) == 0:
                measures = sorted(float_occur.keys())
            else:
                measures = list(map(lambda x: x[0], self.measures))
            for measure in measures:
                if measure in float_occur:
                    self.values.at[1, col] = measure
                    self._add_summary_formula(block, col_name, measure, float_occur, col)
                    self.summary_refs[col_name][measure] = (
                        col,
                        "{0}:{1}".format(
                            get_cell_index(col, 2, True), get_cell_index(col, self.result_offset - 1, True)
                        ),
                    )
                    col += 1
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, block.offset] = col_name
            self.values.at[0, block.offset] = col_name

    def _add_summary_formula(
        self, block: "SystemBlock", operator: str, measure: str, float_occur: dict[str, Any], col: int
    ) -> None:
        """
        Add row summary formula.

        Attributes:
            block (SystemBlock):          SystemBlock to which summary is added.
            operator (str):               Summary operator.
            measure (str):                Name of the measure to be summarized.
            float_occur (dict[str, Any]): Dict containing column references of float columns.
            col (int):                    Current column index.
        """
        for row in range(self.result_offset - 2):
            ref_range = ""
            for col_ref in sorted(float_occur[measure]):
                if ref_range != "":
                    ref_range += ";"
                ref_range += get_cell_index(col_ref, row + 2, True)
            block.add_cell(row, measure, "formular", Formula("{1}({0})".format(ref_range, operator.upper())))
            self.values.at[2 + row, col] = getattr(np, "nan" + operator)(
                self.values.loc[2 + row, sorted(float_occur[measure])]
            )

    def add_col_summary(self) -> None:
        """
        Add column summary if applicable to column type.
        """
        for col in self.content:
            name = self.content.at[1, col]
            if self.types.get(name, "") in ["float", "classresult"]:
                ref_value = "{0}:{1}".format(
                    get_cell_index(col, 2, True), get_cell_index(col, self.result_offset - 1, True)
                )
                values = np.array(self.values.loc[2 : self.result_offset - 1, col])
                # SUM
                self.content.at[self.result_offset + 1, col] = Formula("SUM({0})".format(ref_value))
                self.values.at[self.result_offset + 1, col] = np.nansum(values)
                # AVG
                self.content.at[self.result_offset + 2, col] = Formula("AVERAGE({0})".format(ref_value))
                self.values.at[self.result_offset + 2, col] = np.nanmean(values)
                # DEV
                self.content.at[self.result_offset + 3, col] = Formula("STDEV({0})".format(ref_value))
                if len(values) != 1:
                    self.values.at[self.result_offset + 3, col] = np.nanstd(values, ddof=1)
                else:
                    self.values.at[self.result_offset + 3, col] = np.nan
                if col < self.summary_refs["min"]["col"]:
                    # DST
                    self.content.at[self.result_offset + 4, col] = Formula(
                        "SUMPRODUCT(--({0}-{1})^2)^0.5".format(ref_value, self.summary_refs["min"][name][1])
                    )
                    self.values.at[self.result_offset + 4, col] = (
                        np.nansum(
                            (
                                values
                                - np.array(
                                    self.values.loc[2 : self.result_offset - 1, self.summary_refs["min"][name][0]]
                                )
                            )
                            ** 2
                        )
                        ** 0.5
                    )
                    # BEST (values * -1, since higher better)
                    self.content.at[self.result_offset + 5, col] = Formula(
                        "SUMPRODUCT(--({0}={1}))".format(ref_value, self.summary_refs["min"][name][1])
                    )
                    self.values.at[self.result_offset + 5, col] = -1 * np.nansum(
                        values
                        == np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["min"][name][0]])
                    )
                    # BETTER (values * -1, since higher better)
                    self.content.at[self.result_offset + 6, col] = Formula(
                        "SUMPRODUCT(--({0}<{1}))".format(ref_value, self.summary_refs["median"][name][1])
                    )
                    self.values.at[self.result_offset + 6, col] = -1 * np.nansum(
                        values
                        < np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["median"][name][0]])
                    )
                    # WORSE
                    self.content.at[self.result_offset + 7, col] = Formula(
                        "SUMPRODUCT(--({0}>{1}))".format(ref_value, self.summary_refs["median"][name][1])
                    )
                    self.values.at[self.result_offset + 7, col] = np.nansum(
                        values
                        > np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["median"][name][0]])
                    )
                    # WORST
                    self.content.at[self.result_offset + 8, col] = Formula(
                        "SUMPRODUCT(--({0}={1}))".format(ref_value, self.summary_refs["max"][name][1])
                    )
                    self.values.at[self.result_offset + 8, col] = np.nansum(
                        values
                        == np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["max"][name][0]])
                    )

    def add_styles(self, float_occur):
        """
        Color float results and their summaries.

        Attributes:
            float_occur (dict[str, Any]): Dict containing column references of float columns.
        """
        for measure in self.measures:
            if measure[0] in float_occur:
                func = measure[1]
                if func == "t":
                    diff = 2
                elif func == "to":
                    diff = 0
                else:
                    return
                # results:
                values = np.nan_to_num(
                    np.array(
                        self.values.loc[2 : self.result_offset - 1, sorted(float_occur[measure[0]])].values, dtype=float
                    )
                )
                min_values = np.array(
                    self.values[[self.summary_refs["min"][measure[0]][0]]].loc[2 : self.result_offset - 1].values,
                    dtype=float,
                )
                median_values = np.array(
                    self.values[[self.summary_refs["median"][measure[0]][0]]].loc[2 : self.result_offset - 1].values,
                    dtype=float,
                )
                max_values = np.array(
                    self.values[[self.summary_refs["max"][measure[0]][0]]].loc[2 : self.result_offset - 1].values,
                    dtype=float,
                )
                max_min_diff = (max_values - min_values) > diff
                max_med_diff = (max_values - median_values) > diff

                self.content = (
                    self.content.loc[2 : self.result_offset - 1, sorted(float_occur[measure[0]])]
                    .mask(
                        (values == min_values) & (values < median_values) & max_min_diff,
                        self.content.map(lambda x: (x, "cellBest")),
                    )
                    .combine_first(self.content)
                )
                self.content = (
                    self.content.loc[2 : self.result_offset - 1, sorted(float_occur[measure[0]])]
                    .mask(
                        (values == max_values) & (values > median_values) & max_med_diff,
                        self.content.map(lambda x: (x, "cellWorst")),
                    )
                    .combine_first(self.content)
                )

                # summary
                values = np.nan_to_num(
                    np.array(
                        self.values.loc[self.result_offset + 1 :, sorted(float_occur[measure[0]])].values, dtype=float
                    )
                )
                min_values = np.reshape(np.min(values, axis=1), (-1, 1))
                median_values = np.reshape(np.median(values, axis=1), (-1, 1))
                max_values = np.reshape(np.max(values, axis=1), (-1, 1))
                max_min_diff = (max_values - min_values) > diff
                max_med_diff = (max_values - median_values) > diff

                self.content = (
                    self.content.loc[self.result_offset + 1 :, sorted(float_occur[measure[0]])]
                    .mask(
                        (values == min_values) & (values < median_values) & max_min_diff,
                        self.content.map(lambda x: (x, "cellBest")),
                    )
                    .combine_first(self.content)
                )
                self.content = (
                    self.content.loc[self.result_offset + 1 :, sorted(float_occur[measure[0]])]
                    .mask(
                        (values == max_values) & (values > median_values) & max_med_diff,
                        self.content.map(lambda x: (x, "cellWorst")),
                    )
                    .combine_first(self.content)
                )


@dataclass(order=True, unsafe_hash=True)
class SystemBlock:
    """
    Dataframe containing results for system.

    Attributes:
        setting (Optional[Setting]): Benchmark setting.
        machine (Optional[Machine]): Machine.
        content (DataFrame):         Results.
        columns (dict[str, Any]):    Dictionary of columns and their types.
        offset (Optional[int]):      Offset for final block position.
    """

    setting: Optional["result.Setting"]
    machine: Optional["result.Machine"]
    content: pd.DataFrame = field(default_factory=pd.DataFrame, compare=False)
    columns: dict[str, Any] = field(default_factory=dict, compare=False)
    offset: Optional[int] = field(default=None, compare=False)

    def gen_name(self, add_machine: bool) -> str:
        """
        Generate name of the block.

        Attributes:
            addMachine (bool): Whether to include the machine name in the name.
        """
        res: str = ""
        if self.setting:
            res = self.setting.system.name + "-" + self.setting.system.version + "/" + self.setting.name
            if add_machine and self.machine:
                res += " ({0})".format(self.machine.name)
        return res

    def add_cell(self, row: int, name: str, value_type: str, value: Any) -> None:
        """
        Add cell to dataframe.

        Attributes:
            row (int):       Row of the new cell.
            name (str):      Name of the column of the new cell (in most cases the measure).
            valueType (str): Data type of the new cell.
            value (Any):     Value of the new cell.
        """
        if name not in self.columns:
            self.content.at[1, name] = name
        self.columns[name] = value_type
        # leave space for header
        self.content.at[row + 2, name] = value
