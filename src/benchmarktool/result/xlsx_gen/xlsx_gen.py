"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any, Optional

from xlsxwriter import Workbook  # type: ignore[import-untyped]
from xlsxwriter.color import Color  # type: ignore[import-untyped]

from benchmarktool.result.xlsx_gen.plot_sheets.chart_sheet import ChartSheet
from benchmarktool.result.xlsx_gen.plot_sheets.helper_sheet import HelperSheet
from benchmarktool.result.xlsx_gen.result_sheets.class_sheet import ClassSheet
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.result_sheets.merged_sheet import MergedRunSheet

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage

# pylint: disable=too-many-lines


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

        self.inst_sheet = InstanceSheet("Instances", benchmark, measures)
        self.merged_sheet = MergedRunSheet("Merged_Runs", benchmark, measures, self.inst_sheet)
        self.class_sheet = ClassSheet("Classes", benchmark, measures, self.inst_sheet)
        self.chart_sheet = ChartSheet("Charts", benchmark, measures, self.inst_sheet)
        self.helper_sheet = HelperSheet(
            name="Helper",
            benchmark=benchmark,
            measures=measures,
            instance_sheet=self.inst_sheet,
            merged_run_sheet=self.merged_sheet,
            chart_sheet=self.chart_sheet,
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

        self.helper_sheet.finalize()
        self.chart_sheet.finalize(self.helper_sheet)

    def make_xlsx(self, out: str) -> None:
        """
        Write XLSX file.

        Attributes:
            out (str): Name of the generated XLSX file.
        """
        self.workbook = Workbook(out)

        for sheet in (self.inst_sheet, self.merged_sheet, self.class_sheet, self.helper_sheet, self.chart_sheet):
            sheet.write_sheet(self)
        self.workbook.close()
