"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any, Optional

from xlsxwriter import Workbook  # type: ignore[import-untyped]

from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.spreadsheet import Chart, DataValidation, Formula, Sheet, get_cell_index

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage
    from benchmarktool.result.xlsx_gen.plot_sheets.helper_sheet import HelperSheet  # nocoverage
    from benchmarktool.result.xlsx_gen.xlsx_gen import XLSXDoc  # nocoverage


class ChartSheet(Sheet):
    """
    A sheet for charts.
    """

    def __init__(
        self, name: str, benchmark: "result.BenchmarkMerge", measures: dict[str, Any], instance_sheet: InstanceSheet
    ):
        super().__init__(name, benchmark, measures)

        self.merge_select = ""
        self.measure_select = ""
        self.instance_sheet = instance_sheet

        self.prepare()

    def prepare(self) -> None:
        """
        Prepare the chart sheet.
        """
        self.content[0] = None
        self.content[1] = None
        self.content.loc[1, 1] = "Select merge criteria:"
        self.content.loc[2, 1] = DataValidation(
            {
                "validate": "list",
                "source": ["none", "average", "median", "min", "max"],
                "input_message": "Select how runs should be merged. 'none' means no merging.",
            },
            "none",
            "input",
        )
        self.merge_select = get_cell_index(1, 2, True, True)

        self.content.loc[1, 5] = "Select measure:"
        self.content.loc[2, 5] = "PLACEHOLDER: Measure select"
        self.measure_select = get_cell_index(5, 2, True, True)
        self.content = self.content.astype(object)

    def finalize(self, helper_sheet: Optional["HelperSheet"] = None) -> None:
        """
        Finalize the chart sheet. Call after helper sheet is finalized.

        Attributes:
            helper_sheet (Optional[HelperSheet]): Helper sheet for chart data. Required for adding charts
        """
        if helper_sheet is None:
            raise ValueError("Helper sheet is required to finalize chart sheet.")
        # measure select
        measures = sorted(self.instance_sheet.float_occur.keys())
        self.content.loc[2, 5] = DataValidation(
            {
                "validate": "list",
                "source": measures,
                "input_message": "Select measure to display.",
            },
            measures[0] if measures else "",
            "input",
        )

        survivor_chart = Chart("Survivor", "scatter", "straight")
        cactus_chart = Chart("Cactus", "scatter", "straight")
        cdf_chart = Chart("CDF", "scatter", "straight")

        # offsets
        sorted_index_offset = 0
        sorted_offset = 1
        aggregated_index_offset = 2
        aggregated_offset = 3

        for setting in range(helper_sheet.setting_n):
            setting_offset = 4 * setting
            survivor_chart.add_series(
                {
                    "name": f"""Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset,
                        helper_sheet.plot_row - 2,
                    )}""",
                    # x-axis aggregated values
                    "categories": f"""(Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + aggregated_offset,
                        helper_sheet.plot_row,
                    )}:{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + aggregated_offset,
                        helper_sheet.plot_row + 2*helper_sheet.instance_n,
                    )})""",
                    # y-axis index
                    "values": f"""(Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + aggregated_index_offset,
                        helper_sheet.plot_row,
                    )}:{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + aggregated_index_offset,
                        helper_sheet.plot_row + 2*helper_sheet.instance_n,
                    )})""",
                }
            )
            survivor_chart.set_params(
                x_axis={"name": f"={self.name}!{self.measure_select}"}, y_axis={"name": "# of Instances"}
            )
            cactus_chart.add_series(
                {
                    "name": f"""Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset,
                        helper_sheet.plot_row - 2,
                    )}""",
                    # x-axis index
                    "categories": f"""(Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_index_offset,
                        helper_sheet.plot_row,
                    )}:{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_index_offset,
                        helper_sheet.plot_row + 2*helper_sheet.instance_n,
                    )})""",
                    # y-axis sorted values
                    "values": f"""(Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_offset,
                        helper_sheet.plot_row,
                    )}:{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_offset,
                        helper_sheet.plot_row + 2*helper_sheet.instance_n,
                    )})""",
                }
            )
            cactus_chart.set_params(
                x_axis={"name": "# of Instances"}, y_axis={"name": f"={self.name}!{self.measure_select}"}
            )
            cdf_chart.add_series(
                {
                    "name": f"""Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset,
                        helper_sheet.plot_row - 2,
                    )}""",
                    # x-axis sorted values
                    "categories": f"""(Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_offset,
                        helper_sheet.plot_row,
                    )}:{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_offset,
                        helper_sheet.plot_row + 2*helper_sheet.instance_n,
                    )})""",
                    # y-axis index
                    "values": f"""(Helper!{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_index_offset,
                        helper_sheet.plot_row,
                    )}:{get_cell_index(
                        helper_sheet.start_cols['plot'] + setting_offset + sorted_index_offset,
                        helper_sheet.plot_row + 2*helper_sheet.instance_n,
                    )})""",
                }
            )
            cdf_chart.set_params(
                x_axis={"name": f"={self.name}!{self.measure_select}"}, y_axis={"name": "# of Instances"}
            )

        self.content.loc[4, 1] = survivor_chart
        self.content.loc[4, 10] = cactus_chart
        self.content.loc[4, 19] = cdf_chart

        self.content = self.content.reindex(
            index=list(range(self.content.index.max() + 1)), columns=list(range(self.content.columns.max() + 1))
        )
        self.content = self.content.astype(object).where(self.content.notna(), None)

    def write_sheet(self, xlsxdoc: "XLSXDoc") -> None:
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
                    elif isinstance(val, Chart) and len(val.series) > 0:
                        val.write(xlsxdoc, sheet, row, col)
        else:
            raise ValueError("Trying to write to uninitialized workbook.")
