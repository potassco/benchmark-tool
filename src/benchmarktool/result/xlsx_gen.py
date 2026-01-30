"""
Created on Dec 2, 2025

@author: Tom Schmidt
"""

import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from xlsxwriter import Workbook  # type: ignore[import-untyped]
from xlsxwriter.color import Color  # type: ignore[import-untyped]
from xlsxwriter.utility import cell_autofit_width  # type: ignore[import-untyped]
from xlsxwriter.worksheet import Worksheet  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage


class Formula:
    """
    Helper class representing a spreadsheet formula.
    """

    def __init__(self, formula_string: str):
        """
        Initialize Formula.

        Attributes:
            formula_string (str): Formula string.
        """
        self.formula_string = formula_string

    def __str__(self) -> str:
        """
        Get spreadsheet string representation.
        """
        # remove leading '='
        s = self.formula_string.lstrip("=")
        return f"={s}"


# pylint: disable=too-few-public-methods, dangerous-default-value
class DataValidation:
    """
    Helper class representing a spreadsheet data validation.
    """

    def __init__(self, params: dict[str, Any] = {}, default: Any = None, color: Optional[str] = None):
        """
        Initialize DataValidation.

        Attributes:
            params (dict[str, Any]): Data validation parameters.
            default (Any):           Default value.
            color (Optional[str]):   Color reference.
        """
        self.params = params
        self.default = default
        self.color = color

    def write(self, xlsxdoc: "XLSXDoc", sheet: Worksheet, row: int, col: int) -> None:
        """
        Write to XLSX document sheet.

        Attributes:
            xlsxdoc (XLSXDoc): XLSX document.
            sheet (Worksheet): XLSX worksheet.
            row (int):         Row index.
            col (int):         Column index.
        """
        if isinstance(xlsxdoc.workbook, Workbook):
            if self.default is not None:
                if self.color is not None:
                    sheet.write(
                        row, col, self.default, xlsxdoc.workbook.add_format({"bg_color": xlsxdoc.colors[self.color]})
                    )
                else:
                    sheet.write(row, col, self.default)
            sheet.data_validation(row, col, row, col, self.params)
        else:
            raise ValueError("Trying to write to uninitialized workbook.")

    def __eq__(self, other: object) -> bool:
        """
        Equality operator.

        Attributes:
            other (object): Other DataValidation object.
        """
        if not isinstance(other, DataValidation):
            raise TypeError("Comparison with non DataValidation object.")
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        """
        Hash function.
        """
        return hash((repr(sorted(self.params.items())), self.default, self.color))


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
    Calculate spreadsheet cell index.

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
    pre_col = "$" if abs_col else ""
    pre_row = "$" if abs_row else ""
    return f"{pre_col}{ret}{pre_row}{row + 1}"


# pylint: disable=too-many-instance-attributes
class XLSXDoc:
    """
    Class representing XLSX document.
    """

    def __init__(self, benchmark: "result.BenchmarkMerge", measures: dict[str, Any], max_col_width: int = 300):
        """
        Setup Instance and Class sheet.

        Attributes:
            benchmark (BenchmarkMerge):       BenchmarkMerge object.
            measures (dict[str, Any]): Measures to be displayed.
        """
        self.workbook: Optional[Workbook] = None
        self.max_col_width = max_col_width
        self.header_width = 80

        self.colors: dict[str, Color] = {
            "best": Color("#00ff00"),
            "worst": Color("#ff0000"),
            "input": Color("#ffcc99"),
            "none": Color("#ffffff"),
        }

        self.num_formats: dict[str, str] = {
            "defaultNumber": "0.00",
            "formula": "0.00",
            "to": "0",
        }

        self.inst_sheet = Sheet(benchmark, measures, "Instances")
        self.merged_sheet = Sheet(benchmark, measures, "Merged Runs", self.inst_sheet, "merge")
        self.class_sheet = Sheet(benchmark, measures, "Classes", self.inst_sheet, "class")

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Attributes:
            runspec (Runspec): Run specification.
        """
        self.inst_sheet.add_runspec(runspec)
        self.merged_sheet.add_runspec(runspec)
        self.class_sheet.add_runspec(runspec)

    def finish(self) -> None:
        """
        Complete sheets by adding formulas and summaries.
        """
        self.inst_sheet.finish()
        self.merged_sheet.finish()
        self.class_sheet.finish()

    def make_xlsx(self, out: str) -> None:
        """
        Write XLSX file.

        Attributes:
            out (str): Name of the generated XLSX file.
        """
        self.workbook = Workbook(out)

        for sheet in (self.inst_sheet, self.merged_sheet, self.class_sheet):
            sheet.write_sheet(self)
        self.workbook.close()


# pylint: disable=too-many-instance-attributes, too-many-positional-arguments
class Sheet:
    """
    Class representing an XLSX sheet.
    """

    # pylint: disable=too-many-branches
    def __init__(
        self,
        benchmark: "result.BenchmarkMerge",
        measures: dict[str, Any],
        name: str,
        ref_sheet: Optional["Sheet"] = None,
        sheet_type: str = "instance",
    ):
        """
        Initialize sheet.

        Attributes:
            benchmark (BenchmarkMerge):       Benchmark.
            measures (dict[str, Any]):        Measures to be displayed.
            name (str):                       Name of the sheet.
            refSheet (Optional[Sheet]):       Reference sheet.
            sheet_type (str):                 Type of the sheet.
        """
        # dataframe resembling almost final xlsx form
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
        # sheet type
        self.type = sheet_type
        # references for summary generation
        self.summary_refs: dict[str, Any] = {}
        # dataframe containing all results and stats
        self.values = pd.DataFrame()
        # columns containing floats
        self.float_occur: dict[str, set[Any]] = {}
        # formats for columns
        self.formats: dict[int, str] = {}
        # number of runs
        self.runs: Optional[int] = None
        # run summary only if same number of runs for all instances
        run_summary = True

        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        if self.ref_sheet is None and sheet_type == "instance":
            row = 2
            for benchclass in benchmark:
                for instance in benchclass:
                    self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                    row += instance.values["max_runs"]
                    if self.runs is None:
                        self.runs = instance.values["max_runs"]
                    elif self.runs != instance.values["max_runs"]:  # nocoverage
                        run_summary = False
        elif self.ref_sheet is not None and sheet_type == "class":
            row = 2
            for benchclass in benchmark:
                self.content.loc[row] = benchclass.name
                row += 1
        elif self.ref_sheet is not None and sheet_type == "merge":
            self.content.loc[0] = "Merge criteria:"
            # selection
            self.content.loc[1] = DataValidation(
                {
                    "validate": "list",
                    "source": ["average", "median", "min", "max", "diff"],
                    "input_message": "Select merge criteria",
                },
                "median",
                "input",
            )
            row = 2
            for benchclass in benchmark:
                for instance in benchclass:
                    self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                    row += 1
                    if self.runs is None:
                        self.runs = instance.values["max_runs"]
                    elif self.runs != instance.values["max_runs"]:  # nocoverage
                        run_summary = False
        else:
            raise ValueError("Invalid sheet parameters.")

        self.result_offset = row
        for idx, label in enumerate(["SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"], 1):
            self.content.loc[self.result_offset + idx] = label

        # run summary
        if run_summary and self.runs and self.runs > 1 and self.ref_sheet is None:
            selection = DataValidation(
                {
                    "validate": "list",
                    "source": list(range(1, self.runs + 1)),
                    "input_message": "Select run number",
                },
                1,
                "input",
            )

            for idx, label in enumerate(  # type: ignore[assignment]
                ["Select run:", selection, "SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"], 10
            ):
                self.content.loc[self.result_offset + idx] = label

        # fill missing rows
        self.content = self.content.reindex(list(range(self.content.index.max() + 1))).replace(np.nan, None)

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add results to their respective blocks.

        Attributes:
            runspec (Runspec): Run specification
        """
        key = (runspec.setting, runspec.machine)
        block = self.system_blocks.setdefault(key, SystemBlock(runspec.setting, runspec.machine))
        if block.machine:
            self.machines.add(block.machine)

        for benchclass_result in runspec:
            benchclass_summary: dict[str, Any] = {}
            instance_summary: dict[result.InstanceResult, dict[str, Any]] = {}
            for instance_result in benchclass_result:
                self.add_instance_results(block, instance_result, benchclass_summary, instance_summary)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]
                    # mixed measure
                    elif block.columns[m] not in {self.types[m], "None", "empty"}:
                        self.types[m] = "string"
            if self.ref_sheet:
                # mergeSheet
                if self.type == "merge":
                    for instance_result in benchclass_result:
                        self.add_merged_instance_results(block, instance_result, instance_summary)
                # classSheet
                elif self.type == "class":
                    self.add_benchclass_summary(block, benchclass_result, benchclass_summary)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]

    def add_instance_results(
        self,
        block: "SystemBlock",
        instance_result: "result.InstanceResult",
        benchclass_summary: dict[str, Any],
        instance_summary: dict["result.InstanceResult", dict[str, Any]],
    ) -> None:
        """
        Add instance results to SystemBlock and add values to summary if necessary.

        Attributes:
            block (SystemBlock):                 SystemBlock to which results are added.
            instance_result (InstanceResult):    InstanceResult.
            benchclass_summary (dict[str, Any]): Summary of benchmark class.
            instance_summary (dict[InstanceResult, dict[str, Any]]): Summary of instance results.
        """
        instance_summary[instance_result] = {}
        for run in instance_result:
            for name, value_type, value in run.iter(self.measures):
                self.measures.setdefault(name, None)
                instance_summary[instance_result].setdefault(name, False)
                if value_type == "int":
                    value_type = "float"
                elif value_type not in {"float", "None", "empty"}:
                    value_type = "string"
                if self.ref_sheet is None:
                    if value_type == "float":
                        block.add_cell(
                            instance_result.instance.values["row"] + run.number - 1, name, value_type, float(value)
                        )
                    elif value_type in {"None", "empty"}:
                        block.add_cell(
                            instance_result.instance.values["row"] + run.number - 1, name, value_type, np.nan
                        )
                    else:
                        block.add_cell(instance_result.instance.values["row"] + run.number - 1, name, value_type, value)
                elif value_type == "float" and self.ref_sheet.types.get(name, "") == "float":
                    instance_summary[instance_result][name] = True
                    if benchclass_summary.get(name) is None:
                        benchclass_summary[name] = (0.0, 0)
                    benchclass_summary[name] = (
                        float(value) + benchclass_summary[name][0],
                        1 + benchclass_summary[name][1],
                    )
                else:
                    if name not in benchclass_summary:
                        benchclass_summary[name] = None

    def add_merged_instance_results(
        self,
        block: "SystemBlock",
        instance_result: "result.InstanceResult",
        instance_summary: dict["result.InstanceResult", dict[str, Any]],
    ) -> None:
        """
        Add merged instance results to SystemBlock and add values to summary if necessary.

        Attributes:
            block (SystemBlock):                 SystemBlock to which results are added.
            instance_result (InstanceResult):    InstanceResult.
            instance_summary (dict[result.InstanceResult, dict[str, Any]]): Summary of benchmark class.
        """
        for name, value in instance_summary[instance_result].items():
            inst_val = instance_result.instance.values
            # check if any run has a float value
            if value:
                # value just to signal non empty cell
                block.add_cell(
                    (inst_val["row"] + inst_val["max_runs"]) // inst_val["max_runs"] - 1,
                    name,
                    "merged_runs",
                    {
                        "inst_start": inst_val["row"],
                        "inst_end": inst_val["row"] + inst_val["max_runs"] - 1,
                        "value": 1,
                    },
                )
            else:
                block.add_cell(
                    (inst_val["row"] + inst_val["max_runs"]) // inst_val["max_runs"] - 1, name, "None", np.nan
                )

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
            if value is not None:
                temp_res = value[0] / value[1]
                if name == "timeout":
                    temp_res = value[0]
                block.add_cell(
                    benchclass_result.benchclass.values["row"],
                    name,
                    "classresult",
                    {
                        "inst_start": benchclass_result.benchclass.values["inst_start"],
                        "inst_end": benchclass_result.benchclass.values["inst_end"],
                        "value": temp_res,
                    },
                )
            else:
                block.add_cell(benchclass_result.benchclass.values["row"], name, "None", np.nan)

    def finish(self) -> None:
        """
        Finish XLSX content.
        """
        col = 1
        # join results of different blocks
        for block in sorted(self.system_blocks.values()):
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, col] = block.gen_name(len(self.machines) > 1)
            col += len(block.columns)

        # get columns used for summary calculations
        # add formulas for results of classSheet
        for column in self.content:
            name = self.content.at[1, column]
            if self.types.get(name, "") == "merged_runs":
                for row in range(2, self.result_offset):
                    if isinstance(self.content.at[row, column], dict):
                        # value just to signal non empty cell
                        self.values.at[row, column] = self.content.at[row, column]["value"]
                        cell_range = (
                            f'(Instances!{get_cell_index(column, self.content.at[row, column]["inst_start"] + 2)}:'
                            f'Instances!{get_cell_index(column, self.content.at[row, column]["inst_end"] + 2)})'
                        )
                        self.content.at[row, column] = Formula(
                            f"SWITCH($A$2,"
                            f'"average", AVERAGE{cell_range},'
                            f'"median", MEDIAN{cell_range},'
                            f'"min", MIN{cell_range},'
                            f'"max", MAX{cell_range},'
                            f'"diff", MAX{cell_range}-MIN{cell_range}'
                            ")"
                        )
            elif self.types.get(name, "") == "classresult":
                for row in range(2, self.result_offset):
                    op = "SUM" if name == "timeout" else "AVERAGE"
                    if isinstance(self.content.at[row, column], dict):
                        self.values.at[row, column] = self.content.at[row, column]["value"]
                        self.content.at[row, column] = Formula(
                            f"{op}(Instances!{get_cell_index(column, self.content.at[row, column]['inst_start'] + 2)}:"
                            f"Instances!{get_cell_index(column, self.content.at[row, column]['inst_end'] + 2)})"
                        )
            if self.types.get(name, "") in ["float", "classresult", "merged_runs"]:
                self.float_occur.setdefault(name, set()).add(column)
            # defragmentation (temporary workaround)
            self.content = self.content.copy()
            self.values = self.values.copy()

        if self.ref_sheet is not None:
            self.values = self.values.reindex(index=self.content.index, columns=self.content.columns)
            self.values = self.values.combine_first(self.content)
        else:
            self.values = self.content.copy()

        # defragmentation (temporary workaround)
        self.content = self.content.copy()
        self.values = self.values.copy()

        # add summaries
        self.values = self.values.replace({None: np.nan})
        self.add_row_summary(col)
        self.values = self.values.replace({None: np.nan})
        self.add_col_summary()

        # color cells
        self.add_styles()

        # replace all undefined cells with None (empty cell)
        self.content = self.content.fillna(np.nan).replace(np.nan, None)

    def add_row_summary(self, offset: int) -> None:
        """
        Add row summary (min, max, median).

        Attributes:
            offset (int): Column offset.
        """
        col = offset
        for col_name in ["min", "median", "max"]:
            block = SystemBlock(None, None)
            block.offset = col
            self.summary_refs[col_name] = {"col": col}
            measures = sorted(self.float_occur.keys()) if not self.measures else list(self.measures.keys())
            for measure in measures:
                if measure in self.float_occur:
                    self.values.at[1, col] = measure
                    self._add_summary_formula(block, col_name, measure, self.float_occur, col)
                    self.summary_refs[col_name][measure] = (
                        col,
                        f"{get_cell_index(col, 2, True, True)}:"
                        f"{get_cell_index(col, self.result_offset - 1, True, True)}",
                    )
                    col += 1
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, block.offset] = col_name
            self.values.at[0, block.offset] = col_name

    # pylint: disable=too-many-positional-arguments
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
        self.values[col] = self.values[col].astype(object)
        for row in range(self.result_offset - 2):
            ref_range = ",".join(get_cell_index(col_ref, row + 2, True) for col_ref in sorted(float_occur[measure]))
            values = np.array(self.values.loc[2 + row, sorted(float_occur[measure])], float)
            if np.isnan(values).all():
                self.values.at[2 + row, col] = np.nan
            else:
                # don't write formula if full row is nan
                block.add_cell(row, measure, "formula", Formula(f"{operator.upper()}({ref_range})"))
                self.values.at[2 + row, col] = getattr(np, "nan" + operator)(values)

    def add_col_summary(self) -> None:
        """
        Add column summary if applicable to column type.
        """

        def _get_run_select(ref: str, runs: int, col_idx: int, abs_col: bool = True) -> str:
            """
            Get run dependent row selection formula.

            Attributes:
                ref (str): Row range reference
                runs (int): Number of runs
                col_idx (int): Current column index
                abs_col (bool): Set '$' for new column reference
            """
            return (
                f"CHOOSE({ref},"
                + ",".join([f"ROW({get_cell_index(col_idx, 2 + i, abs_col, True)})" for i in range(runs)])
                + ")"
            )

        def _get_run_filter(base_range: str, choose_rows: str) -> str:
            """
            Get formula for filtered rows by run.

            Attributes:
                base_range (str): Row range to filter
                choose_rows (str): Run selection formula
            """
            return f"FILTER({base_range},MOD(ROW({base_range})-{choose_rows},{self.runs})=0)"

        run_select_cell = f"{get_cell_index(0, self.result_offset + 11, True, True)}"
        for col in self.content:
            name = self.content.at[1, col]
            if self.types.get(name, "") in {"float", "classresult", "merged_runs"}:

                # skip empty columns
                values = np.array(self.values.loc[2 : self.result_offset - 1, col], dtype=float)
                if np.isnan(values).all():
                    continue

                ref_value = (
                    f"{get_cell_index(col, 2, False, True)}:{get_cell_index(col, self.result_offset - 1, False, True)}"
                )
                min_rows = self.summary_refs["min"][name][1]
                med_rows = self.summary_refs["median"][name][1]
                max_rows = self.summary_refs["max"][name][1]
                summaries = [(0, ref_value, min_rows, med_rows, max_rows)]

                # Add run summary formulas if applicable
                if self.ref_sheet is None and self.runs is not None and self.runs > 1:
                    sel_runs = _get_run_select(run_select_cell, self.runs, col, False)
                    ref_runs = _get_run_filter(ref_value, sel_runs)
                    min_runs = _get_run_filter(
                        min_rows, _get_run_select(run_select_cell, self.runs, self.summary_refs["min"][name][0])
                    )
                    med_runs = _get_run_filter(
                        med_rows, _get_run_select(run_select_cell, self.runs, self.summary_refs["median"][name][0])
                    )
                    max_runs = _get_run_filter(
                        max_rows, _get_run_select(run_select_cell, self.runs, self.summary_refs["max"][name][0])
                    )
                    summaries.append((11, ref_runs, min_runs, med_runs, max_runs))

                for offset, ref, min_ref, med_ref, max_ref in summaries:
                    # SUM
                    self.content.at[self.result_offset + offset + 1, col] = Formula(f"SUM({ref})")
                    # AVG
                    self.content.at[self.result_offset + offset + 2, col] = Formula(f"AVERAGE({ref})")
                    # DEV
                    self.content.at[self.result_offset + offset + 3, col] = Formula(f"STDEV({ref})")
                    if col < self.summary_refs["min"]["col"]:
                        with np.errstate(invalid="ignore"):
                            # DST
                            self.content.at[self.result_offset + offset + 4, col] = Formula(
                                f"SUMPRODUCT(--({ref}-{min_ref})^2)^0.5"
                            )
                            # BEST
                            self.content.at[self.result_offset + offset + 5, col] = Formula(
                                f"SUMPRODUCT(NOT(ISBLANK({ref}))*({ref}={min_ref}))"
                            )
                            # BETTER
                            self.content.at[self.result_offset + offset + 6, col] = Formula(
                                f"SUMPRODUCT(NOT(ISBLANK({ref}))*({ref}<{med_ref}))"
                            )
                            # blank values are counted as worse/worst
                            # WORSE
                            self.content.at[self.result_offset + offset + 7, col] = Formula(
                                f"SUMPRODUCT((NOT(ISBLANK({ref}))*({ref}>{med_ref}))+ISBLANK({ref}))"
                            )
                            # WORST
                            self.content.at[self.result_offset + offset + 8, col] = Formula(
                                f"SUMPRODUCT((NOT(ISBLANK({ref}))*({ref}={max_ref}))+ISBLANK({ref}))"
                            )
                if self.type == "merge":
                    continue
                # values
                # SUM
                self.values.at[self.result_offset + 1, col] = np.nansum(values)
                # AVG
                self.values.at[self.result_offset + 2, col] = np.nanmean(values)
                # DEV
                # catch warnings caused by missing values (nan)
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", "Degrees of freedom <= 0 for slice", RuntimeWarning)
                    self.values.at[self.result_offset + 3, col] = (
                        np.nanstd(values, ddof=1) if len(values) != 1 else np.nan
                    )
                if col < self.summary_refs["min"]["col"]:
                    with np.errstate(invalid="ignore"):
                        # DST
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
                        self.values.at[self.result_offset + 5, col] = -1 * np.nansum(
                            values
                            == np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["min"][name][0]])
                        )
                        # BETTER (values * -1, since higher better)
                        self.values.at[self.result_offset + 6, col] = -1 * np.nansum(
                            values
                            < np.array(
                                self.values.loc[2 : self.result_offset - 1, self.summary_refs["median"][name][0]]
                            )
                        )
                        # WORSE
                        self.values.at[self.result_offset + 7, col] = np.nansum(
                            values
                            > np.array(
                                self.values.loc[2 : self.result_offset - 1, self.summary_refs["median"][name][0]]
                            )
                        ) + np.sum(np.isnan(values))
                        # WORST
                        self.values.at[self.result_offset + 8, col] = np.nansum(
                            values
                            == np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["max"][name][0]])
                        ) + np.sum(np.isnan(values))

    def add_styles(self) -> None:
        """
        Color float results and their summaries.
        Get column formats.
        """
        # remove header
        results = self.values.loc[2:, 1:]

        # might be better to move to write_sheet in the future
        for measure, func in self.measures.items():
            if measure in self.float_occur:
                cols = sorted(self.float_occur[measure])
                if func == "t":
                    diff = 2
                elif func == "to":
                    diff = 0
                    for c in cols:
                        self.formats[c] = "to"
                else:
                    continue

                # no coloring for merge sheet
                if self.type == "merge":
                    continue

                # filter empty rows
                values_df = results.loc[:, cols].dropna(how="all")
                rows = values_df.index

                values = np.array(values_df.values, dtype=float)
                min_values = np.reshape(np.nanmin(values, axis=1), (-1, 1))
                median_values = np.reshape(np.nanmedian(values, axis=1), (-1, 1))
                max_values = np.reshape(np.nanmax(values, axis=1), (-1, 1))
                max_min_diff = (max_values - min_values) > diff
                max_med_diff = (max_values - median_values) > diff

                self.content = (
                    self.content.loc[rows, cols]
                    .mask(
                        (values == min_values) & (values < median_values) & max_min_diff,
                        self.content.loc[rows].map(lambda x: (x, "best")),
                    )
                    .combine_first(self.content)
                )
                self.content = (
                    self.content.loc[rows, cols]
                    .mask(
                        (values == max_values) & (values > median_values) & max_med_diff,
                        self.content.loc[rows].map(lambda x: (x, "worst")),
                    )
                    .combine_first(self.content)
                )

    def export_values(self, file_name: str, metadata: dict[str, list[Any]]) -> None:
        """
        Export values to parquet file.

        Attributes:
            file_name (str): Name of the parquet file.
        """
        # currently only inst sheet exported
        if self.ref_sheet is not None:
            return
        # fill settings
        self.values.iloc[0, :] = self.values.iloc[0, :].ffill()
        # group values by measure
        df = self.values.iloc[2:, [0]].reset_index(drop=True).astype("string")
        df.columns = pd.MultiIndex.from_tuples([("", "instance")], names=["measure", "setting"])
        for m, cols in self.float_occur.items():
            nf = self.values.iloc[2:, sorted(cols)].reset_index(drop=True).astype("float64")
            nf.columns = self.values.iloc[0, sorted(cols)].to_list()
            nf.columns = pd.MultiIndex.from_product([[m], nf.columns], names=["measure", "setting"])
            df = df.join(nf)
        # metadata
        # offset -2 (header) -1 (empty row)
        metadict = {**{"offset": [self.result_offset - 3]}, **metadata}
        metadf = pd.DataFrame({k: pd.Series(v) for k, v in metadict.items()})
        metadf.columns = pd.MultiIndex.from_product([["_metadata"], metadf.columns], names=["measure", "setting"])
        self.values = df.join(metadf)
        #! min,med,max no longer included
        self.values.astype(str).to_parquet(file_name)

    # pylint: disable=too-many-nested-blocks
    def write_sheet(self, xlsxdoc: XLSXDoc) -> None:
        """
        Write sheet to XLSX document.

        Attributes:
            xlsxdoc (XLSXDoc): XLSX document.
        """
        if isinstance(xlsxdoc.workbook, Workbook):
            sheet = xlsxdoc.workbook.add_worksheet(self.name)
            measure_count = len(self.measures.keys())
            for col in range(len(self.content.columns)):
                num_format = xlsxdoc.num_formats.get(self.formats.get(col, "defaultNumber"), "0.00")
                col_width = xlsxdoc.header_width
                for row, cell in enumerate(list(self.content.iloc[:, col])):
                    val = cell
                    color: Optional[str] = None
                    if isinstance(cell, tuple):
                        val, color = cell
                    if isinstance(val, Formula):
                        val = str(val)
                        num_format = xlsxdoc.num_formats.get("formula", "0.00")
                    elif isinstance(val, str):
                        # header
                        if row == 0:
                            if measure_count > 0:
                                xlsxdoc.header_width = min(
                                    xlsxdoc.max_col_width, max(80, cell_autofit_width(val) // measure_count)
                                )
                            else:
                                xlsxdoc.header_width = min(xlsxdoc.max_col_width, 80)
                            col_width = xlsxdoc.header_width
                        else:
                            col_width = min(xlsxdoc.max_col_width, max(col_width, cell_autofit_width(val)))
                    if isinstance(val, (int, float, str, bool)) or val is None:
                        if isinstance(color, str):
                            sheet.write(
                                row,
                                col,
                                val,
                                xlsxdoc.workbook.add_format(
                                    {"bg_color": xlsxdoc.colors[color], "num_format": num_format}
                                ),
                            )
                        else:
                            sheet.write(row, col, val, xlsxdoc.workbook.add_format({"num_format": num_format}))
                    elif isinstance(val, DataValidation):
                        val.write(xlsxdoc, sheet, row, col)
                sheet.set_column_pixels(col, col, col_width)
                sheet.freeze_panes(2, 1)
        else:
            raise ValueError("Trying to write to uninitialized workbook.")


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
            res = f"{self.setting.system.name}-{self.setting.system.version}/{self.setting.name}"
            if add_machine and self.machine:
                res += f" ({self.machine.name})"
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
            # force correct dtype
            self.content[name] = self.content[name].astype(object)
            self.columns[name] = value_type
        # first occurrence of column
        elif self.columns[name] in {"None", "empty"}:
            self.columns[name] = value_type
        # mixed system column
        elif value_type not in {self.columns[name], "None", "empty"}:
            self.columns[name] = "string"
        # leave space for header and add new row if necessary
        if row + 2 not in self.content.index:
            self.content = self.content.reindex(self.content.index.tolist() + [row + 2])
        self.content.at[row + 2, name] = value
