"""
Created on Feb 13, 2026

@author: Tom Schmidt
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

import pandas as pd  # type: ignore[import-untyped]
from xlsxwriter import Workbook  # type: ignore[import-untyped]
from xlsxwriter.worksheet import Worksheet  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage
    from benchmarktool.result import spreadsheet  # nocoverage


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
        # array formulas
        if s.startswith("{"):
            return s
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

    def write(self, xlsxdoc: "spreadsheet.XLSXDoc", sheet: Worksheet, row: int, col: int) -> None:
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


# pylint: disable=too-many-instance-attributes
class Chart:
    """
    Helper class representing a spreadsheet chart.
    """

    def __init__(self, title: str, chart_type: str, chart_subtype: Optional[str] = None):
        """
        Initialize Chart.

        Supported types/subtypes:
        - area
          - stacked
          - percent_stacked
        - bar
          - stacked
          - percent_stacked
        - column
          - stacked
          - percent_stacked
        - scatter
          - straight_with_markers
          - straight
          - smooth_with_markers
          - smooth
        - line
          - stacked
          - percent_stacked
        - radar
          - with_markers
          - filled
        - pie
        - doughnut
        - stock

        Attributes:
            title (str):      Title of the chart.
            chart_type (str): Type of the chart.
            chart_subtype (Optional[str]): Subtype of the chart.
        """
        self.title = title
        self.chart_type = chart_type
        self.chart_subtype = chart_subtype

        self.series: list[dict[str, Any]] = []

        self.x_axis_params: dict[str, Any] = {}
        self.y_axis_params: dict[str, Any] = {}
        self.size_params: dict[str, Any] = {}
        self.legend_params: dict[str, Any] = {}
        self.style: int = 2

    def add_series(self, series_options: dict[str, Any]) -> None:
        """
        Add series to the chart.

        Attributes:
            series_options (dict[str, Any]): Series options.
        """
        self.series.append(series_options)

    def set_params(
        self,
        *,
        x_axis: dict[str, Any] = {},
        y_axis: dict[str, Any] = {},
        size: dict[str, Any] = {},
        legend: dict[str, Any] = {},
        style: Optional[int] = None,
    ) -> None:
        """
        Set chart parameters.

        Attributes:
            x_axis (dict[str, Any]): X axis parameters.
            y_axis (dict[str, Any]): Y axis parameters.
            size (dict[str, Any]):   Size parameters.
            legend (dict[str, Any]): Legend parameters.
            style (Optional[int]):   Chart style (1-48).
        """
        if x_axis:
            self.x_axis_params = x_axis
        if y_axis:
            self.y_axis_params = y_axis
        if size:
            self.size_params = size
        if legend:
            self.legend_params = legend
        if style is not None:
            self.style = style

    def write(self, xlsxdoc: "spreadsheet.XLSXDoc", sheet: Worksheet, row: int, col: int) -> None:
        """
        Write to XLSX document sheet.

        Attributes:
            xlsxdoc (XLSXDoc): XLSX document.
            sheet (Worksheet): XLSX worksheet.
            row (int):         Row index.
            col (int):         Column index.
        """
        if isinstance(xlsxdoc.workbook, Workbook):
            # create chart
            if self.chart_subtype:
                chart = xlsxdoc.workbook.add_chart({"type": self.chart_type, "subtype": self.chart_subtype})
            else:
                chart = xlsxdoc.workbook.add_chart({"type": self.chart_type})

            # set parameters
            chart.set_title({"name": self.title})
            if self.x_axis_params:
                chart.set_x_axis(self.x_axis_params)
            if self.y_axis_params:
                chart.set_y_axis(self.y_axis_params)
            if self.size_params:
                chart.set_size(self.size_params)
            if self.legend_params:
                chart.set_legend(self.legend_params)
            chart.set_style(self.style)

            # add series
            for series in self.series:
                chart.add_series(series)

            # write to sheet
            sheet.insert_chart(
                row,
                col,
                chart,
            )
        else:
            raise ValueError("Trying to write to uninitialized workbook.")

    def __eq__(self, other: object) -> bool:
        """
        Equality operator.

        Attributes:
            other (object): Other Chart object.
        """
        if not isinstance(other, Chart):
            raise TypeError("Comparison with non Chart object.")
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        """
        Hash function.
        """
        return hash(
            (
                self.title,
                self.chart_type,
                self.chart_subtype,
                repr(sorted(list(map(lambda x: repr(x.items()), self.series)))),
            )
        )


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
