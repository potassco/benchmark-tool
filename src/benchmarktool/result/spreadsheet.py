"""
Created on Feb 13, 2026

@author: Tom Schmidt
"""

import warnings
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from xlsxwriter import Workbook  # type: ignore[import-untyped]
from xlsxwriter.color import Color  # type: ignore[import-untyped]
from xlsxwriter.utility import cell_autofit_width  # type: ignore[import-untyped]

from benchmarktool.result.spreadsheet_utils import DataValidation, Formula, SystemBlock, get_cell_index  # nocoverage

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage

# pylint: disable=too-many-lines


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

        self.inst_sheet = InstanceSheet("Instances", benchmark, measures)
        self.merged_sheet = MergedRunSheet("Merged_Runs", benchmark, measures, self.inst_sheet)
        self.class_sheet = ClassSheet("Classes", benchmark, measures, self.inst_sheet)
        self.chart_sheet = ChartSheet("Charts", benchmark, measures, self.inst_sheet)
        self.helper_sheet = HelperSheet(
            "Helper", benchmark, measures, self.inst_sheet, self.merged_sheet, self.chart_sheet
        )

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Attributes:
            runspec (Runspec): Run specification.
        """
        self.inst_sheet.add_runspec(runspec)
        self.merged_sheet.add_runspec(runspec)
        self.class_sheet.add_runspec(runspec)

    def finalize(self) -> None:
        """
        Finalize the sheet, e.g., by collecting content and adding summaries.
        """
        self.inst_sheet.finalize()
        self.merged_sheet.finalize()
        self.class_sheet.finalize()

        self.chart_sheet.prepare()
        self.helper_sheet.prepare()
        self.helper_sheet.finalize()
        self.chart_sheet.finalize(self.helper_sheet)

    def make_xlsx(self, out: str) -> None:
        """
        Write XLSX file.

        Attributes:
            out (str): Name of the generated XLSX file.
        """
        print(self.chart_sheet.content)
        print(self.helper_sheet.content)
        self.workbook = Workbook(out)

        for sheet in (self.inst_sheet, self.merged_sheet, self.class_sheet, self.helper_sheet, self.chart_sheet):
            sheet.write_sheet(self)
        self.workbook.close()


class Sheet:
    """
    Class representing a sheet in the XLSX document.
    """

    def __init__(self, name: str, benchmark: "result.Benchmark", measures: dict[str, Any]):
        self.name = name
        self.benchmark = benchmark
        self.measures = measures
        self.content = pd.DataFrame()

        self.prepare()

    def prepare(self) -> None:
        """
        Prepare the sheet.
        """
        raise NotImplementedError

    def finalize(self) -> None:
        """
        Finalize the sheet, e.g., by collecting content and adding summaries.
        """
        raise NotImplementedError


class ResultSheet(Sheet):
    """
    A sheet displaying results.
    """

    def __init__(self, name: str, benchmark: "result.Benchmark", measures: dict[str, Any]):

        self.system_blocks: dict[tuple[Any, Any], SystemBlock] = {}
        self.types: dict[str, str] = {}
        self.machines: set["result.Machine"] = set()

        self.summary_refs: dict[str, Any] = {}
        self.values = pd.DataFrame()
        self.float_occur: dict[str, set[Any]] = {}

        self.result_offset = 0
        self.col_offset = 0

        self.formats: dict[int, str] = {}

        super().__init__(name, benchmark, measures)

    def finalize(self) -> None:
        """
        Finalize the sheet, e.g., by collecting content and adding summaries.
        """
        col = 1
        # join results of different blocks
        for block in sorted(self.system_blocks.values()):
            self.content = self.content.join(block.content)
            self.content = self.content.set_axis(list(range(len(self.content.columns))), axis=1)
            self.content.at[0, col] = block.gen_name(len(self.machines) > 1)
            col += len(block.columns)

        self.col_offset = col

        self._finalize_results()
        self._obtain_values()

        # defragmentation (temporary workaround)
        self.content = self.content.copy()
        self.values = self.values.copy()

        # add summaries
        self.values = self.values.replace({None: np.nan})
        self.add_row_summary()
        self.values = self.values.replace({None: np.nan})
        self.add_col_summary()

        # color cells
        self.add_styles()

        # replace all undefined cells with None (empty cell)
        self.content = self.content.fillna(np.nan).replace(np.nan, None)

    def _finalize_results(self) -> None:
        """
        Finalize the results of the sheet.
        """
        raise NotImplementedError

    def _obtain_values(self) -> None:
        """
        Obtain values from the sheet.
        """
        raise NotImplementedError

    def add_col_summary(self) -> None:
        """
        Add column summary.
        """
        raise NotImplementedError

    def add_row_summary(self) -> None:
        """
        Add row summary (min, max, median).
        """
        col = self.col_offset
        for col_name in ["min", "median", "max"]:
            block = SystemBlock(None, None)
            block.offset = col
            self.summary_refs[col_name] = {"col": col}
            # measures = sorted(self.float_occur.keys()) if not self.measures else list(self.measures.keys())
            for measure in sorted(self.float_occur.keys()):
                # if measure in self.float_occur:
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
        self, block: SystemBlock, operator: str, measure: str, float_occur: dict[str, Any], col: int
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
        raise NotImplementedError

    def _add_default_col_summary_formulas(self, col: int, summaries: list[tuple[int, str, str, str, str]]) -> None:
        """
        Add column summary formulas.

        Attributes:
            col (int): Current column index.
            summaries (list[tuple[int, str, str, str, str]]): List of summary specifications containing:
                - offset (int): Row offset for the summary.
                - ref (str): Cell range reference for the summarized values.
                - min_ref (str): Cell range reference for the minimum values.
                - med_ref (str): Cell range reference for the median values.
                - max_ref (str): Cell range reference for the maximum values.
        """
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

    def _add_default_col_summary_values(self, col: int, name: str, values: np.ndarray) -> None:
        """
        Add column summary values.

        Attributes:
            col (int): Current column index.
            name (str): Name of the column.
            values (np.ndarray): Array of values for the column.
        """
        # values
        # SUM
        self.values.at[self.result_offset + 1, col] = np.nansum(values)
        # AVG
        self.values.at[self.result_offset + 2, col] = np.nanmean(values)
        # DEV
        # catch warnings caused by missing values (nan)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "Degrees of freedom <= 0 for slice", RuntimeWarning)
            self.values.at[self.result_offset + 3, col] = np.nanstd(values, ddof=1) if len(values) != 1 else np.nan
        if col < self.summary_refs["min"]["col"]:
            with np.errstate(invalid="ignore"):
                # DST
                self.values.at[self.result_offset + 4, col] = (
                    np.nansum(
                        (
                            values
                            - np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["min"][name][0]])
                        )
                        ** 2
                    )
                    ** 0.5
                )
                # BEST (values * -1, since higher better)
                self.values.at[self.result_offset + 5, col] = -1 * np.nansum(
                    values == np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["min"][name][0]])
                )
                # BETTER (values * -1, since higher better)
                self.values.at[self.result_offset + 6, col] = -1 * np.nansum(
                    values < np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["median"][name][0]])
                )
                # WORSE
                self.values.at[self.result_offset + 7, col] = np.nansum(
                    values > np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["median"][name][0]])
                ) + np.sum(np.isnan(values))
                # WORST
                self.values.at[self.result_offset + 8, col] = np.nansum(
                    values == np.array(self.values.loc[2 : self.result_offset - 1, self.summary_refs["max"][name][0]])
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


class InstanceSheet(ResultSheet):
    """
    A sheet displaying instance results.
    """

    def __init__(self, name, benchmark, measures):
        self.runs: Optional[int] = None
        super().__init__(name, benchmark, measures)

    def prepare(self) -> None:
        """
        Prepare the sheet.
        """
        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        run_summary = True
        row = 2
        for benchclass in self.benchmark:
            for instance in benchclass:
                self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                row += instance.values["max_runs"]
                if self.runs is None:
                    self.runs = instance.values["max_runs"]
                elif self.runs != instance.values["max_runs"]:  # nocoverage
                    run_summary = False

        self.result_offset = row
        for idx, label in enumerate(["SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"], 1):
            self.content.loc[self.result_offset + idx] = label

        # run summary
        if run_summary and self.runs and self.runs > 1:
            selection = DataValidation(
                {
                    "validate": "list",
                    "source": list(range(1, self.runs + 1)),
                    "input_message": "Select run number",
                },
                1,
                "input",
            )

            for idx, label in enumerate(
                ["Select run:", selection, "SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"], 10
            ):
                self.content.loc[self.result_offset + idx] = label

        # fill missing rows
        self.content = self.content.reindex(list(range(self.content.index.max() + 1))).replace(np.nan, None)

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add a run specification to the sheet.

        Attributes:
            runspec (Runspec): Run specification.
        """
        key = (runspec.setting, runspec.machine)
        block = self.system_blocks.setdefault(key, SystemBlock(runspec.setting, runspec.machine))
        if block.machine:
            self.machines.add(block.machine)

        for benchclass_result in runspec:
            for instance_result in benchclass_result:
                self.add_instance_results(block, instance_result)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]
                    # mixed measure
                    elif block.columns[m] not in {self.types[m], "None", "empty"}:
                        self.types[m] = "string"

    def add_instance_results(
        self,
        block: SystemBlock,
        instance_result: "result.InstanceResult",
    ) -> None:
        """
        Add instance results to SystemBlock.

        Attributes:
            block (SystemBlock):                 SystemBlock to which results are added.
            instance_result (InstanceResult):    InstanceResult.
        """
        for run in instance_result:
            for name, value_type, value in run.iter(self.measures):
                self.measures.setdefault(name, None)
                if value_type == "int":
                    value_type = "float"
                elif value_type not in {"float", "None", "empty"}:
                    value_type = "string"
                if value_type == "float":
                    block.add_cell(
                        instance_result.instance.values["row"] + run.number - 1, name, value_type, float(value)
                    )
                elif value_type in {"None", "empty"}:
                    block.add_cell(instance_result.instance.values["row"] + run.number - 1, name, value_type, np.nan)
                else:
                    block.add_cell(instance_result.instance.values["row"] + run.number - 1, name, value_type, value)

    def _finalize_results(self):
        """
        Finalize the results of the sheet.
        """
        for column in self.content:
            name = self.content.at[1, column]
            if self.types.get(name, "") in ["float", "classresult", "merged_runs"]:
                self.float_occur.setdefault(name, set()).add(column)
            # defragmentation (temporary workaround)
            self.content = self.content.copy()
            self.values = self.values.copy()

    def _obtain_values(self):
        """
        Obtain values from the sheet.
        """
        self.values = self.content.copy()

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
                if self.runs is not None and self.runs > 1:
                    sel_runs = _get_run_select(run_select_cell, self.runs, col, False)
                    ref_runs = _get_run_filter(summaries[0][1], sel_runs)
                    min_runs = _get_run_filter(
                        summaries[0][2], _get_run_select(run_select_cell, self.runs, self.summary_refs["min"][name][0])
                    )
                    med_runs = _get_run_filter(
                        summaries[0][3],
                        _get_run_select(run_select_cell, self.runs, self.summary_refs["median"][name][0]),
                    )
                    max_runs = _get_run_filter(
                        summaries[0][4], _get_run_select(run_select_cell, self.runs, self.summary_refs["max"][name][0])
                    )
                    summaries.append((11, ref_runs, min_runs, med_runs, max_runs))

                self._add_default_col_summary_formulas(col, summaries)
                self._add_default_col_summary_values(col, name, values)

    def export_values(self, file_name: str, metadata: dict[str, list[Any]]) -> None:
        """
        Export values to parquet file.

        Attributes:
            file_name (str): Name of the parquet file.
        """
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


class ClassSheet(ResultSheet):
    """
    A sheet displaying benchmark class summaries.
    """

    def __init__(self, name: str, benchmark: "result.Benchmark", measures: dict[str, Any], ref_sheet: InstanceSheet):
        self.ref_sheet = ref_sheet
        super().__init__(name, benchmark, measures)

    def prepare(self) -> None:
        """
        Prepare the sheet.
        """
        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        row = 2
        for benchclass in self.benchmark:
            self.content.loc[row] = benchclass.name
            row += 1

        self.result_offset = row
        for idx, label in enumerate(["SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"], 1):
            self.content.loc[self.result_offset + idx] = label

        # fill missing rows
        self.content = self.content.reindex(list(range(self.content.index.max() + 1))).replace(np.nan, None)

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add a run specification to the sheet.

        Attributes:
            runspec (Runspec): Run specification.
        """
        key = (getattr(runspec, "setting", None), getattr(runspec, "machine", None))
        block = self.system_blocks.setdefault(
            key, SystemBlock(getattr(runspec, "setting", None), getattr(runspec, "machine", None))
        )
        if block.machine:
            self.machines.add(block.machine)

        for benchclass_result in runspec:
            benchclass_summary: dict[str, Any] = {}
            for instance_result in benchclass_result:
                self.add_instance_results_to_benchclass_summary(instance_result, benchclass_summary)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]
                    # mixed measure
                    elif block.columns[m] not in {self.types[m], "None", "empty"}:
                        self.types[m] = "string"
            self.add_benchclass_summary(block, benchclass_result, benchclass_summary)
            for m in block.columns:
                if m not in self.types or self.types[m] in {"None", "empty"}:
                    self.types[m] = block.columns[m]

    def add_instance_results_to_benchclass_summary(
        self,
        instance_result: "result.InstanceResult",
        benchclass_summary: dict[str, Any],
    ) -> None:
        """
        Aggregate instance results to benchmark class summary.

        Attributes:
            instance_result (InstanceResult): Instance result.
            benchclass_summary (dict[str, Any]): Benchmark class summary.
        """
        for run in instance_result:
            for name, value_type, value in run.iter(self.measures):
                self.measures.setdefault(name, None)
                if value_type == "int":
                    value_type = "float"
                elif value_type not in {"float", "None", "empty"}:
                    value_type = "string"
                if value_type == "float" and self.ref_sheet.types.get(name, "") == "float":
                    if benchclass_summary.get(name) is None:
                        benchclass_summary[name] = (0.0, 0)
                    benchclass_summary[name] = (
                        float(value) + benchclass_summary[name][0],
                        1 + benchclass_summary[name][1],
                    )
                else:
                    if name not in benchclass_summary:
                        benchclass_summary[name] = None

    def add_benchclass_summary(
        self, block: SystemBlock, benchclass_result: "result.ClassResult", benchclass_summary: dict[str, Any]
    ) -> None:
        """
        Add benchmark class summary to a system block.

        Attributes:
            block (SystemBlock): System block.
            benchclass_result (ClassResult): Benchmark class result.
            benchclass_summary (dict[str, Any]): Benchmark class summary.
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

    def _finalize_results(self):
        """
        Finalize the results of the sheet.
        """
        for column in self.content:
            name = self.content.at[1, column]
            if self.types.get(name, "") == "classresult":
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

    def _obtain_values(self):
        """
        Obtain values from the sheet.
        """
        self.values = self.values.reindex(index=self.content.index, columns=self.content.columns)
        self.values = self.values.combine_first(self.content)

    def add_col_summary(self) -> None:
        """
        Add column summary if applicable to column type.
        """
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

                self._add_default_col_summary_formulas(col, summaries)
                self._add_default_col_summary_values(col, name, values)


class MergedRunSheet(ResultSheet):
    """
    A sheet displaying merged runs.
    """

    def __init__(self, name: str, benchmark: "result.Benchmark", measures: dict[str, Any], ref_sheet: InstanceSheet):
        self.ref_sheet = ref_sheet
        super().__init__(name, benchmark, measures)

    def prepare(self) -> None:
        """
        Prepare the merged run sheet.
        """
        self.content[0] = None
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
        for benchclass in self.benchmark:
            for instance in benchclass:
                self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                row += 1

        self.result_offset = row
        for idx, label in enumerate(["SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"], 1):
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
            instance_summary: dict[result.InstanceResult, dict[str, Any]] = {}
            for instance_result in benchclass_result:
                self.add_instance_results_to_instance_summary(instance_result, instance_summary)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]
                    # mixed measure
                    elif block.columns[m] not in {self.types[m], "None", "empty"}:
                        self.types[m] = "string"
            if self.ref_sheet:
                for instance_result in benchclass_result:
                    self.add_merged_instance_results(block, instance_result, instance_summary)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]

    def add_instance_results_to_instance_summary(
        self,
        instance_result: "result.InstanceResult",
        instance_summary: dict["result.InstanceResult", dict[str, Any]],
    ) -> None:
        """
        Add instance results to summary.

        Attributes:
            instance_result (InstanceResult):    InstanceResult.
            instance_summary (dict[InstanceResult, dict[str, Any]]): Summary of instance results.
        """
        instance_summary[instance_result] = {}
        for run in instance_result:
            for name, value_type, _ in run.iter(self.measures):
                self.measures.setdefault(name, None)
                instance_summary[instance_result].setdefault(name, False)
                if value_type == "int":
                    value_type = "float"
                elif value_type not in {"float", "None", "empty"}:
                    value_type = "string"
                if value_type == "float" and self.ref_sheet.types.get(name, "") == "float":
                    instance_summary[instance_result][name] = True

    def add_merged_instance_results(
        self,
        block: SystemBlock,
        instance_result: "result.InstanceResult",
        instance_summary: dict["result.InstanceResult", dict[str, Any]],
    ) -> None:
        """
        Add merged instance results to SystemBlock.

        Attributes:
            block (SystemBlock):              SystemBlock to which results are added.
            instance_result (InstanceResult): InstanceResult.
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

    def _finalize_results(self):
        """
        Finalize the results of the sheet.
        """
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
            if self.types.get(name, "") in ["float", "classresult", "merged_runs"]:
                self.float_occur.setdefault(name, set()).add(column)
            # defragmentation (temporary workaround)
            self.content = self.content.copy()
            self.values = self.values.copy()

    def _obtain_values(self):
        """
        Obtain values from the sheet.
        """
        self.values = self.values.reindex(index=self.content.index, columns=self.content.columns)
        self.values = self.values.combine_first(self.content)

    def add_col_summary(self) -> None:
        """
        Add column summary if applicable to column type.
        """
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

                self._add_default_col_summary_formulas(col, summaries)


class HelperSheet(Sheet):
    """
    A helper sheet to prepare data for charts.
    """

    def __init__(
        self,
        name,
        benchmark,
        measures,
        instance_sheet: InstanceSheet,
        merged_run_sheet: MergedRunSheet,
        chart_sheet: Sheet,
    ):
        self.name = name
        self.benchmark = benchmark
        self.measures = measures
        self.content = pd.DataFrame()

        self.instance_sheet = instance_sheet
        self.merged_run_sheet = merged_run_sheet
        self.chart_sheet = chart_sheet

        self.setting_n = 0
        self.col_offset = 0
        self.instance_n = 0

        self.float_occur: dict[str, list[int]] = {}
        self.sorted_cols: dict[str, int] = {}
        self.aggregated_cols: dict[str, int] = {}

    def prepare(self) -> None:
        """
        Prepare the helper sheet.
        """
        for measure, cols in self.instance_sheet.float_occur.items():
            s_cols = sorted(cols)
            self.float_occur[measure] = s_cols
            if self.setting_n == 0:
                self.setting_n = len(s_cols)
            if self.col_offset == 0 and len(s_cols) > 1:
                self.col_offset = s_cols[1] - s_cols[0]

        # self.instance_n = self.instance_sheet.result_offset - 2
        self.content[0] = None

        # lookup table, col 0,1
        lookup_row = 1
        for measure in self.float_occur.keys():
            self.content.loc[lookup_row, 0] = measure
            self.content.loc[lookup_row, 1] = self.float_occur[measure][0]
            lookup_row += 1

        start_col = 3
        start_row = 1
        col = start_col
        for i in range(2):
            if i == 0:
                sheet = "Instances"
                sheet_ref = self.instance_sheet
            else:
                sheet = "Merged_Runs"
                sheet_ref = self.merged_run_sheet

            self.instance_n = sheet_ref.result_offset - 2
            self.plot_offset = self.instance_n + 6

            # index columns
            self.content.loc[start_row + 2, col] = "index"
            index_col = col
            self.content.loc[self.plot_offset, col] = "pre-plot"
            for r in range(self.instance_n):
                self.content.loc[r + start_row + 3, col] = r + 1
                self.content.loc[self.plot_offset + r + start_row, col] = r + 1

            col += 1
            for setting in range(self.setting_n):
                # setting refs
                if setting == 0:
                    self.content.loc[start_row, col] = Formula(
                        f"=VLOOKUP(Charts!{self.chart_sheet.measure_select},{get_cell_index(0, start_row)}:{get_cell_index(1, lookup_row - 1)},2,FALSE)"
                    )
                else:
                    self.content.loc[start_row, col] = Formula(
                        f"={get_cell_index(start_col + 1, start_row)}+{setting*self.col_offset}"
                    )
                self.content.loc[start_row + 1, col] = Formula(
                    f"={sheet}!{get_cell_index(1 + setting*self.col_offset, 0)}"
                )
                # headers
                self.content.loc[start_row + 2, col] = "values"
                self.content.loc[start_row + 2, col + 1] = "sorted"
                self.content.loc[start_row + 2, col + 2] = "aggregated"

                get_inst_col = (
                    lambda ref_row, ref_col: f'INDIRECT(ADDRESS({get_cell_index(index_col, ref_row, True, False)}+2,{get_cell_index(ref_col, start_row, False, True)}+1,,,"{sheet}"))'
                )
                inst_row = start_row + 3
                for row in range(self.instance_n):
                    # values
                    self.content.loc[inst_row + row, col] = Formula(
                        f'=IF({get_inst_col(row + start_row + 3, col)}="","",{get_inst_col(row + start_row + 3, col)})'
                    )
                    # sorted
                    self.content.loc[inst_row + row, col + 1] = Formula(
                        f'=IFERROR(SMALL({get_cell_index(col, inst_row, True, True)}:{get_cell_index(col, inst_row + self.instance_n - 1, True, True)},ROW()-ROW({get_cell_index(col + 1, inst_row, True, True)})+1),"")'
                    )
                    # aggregated
                    self.content.loc[inst_row + row, col + 2] = Formula(
                        f'=IFERROR(SUM({get_cell_index(col + 1, inst_row, True, True)}:{get_cell_index(col + 1, inst_row + row, True, True)}),"")'
                    )
                    if row == self.instance_n - 1:
                        # sorted
                        self.content.loc[self.plot_offset + 1 + row, col + 1] = Formula(
                            f"={get_cell_index(col + 1, inst_row + row)}"
                        )
                        # aggregated
                        self.content.loc[self.plot_offset + 1 + row, col + 2] = Formula(
                            f"={get_cell_index(col + 2, inst_row + row)}"
                        )
                    else:
                        # sorted
                        self.content.loc[self.plot_offset + 1 + row, col + 1] = Formula(
                            f'=IF({get_cell_index(col + 1, inst_row + row )}={get_cell_index(col + 1, inst_row + row + 1)}, "", {get_cell_index(col + 1, inst_row + row)})'
                        )
                        # aggregated
                        self.content.loc[self.plot_offset + 1 + row, col + 2] = Formula(
                            f'=IF({get_cell_index(col + 2, inst_row + row )}={get_cell_index(col + 2, inst_row + row + 1)}, "", {get_cell_index(col + 2, inst_row + row)})'
                        )

                col += 3
            col += 1

        self.content = self.content.reindex(
            index=list(range(self.content.index.max() + 1)), columns=list(range(self.content.columns.max() + 1))
        ).replace(np.nan, None)

    def finalize(self):
        self.content = self.content.fillna(np.nan).replace(np.nan, None)

    def write_sheet(self, xlsxdoc: XLSXDoc) -> None:
        """
        Write sheet to XLSX document.

        Attributes:
            xlsxdoc (XLSXDoc): XLSX document.
        """
        if isinstance(xlsxdoc.workbook, Workbook):
            sheet = xlsxdoc.workbook.add_worksheet(self.name)
            for col in range(len(self.content.columns)):
                for row, cell in enumerate(list(self.content.iloc[:, col])):
                    val = cell
                    if isinstance(val, Formula):
                        val = str(val)
                        print(val)
                    if isinstance(val, (int, float, str, bool)) or val is None:
                        sheet.write(row, col, val)
        else:
            raise ValueError("Trying to write to uninitialized workbook.")


class ChartSheet(Sheet):
    """
    A sheet for charts.
    """

    def __init__(self, name, benchmark, measures: dict[str, Any], instance_sheet: InstanceSheet):
        self.name = name
        self.benchmark = benchmark
        self.measures = measures
        self.content = pd.DataFrame()

        self.merge_select = ""
        self.measure_select = ""
        self.instance_sheet = instance_sheet

    def prepare(self) -> None:
        """
        Prepare the chart sheet. Call after instance sheet is finalized.
        """
        self.measures = (
            sorted(self.instance_sheet.float_occur.keys()) if not self.measures else list(self.measures.keys())
        )

        self.content[0] = None
        self.content[1] = None
        self.content.loc[1, 1] = "Merge criteria:"
        self.content.loc[2, 1] = DataValidation(
            {
                "validate": "list",
                "source": ["none", "average", "median", "min", "max"],
                "input_message": "Select merge criteria",
            },
            "none",
            "input",
        )
        self.merge_select = get_cell_index(1, 2, True, True)

        self.content.loc[1, 3] = "Measure criteria:"
        self.content.loc[2, 3] = DataValidation(
            {
                "validate": "list",
                "source": list(self.instance_sheet.float_occur.keys()),
                "input_message": "Select measure criteria",
            },
            self.measures[0] if self.measures else "",
            "input",
        )
        self.measure_select = get_cell_index(3, 2, True, True)

        self.content = self.content.reindex(
            index=list(range(self.content.index.max() + 1)), columns=list(range(self.content.columns.max() + 1))
        ).replace(np.nan, None)

    def finalize(self, helper_sheet: HelperSheet) -> None:
        """
        Finalize the chart sheet. Call after helper sheet is finalized.
        """
        self.content = self.content.fillna(np.nan).replace(np.nan, None)

    def write_sheet(self, xlsxdoc: XLSXDoc) -> None:
        """
        Write sheet to XLSX document.

        Attributes:
            xlsxdoc (XLSXDoc): XLSX document.
        """
        if isinstance(xlsxdoc.workbook, Workbook):
            sheet = xlsxdoc.workbook.add_worksheet(self.name)
            for col in range(len(self.content.columns)):
                for row, cell in enumerate(list(self.content.iloc[:, col])):
                    val = cell
                    if isinstance(val, Formula):
                        val = str(val)
                    if isinstance(val, (int, float, str, bool)) or val is None:
                        sheet.write(row, col, val)
                    elif isinstance(val, DataValidation):
                        val.write(xlsxdoc, sheet, row, col)
        else:
            raise ValueError("Trying to write to uninitialized workbook.")


def __main__():
    from benchmarktool.result import parser  # nocoverage

    p = parser.Parser()
    res = p.parse("p2eval.xml")
    projects = []
    for project in res.projects.values():
        projects.append(project)
    benchmark_merge = res.merge(projects)

    # doc = XLSXDoc(benchmark_merge, measures, max_col_width)
    intance_sheet = InstanceSheet("Instances", benchmark_merge, {})
    class_sheet = ClassSheet("Classes", benchmark_merge, {}, intance_sheet)
    merge_sheet = MergedRunSheet("Merged", benchmark_merge, {}, intance_sheet)
    chart_sheet = ChartSheet("Charts", benchmark_merge, {}, intance_sheet)
    helper_sheet = HelperSheet("Helper", benchmark_merge, {}, intance_sheet, chart_sheet)
    for project in projects:
        for runspec in project:
            intance_sheet.add_runspec(runspec)
            class_sheet.add_runspec(runspec)
            merge_sheet.add_runspec(runspec)
    intance_sheet.finalize()
    chart_sheet.prepare()
    helper_sheet.prepare()
    class_sheet.finalize()
    merge_sheet.finalize()
    helper_sheet.finalize()
    chart_sheet.finalize(helper_sheet)
    # print(intance_sheet.content)
    # print(class_sheet.content)
    # print(merge_sheet.content)
    print(chart_sheet.content)
    print(helper_sheet.content)


if __name__ == "__main__":
    __main__()
