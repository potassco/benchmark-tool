"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any, Optional

from xlsxwriter.utility import cell_autofit_width  # type: ignore[import-untyped]

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
        self.matrix_range: Optional[tuple[int, int, int, int]] = None

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
        self.content.loc[4, 10] = cdf_chart
        self.content.loc[20, 1] = cactus_chart

        self.content.loc[4, 19] = "Win-Difference-Matrix"
        matrix_col = helper_sheet.start_cols["matrix"] - 1
        matrix_row = helper_sheet.matrix_row - 1
        for col_offset in range(helper_sheet.setting_n + 1):
            target_col = 19 + col_offset
            if target_col not in self.content.columns:
                self.content[target_col] = None
            self.content[target_col] = self.content[target_col].astype(object)
            for row_offset in range(helper_sheet.setting_n + 1):
                if row_offset == 0 and col_offset == 0:
                    continue
                source = get_cell_index(matrix_col + col_offset, matrix_row + row_offset)
                self.content.loc[4 + row_offset, target_col] = Formula(f"='{helper_sheet.name}'!{source}")

        if helper_sheet.setting_n > 0:
            self.matrix_range = (5, 20, 4 + helper_sheet.setting_n, 19 + helper_sheet.setting_n)

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
        workbook = xlsxdoc.workbook
        if workbook is None:
            raise ValueError("Trying to write to uninitialized workbook.")
        sheet = workbook.add_worksheet(self.name)
        matrix_format = workbook.add_format({"border": 1, "border_color": "#D4D4D4"})
        matrix_header_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#FFFFFF",
                "font_color": "#000000",
                "border": 1,
                "border_color": "#000000",
                "text_wrap": True,
                "valign": "vcenter",
            }
        )
        for col in range(len(self.content.columns)):
            for row, cell in enumerate(self.content.iloc[:, col]):
                if isinstance(cell, DataValidation):
                    cell.write(xlsxdoc, sheet, row, col)
                    continue
                if isinstance(cell, Chart):
                    if cell.series:
                        cell.write(xlsxdoc, sheet, row, col)
                    continue
                val = str(cell) if isinstance(cell, Formula) else cell
                if not isinstance(val, (int, float, str, bool)) and val is not None:
                    continue
                cell_format = None
                if self.matrix_range is not None:
                    first_row, first_col, last_row, last_col = self.matrix_range
                    if first_row - 1 <= row <= last_row and first_col - 1 <= col <= last_col:
                        is_header = row == first_row - 1 or col == first_col - 1
                        cell_format = matrix_header_format if is_header else matrix_format
                sheet.write(row, col, val, cell_format)

        if self.matrix_range is not None:
            first_row, first_col, last_row, last_col = self.matrix_range
            sheet.set_row_pixels(first_row - 1, 80)
            label_width = xlsxdoc.header_width
            for col, block in zip(range(first_col, last_col + 1), sorted(self.instance_sheet.system_blocks.values())):
                name = block.gen_name(len(self.instance_sheet.machines) > 1)
                col_width = min(xlsxdoc.max_col_width, max(xlsxdoc.header_width, cell_autofit_width(name)))
                sheet.set_column_pixels(col, col, min(100, col_width))
                label_width = max(label_width, col_width)
            sheet.set_column_pixels(first_col - 1, first_col - 1, min(xlsxdoc.max_col_width, label_width))
            sheet.conditional_format(
                *self.matrix_range,
                {
                    "type": "3_color_scale",
                    "min_type": "num",
                    "min_value": -1,
                    "min_color": "#F8696B",
                    "mid_type": "num",
                    "mid_value": 0,
                    "mid_color": "#FFFFFF",
                    "max_type": "num",
                    "max_value": 1,
                    "max_color": "#2F8FDF",
                },
            )
            sheet.merge_range(
                last_row + 2,
                first_col - 1,
                last_row + 8,
                max(last_col, first_col + 4),
                "Each value is (row wins - column wins) / instances solved by either setting/solver.\n"
                "Smaller values of the selected measure win. Solving alone also counts as a win.\n"
                "Blue (positive) favors the row. Red (negative) favors the column.\n"
                "Stronger colors mean a larger advantage.\n"
                "Values range from -1 to 1 e.g., +0.5 means 50 more row wins than column wins per 100 "
                "included instances.",
                workbook.add_format({"text_wrap": True, "valign": "top", "font_size": 10}),
            )
