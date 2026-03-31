"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

import warnings
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from xlsxwriter import Workbook  # type: ignore[import-untyped]
from xlsxwriter.utility import cell_autofit_width  # type: ignore[import-untyped]

from benchmarktool.result.xlsx_gen.spreadsheet import DataValidation, Formula, Sheet, SystemBlock, get_cell_index

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage
    from benchmarktool.result.xlsx_gen.xlsx_gen import XLSXDoc  # nocoverage


# pylint: disable=too-many-instance-attributes
class ResultSheet(Sheet):
    """
    A sheet displaying results.
    """

    def __init__(self, name: str, benchmark: "result.BenchmarkMerge", measures: dict[str, Any]):
        super().__init__(name, benchmark, measures)

        self.system_blocks: dict[tuple[Any, Any], SystemBlock] = {}
        self.types: dict[str, str] = {}
        self.machines: set["result.Machine"] = set()

        self.summary_refs: dict[str, Any] = {}
        self.values = pd.DataFrame()
        self.float_occur: dict[str, set[int]] = {}

        self.result_offset = 0
        self.col_offset = 0

        self.formats: dict[int, str] = {}

        self.prepare()

    def prepare(self) -> None:
        """
        Prepare the sheet.
        """
        raise NotImplementedError

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add a run specification to the sheet.

        Attributes:
            runspec (Runspec): Run specification.
        """
        raise NotImplementedError

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
        self.content = self.content.astype(object).where(self.content.notna(), None)

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

    def add_row_summary(self) -> None:
        """
        Add row summary (min, max, median).
        """
        col = self.col_offset
        for col_name in ["min", "median", "max"]:
            block = SystemBlock(None, None)
            block.offset = col
            self.summary_refs[col_name] = {"col": col}
            self.values.at[0, block.offset] = col_name
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

    # pylint: disable=too-many-positional-arguments
    def _add_summary_formula(
        self, block: SystemBlock, operator: str, measure: str, float_occur: dict[str, set[int]], col: int
    ) -> None:
        """
        Add row summary formula.

        Attributes:
            block (SystemBlock):          SystemBlock to which summary is added.
            operator (str):               Summary operator.
            measure (str):                Name of the measure to be summarized.
            float_occur (dict[str, set[int]]): Dict containing column references of float columns.
            col (int):                    Current column index.
        """
        self.values[col] = self.values[col].astype(object)
        for row in range(self.result_offset - 2):
            ref_range = ",".join(get_cell_index(col_ref, row + 2, True) for col_ref in sorted(float_occur[measure]))
            values = np.array(self.values.loc[2 + row, sorted(float_occur[measure])], float)
            # don't write formula if full row is nan
            if np.isnan(values).all():
                self.values.at[2 + row, col] = np.nan
            else:
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
        self.content = self.content.reindex(sorted(self.content.columns), axis=1)

    # pylint: disable=too-many-branches, too-many-nested-blocks
    def write_sheet(self, xlsxdoc: "XLSXDoc") -> None:
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
