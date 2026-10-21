"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any

import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result.xlsx_gen.plot_sheets.chart_sheet import ChartSheet
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.result_sheets.merged_sheet import MergedRunSheet
from benchmarktool.result.xlsx_gen.result_sheets.result_sheet import ResultSheet
from benchmarktool.result.xlsx_gen.spreadsheet import Formula, Sheet, get_cell_index

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage
    from benchmarktool.result.xlsx_gen.xlsx_gen import XLSXDoc  # nocoverage


# pylint: disable=too-many-instance-attributes
class HelperSheet(Sheet):
    """
    A helper sheet to prepare data for charts.
    """

    def __init__(
        self,
        *,
        name: str,
        benchmark: "result.BenchmarkMerge",
        measures: dict[str, Any],
        instance_sheet: InstanceSheet,
        merged_run_sheet: MergedRunSheet,
        chart_sheet: "ChartSheet",
    ):
        super().__init__(name, benchmark, measures)

        self.instance_sheet = instance_sheet
        self.merged_run_sheet = merged_run_sheet
        self.chart_sheet = chart_sheet

        self.setting_n = 0
        self.instance_n = 0

        self.float_occur: dict[str, list[int]] = {}
        self.start_cols: dict[str, int] = {}
        self.clean_rows: dict[str, int] = {}
        self.plot_row = 0
        self.matrix_row = 0
        self._cell_buffer: dict[tuple[int, int], Any] = {}

    def _setup_table_structure(
        self, sheet: str, sheet_ref: ResultSheet, col: int, setting_ref_row: int
    ) -> tuple[dict[str, int], int]:
        """
        Setup the structure of the sheet.

        Attributes:
            sheet (str): Reference sheet name.
            sheet_ref (ResultSheet): Reference sheet object.
            col (int): Column index.
            setting_ref_row (int): Row index for setting reference.
        """
        table_rows: dict[str, int] = {}
        if sheet == "plot":
            instance_n = self.instance_n
            plot_row = setting_ref_row + 3
            self._cell_buffer[(plot_row - 1, col)] = "plot"
            self.plot_row = plot_row

            table_rows["plot"] = plot_row
        elif sheet == "solvable":
            instance_n = self.instance_n
            solvable_row = setting_ref_row + 3
            self._cell_buffer[(solvable_row - 2, col)] = "solvable"
            self._cell_buffer[(solvable_row - 1, col)] = "index"
            for row in range(instance_n):
                self._cell_buffer[(solvable_row + row, col)] = row + 1

            table_rows["solvable"] = solvable_row
        elif sheet == "matrix":
            instance_n = self.instance_n
            matrix_row = setting_ref_row + 3
            self._cell_buffer[(matrix_row - 2, col)] = "matrix"
            self._cell_buffer[(matrix_row - 1, col)] = "i\\j"

            table_rows["matrix"] = matrix_row
        else:
            instance_n = sheet_ref.result_offset - 2
            if sheet == self.instance_sheet.name:
                self.instance_n = instance_n
            # get values + sorted + aggregated
            data_row = setting_ref_row + 3
            self._cell_buffer[(data_row - 2, col)] = "data"
            # index
            self._cell_buffer[(data_row - 1, col)] = "index"
            for row in range(instance_n):
                self._cell_buffer[(data_row + row, col)] = row + 1
            # add step
            step_row = data_row + instance_n + 2
            self._cell_buffer[(step_row - 1, col)] = "step"
            # sort data
            sort_row = step_row + 2 * instance_n + 3
            self._cell_buffer[(sort_row - 1, col)] = "sort"
            # clean data
            clean_row = sort_row + 2 * instance_n + 2
            self._cell_buffer[(clean_row - 1, col)] = "clean"
            self.clean_rows[sheet] = clean_row

            table_rows = {
                "data": data_row,
                "step": step_row,
                "sort": sort_row,
                "clean": clean_row,
            }
        return table_rows, instance_n

    def _add_setting_headers(
        self,
        *,
        sheet_ref: ResultSheet,
        col: int,
        setting_idx: int,
        setting_ref_row: int,
        setting_offset: int,
        last_lookup_row: int,
    ) -> None:
        """
        Add setting headers to the sheet.

        Attributes:
            sheet_ref (ResultSheet): Reference sheet object.
            col (int): Column index for first column of row.
            setting_idx (int): Index of the setting.
            setting_ref_row (int): Row index for setting reference.
            setting_offset (int): Column offset for settings.
            last_lookup_row (int): Last row index of the setting lookup table.
        """
        if isinstance(sheet_ref, InstanceSheet):
            # first setting
            # get initial column from lookup table
            if setting_idx == 0:
                self._cell_buffer[(setting_ref_row, col)] = Formula(
                    "VLOOKUP("
                    f"Charts!{self.chart_sheet.measure_select},{get_cell_index(0, setting_ref_row)}"
                    f":{get_cell_index(1, last_lookup_row - 1)},2,FALSE"
                    ")"
                )
            # other settings
            # get column from first setting + offset
            else:
                self._cell_buffer[(setting_ref_row, col)] = Formula(
                    f"={get_cell_index(self.start_cols[sheet_ref.name], setting_ref_row)}"
                    f"+{setting_idx * setting_offset}"
                )
            # get setting name
            self._cell_buffer[(setting_ref_row + 1, col)] = Formula(
                f"={sheet_ref.name}!{get_cell_index(1 + setting_idx * setting_offset, 0)}"
            )
        elif isinstance(sheet_ref, MergedRunSheet):
            source_col = self.start_cols[self.instance_sheet.name] + setting_idx * 4
            for header_row in (setting_ref_row, setting_ref_row + 1):
                self._cell_buffer[(header_row, col)] = Formula(f"={get_cell_index(source_col, header_row)}")

    def _add_table_headers(self, sheet: str, table_rows: dict[str, int], col: int) -> None:
        """
        Add headers to given rows.

        Attributes:
            sheet (str): Reference sheet name.
            table_rows (dict[str, int]): Dictionary of row indices for each table type.
            col (int): Column index for first column of row.
        """
        for table, row in table_rows.items():
            if table == "data":
                self._cell_buffer[(row - 1, col)] = "values"
            elif table == "plot" and sheet != "plot":
                continue
            else:
                self._cell_buffer[(row - 1, col)] = "index"
                self._cell_buffer[(row - 1, col + 2)] = "index"
            self._cell_buffer[(row - 1, col + 1)] = "sorted"
            self._cell_buffer[(row - 1, col + 3)] = "aggregated"

    def _add_data_table(
        self,
        *,
        sheet_ref: ResultSheet,
        col: int,
        row: int,
        setting_ref_row: int,
        value_rows: int,
        value_data_row: int,
    ) -> None:
        """
        Add data table.

        Attributes:
            sheet_ref (ResultSheet): Reference sheet for data.
            col (int): Column index for first column of row.
            row (int): Row index for current row.
            setting_ref_row (int): Row index for setting reference.
            value_rows (int): Number of rows for values.
            value_data_row (int): Row index for first row of values.
        """
        if isinstance(sheet_ref, InstanceSheet):
            ref = (
                "INDIRECT("
                f"ADDRESS({get_cell_index(self.start_cols[sheet_ref.name] - 1, value_data_row + row, True, False)}+2,"
                f'{get_cell_index(col, setting_ref_row, False, True)}+1,,,"{sheet_ref.name}")'
                ")"
            )
            # get values from instance sheet, empty if no value
            self._cell_buffer[(value_data_row + row, col)] = Formula(f'=IF({ref}="","",{ref})')
        elif isinstance(sheet_ref, MergedRunSheet):
            ref = (
                "INDIRECT("
                f'ADDRESS({sheet_ref.run_refs[row+1]["inst_start"]}+3,'
                f"{get_cell_index(col, setting_ref_row, False, True)}+1,,,"
                f'"{self.instance_sheet.name}") & ":" & '
                f'ADDRESS({sheet_ref.run_refs[row+1]["inst_end"]}+3,'
                f"{get_cell_index(col, setting_ref_row, False, True)}+1)"
                ")"
            )
            # merge values from instance sheet based on merge_select from ChartSheet
            self._cell_buffer[(value_data_row + row, col)] = Formula(
                "SWITCH("
                f"Charts!{self.chart_sheet.merge_select},"
                f'"average", AVERAGE({ref}),'
                f'"median", MEDIAN({ref}),'
                f'"min", MIN({ref}),'
                f'"max", MAX({ref}),'
                f'"diff", MAX({ref})-MIN({ref})'
                ")"
            )
        # sorted
        # sort values from values column, empty if no value
        self._cell_buffer[(value_data_row + row, col + 1)] = Formula(
            "IFERROR("
            f"SMALL({get_cell_index(col, value_data_row)}"
            f":{get_cell_index(col, value_data_row + value_rows - 1)},"
            f'ROW()-ROW({get_cell_index(col + 1, value_data_row, True, True)})+1),""'
            ")"
        )
        # aggregated
        # aggregate values from sorted column, empty if no value
        self._cell_buffer[(value_data_row + row, col + 3)] = Formula(
            "IFERROR("
            f"SUM({get_cell_index(col + 1, value_data_row)}"
            f':{get_cell_index(col + 1, value_data_row + row)}),""'
            ")"
        )

    def _add_step_table(self, *, col: int, row: int, value_rows: int, value_data_row: int, step_data_row: int) -> None:
        """
        Add step table.

        Attributes:
            col (int): Column index for first column of row.
            row (int): Row index for current row.
            value_rows (int): Number of rows for values.
            value_data_row (int): Row index for first row of values.
            step_data_row (int): Row index for first row of step data.
        """
        # copy values from value table
        # sorted
        self._cell_buffer[(step_data_row + row, col + 1)] = Formula(f"={get_cell_index(col + 1, value_data_row + row)}")
        # aggregated
        self._cell_buffer[(step_data_row + row, col + 3)] = Formula(f"={get_cell_index(col + 3, value_data_row + row)}")

        # add step index
        for col_offset in (0, 2):
            self._cell_buffer[(step_data_row + row, col + col_offset)] = row + 1
            if row != 0:
                self._cell_buffer[(step_data_row + row + value_rows - 1, col + col_offset)] = row + 1
            # add 0 step
            else:
                self._cell_buffer[(step_data_row + 2 * value_rows, col + col_offset)] = 1
                self._cell_buffer[(step_data_row + 2 * value_rows, col + col_offset + 1)] = 0
                self._cell_buffer[(step_data_row + 2 * value_rows - 1, col + col_offset)] = 0
                self._cell_buffer[(step_data_row + 2 * value_rows - 1, col + col_offset + 1)] = 0

        # add step values
        if row != value_rows - 1:
            # sorted
            self._cell_buffer[(step_data_row + row + value_rows, col + 1)] = Formula(
                f'=IF({get_cell_index(col + 1, value_data_row + row + 1)}="","",'
                f"{get_cell_index(col + 1, value_data_row + row)})"
            )
            # aggregated
            self._cell_buffer[(step_data_row + row + value_rows, col + 3)] = Formula(
                f"={get_cell_index(col + 3, value_data_row + row)}"
            )

    def _add_sorted_table(
        self,
        *,
        col: int,
        col_offset: int,
        row: int,
        row_offset: int,
        value_rows: int,
        step_data_row: int,
        sorted_data_row: int,
    ) -> None:
        """
        Add sorted table.

        Attributes:
            col (int): Column index for current column.
            col_offset (int): Column offset.
            row (int): Row index for current row.
            row_offset (int): Row offset.
            value_rows (int): Number of rows for values.
            step_data_row (int): Row index for first row of step data.
            sorted_data_row (int): Row index for first row of sorted data.
        """
        c = col + col_offset
        # sorted
        # sort values/indices from step table, empty if no value
        # index-value pairs stay coherent since step table columns are sorted
        self._cell_buffer[(sorted_data_row + row + row_offset, c)] = Formula(
            "IFERROR("
            "SMALL("
            f"{get_cell_index(c, step_data_row)}:"
            f"{get_cell_index(c, step_data_row + 2 * value_rows)},"
            f"ROW()-ROW({get_cell_index(c, sorted_data_row, True, True)})+1"
            '),""'
            ")"
        )

    def _add_clean_table(
        self,
        *,
        col: int,
        col_offset: int,
        row: int,
        row_offset: int,
        value_rows: int,
        sorted_data_row: int,
        clean_data_row: int,
    ) -> None:
        """
        Add clean table.

        Attributes:
            col (int): Column index for current column.
            col_offset (int): Column offset.
            row (int): Row index for current row.
            row_offset (int): Row offset.
            value_rows (int): Number of rows for values.
            sorted_data_row (int): Row index for first row of sorted data.
            clean_data_row (int): Row index for first row of clean data.
        """
        c = col + col_offset
        sorted_row_ref = sorted_data_row + row + row_offset
        clean_row_ref = clean_data_row + row + row_offset
        # clean
        # index
        if col_offset in (0, 2):
            # if corresponding value is NA, return NA,
            # else return index from sorted table
            self._cell_buffer[(clean_row_ref, c)] = Formula(
                "IF("
                f"ISNA({get_cell_index(c + 1, clean_row_ref)}),"
                f"NA(),"
                f"{get_cell_index(c, sorted_row_ref)}"
                ")"
            )
        # sorted and aggregated values
        elif col_offset in (1, 3):
            # edges (first and last row)
            if (row == 0 and row_offset == 0) or (row == value_rows - 1 and row_offset != 0):
                # if value in sorted table is empty return NA, else copy value
                self._cell_buffer[(clean_row_ref, c)] = Formula(
                    "IF(" f'{get_cell_index(c, sorted_row_ref)}="",' f"NA()," f"{get_cell_index(c, sorted_row_ref)}" ")"
                )
            else:
                # if adjacent values in sorted table are the same or value is empty, return NA,
                # else copy value
                self._cell_buffer[(clean_row_ref, c)] = Formula(
                    "IF("
                    "OR("
                    f'{get_cell_index(c, sorted_row_ref)}="",'
                    "AND("
                    f"{get_cell_index(c, sorted_row_ref)}"
                    f"={get_cell_index(c, sorted_row_ref - 1)},"
                    f"{get_cell_index(c, sorted_row_ref)}"
                    f"={get_cell_index(c, sorted_row_ref + 1)}"
                    ")),"
                    f"NA(), {get_cell_index(c, sorted_row_ref)}"
                    ")"
                )

    def _add_plot_table(
        self, *, col: int, col_offset: int, row: int, row_offset: int, instances_col: int, merged_col: int
    ) -> None:
        """
        Add plot table.

        Attributes:
            col (int): Column index for current column.
            col_offset (int): Column offset.
            row (int): Row index for current row.
            row_offset (int): Row offset.
            instances_col (int): Column index for instances.
            merged_col (int): Column index for merged data.
        """
        c = col + col_offset
        plot_row_offset = row + row_offset
        clean_merged_ref = get_cell_index(
            merged_col + col_offset,
            self.clean_rows[self.merged_run_sheet.name] + plot_row_offset,
        )
        clean_instance_ref = get_cell_index(
            instances_col + col_offset,
            self.clean_rows[self.instance_sheet.name] + plot_row_offset,
        )
        self._cell_buffer[(self.plot_row + plot_row_offset, c)] = Formula(
            f'=IF(Charts!{self.chart_sheet.merge_select}="none",'
            f"{clean_instance_ref},"
            f'IF({clean_merged_ref}="",NA(),{clean_merged_ref}))'
        )

    def _add_stepped_tables(
        self,
        *,
        sheet: str,
        col: int,
        row: int,
        setting_idx: int,
        value_rows: int,
        table_rows: dict[str, int],
    ) -> None:
        """
        Add stepped tables sort, clean and plot.

        Attributes:
            sheet (str): Name of the sheet.
            col (int): Column index for current column.
            row (int): Row index for current row.
            setting_idx (int): Index of the setting.
            value_rows (int): Number of value rows.
            table_rows (dict[str, int]): Dictionary of row indices for each table type.
        """
        for pair_idx in range(8):
            # data
            col_offset, row_mult = divmod(pair_idx, 2)
            if sheet != "plot":
                # sort
                self._add_sorted_table(
                    col=col,
                    col_offset=col_offset,
                    row=row,
                    row_offset=row_mult * value_rows,
                    value_rows=value_rows,
                    step_data_row=table_rows["step"],
                    sorted_data_row=table_rows["sort"],
                )
                # clean
                self._add_clean_table(
                    col=col,
                    col_offset=col_offset,
                    row=row,
                    row_offset=row_mult * value_rows,
                    value_rows=value_rows,
                    sorted_data_row=table_rows["sort"],
                    clean_data_row=table_rows["clean"],
                )
            else:
                # plot
                self._add_plot_table(
                    col=col,
                    col_offset=col_offset,
                    row=row,
                    row_offset=row_mult * value_rows,
                    instances_col=self.start_cols[self.instance_sheet.name] + setting_idx * 4,
                    merged_col=self.start_cols[self.merged_run_sheet.name] + setting_idx * 4,
                )

    def _add_solvable_table(self, col: int, setting_ref_row: int) -> int:
        """
        Add solvability table, returning the next table's starting column.

        Attributes:
            col (int): Starting column.
            setting_ref_row (int): Reference row for the settings headers.
        """
        table_rows, instance_n = self._setup_table_structure("solvable", self.instance_sheet, col, setting_ref_row)
        col += 1
        self.start_cols["solvable"] = col
        for setting, block in enumerate(sorted(self.instance_sheet.system_blocks.values())):
            source_col = self.start_cols[self.instance_sheet.name] + setting * 4
            for header_row in (setting_ref_row, setting_ref_row + 1):
                self._cell_buffer[(header_row, col)] = Formula(f"={get_cell_index(source_col, header_row)}")
            values = self.instance_sheet.solvable[(block.setting, block.machine)]
            for row in range(instance_n):
                self._cell_buffer[(table_rows["solvable"] + row, col)] = values.get(row)
            col += 1
        return col + 1

    def _add_matrix_table(self, col: int, setting_ref_row: int) -> None:
        """
        Add setting-pair comparison formulas and headers using values and solvability.

        Attributes:
            col (int): Starting column.
            setting_ref_row (int): Reference row for the settings headers.
        """
        table_rows, instance_n = self._setup_table_structure("matrix", self.instance_sheet, col, setting_ref_row)
        matrix_row = table_rows["matrix"]
        self.matrix_row = matrix_row
        self.start_cols["matrix"] = col + 1
        data_row = setting_ref_row + 3
        last_data_row = data_row + instance_n - 1
        value_ranges: list[str] = []
        solvable_ranges: list[str] = []
        for setting in range(self.setting_n):
            matrix_col = col + 1 + setting
            source_col = self.start_cols[self.instance_sheet.name] + setting * 4
            header = Formula(f"={get_cell_index(source_col, setting_ref_row + 1)}")
            self._cell_buffer[(matrix_row + setting, col)] = header
            self._cell_buffer[(matrix_row - 1, matrix_col)] = header
            value_ranges.append(
                f"{get_cell_index(source_col, data_row, True, True)}:"
                f"{get_cell_index(source_col, last_data_row, True, True)}"
            )
            solvable_col = self.start_cols["solvable"] + setting
            solvable_ranges.append(
                f"{get_cell_index(solvable_col, data_row, True, True)}:"
                f"{get_cell_index(solvable_col, last_data_row, True, True)}"
            )

        for setting_i, value_i in enumerate(value_ranges):
            for setting_j, value_j in enumerate(value_ranges):
                matrix_col = col + 1 + setting_j
                if setting_i == setting_j:
                    self._cell_buffer[(matrix_row + setting_i, matrix_col)] = 0
                    continue
                numeric = f"--ISNUMBER({value_i}),--ISNUMBER({value_j})"
                # A numeric value also wins when the other setting has no value.
                smaller_ij = (
                    f"SUMPRODUCT({numeric},--({value_i}<{value_j}))"
                    f'+SUMPRODUCT(--ISNUMBER({value_i}),--({value_j}=""))'
                )
                smaller_ji = (
                    f"SUMPRODUCT({numeric},--({value_j}<{value_i}))"
                    f'+SUMPRODUCT(--ISNUMBER({value_j}),--({value_i}=""))'
                )
                solvable_ij = f"COUNTIFS({solvable_ranges[setting_i]},1,{solvable_ranges[setting_j]},1)"
                self._cell_buffer[(matrix_row + setting_i, matrix_col)] = Formula(
                    f"IF({solvable_ij}=0,0,(({smaller_ij})-({smaller_ji}))/{solvable_ij})"
                )

    def finalize(self) -> None:
        """
        Finalize sheet.
        """
        setting_offset = 0
        for measure, cols in self.instance_sheet.float_occur.items():
            s_cols = sorted(cols)
            self.float_occur[measure] = s_cols
            if self.setting_n == 0:
                self.setting_n = len(s_cols)
            if len(s_cols) > 1:
                setting_offset = s_cols[1] - s_cols[0]
            else:
                setting_offset = 0
        self._cell_buffer.clear()

        # lookup table, col 0,1
        lookup_row = 1
        for measure, ref in self.float_occur.items():
            self._cell_buffer[(lookup_row, 0)] = measure
            self._cell_buffer[(lookup_row, 1)] = min(ref)
            lookup_row += 1

        start_col = 3
        setting_ref_row = 1
        col = start_col
        for sheet, sheet_ref in (
            (self.instance_sheet.name, self.instance_sheet),
            (self.merged_run_sheet.name, self.merged_run_sheet),
            ("plot", self.instance_sheet),
        ):
            # labels for tables
            table_rows, instance_n = self._setup_table_structure(sheet, sheet_ref, col, setting_ref_row)

            col += 1
            self.start_cols[sheet] = col
            for setting in range(self.setting_n):
                # setting refs
                self._add_setting_headers(
                    sheet_ref=sheet_ref,
                    col=col,
                    setting_idx=setting,
                    setting_ref_row=setting_ref_row,
                    setting_offset=setting_offset,
                    last_lookup_row=lookup_row,
                )
                # headers
                self._add_table_headers(sheet, table_rows, col)
                for row in range(instance_n):
                    if sheet != "plot":
                        # data
                        self._add_data_table(
                            sheet_ref=sheet_ref,
                            col=col,
                            row=row,
                            setting_ref_row=setting_ref_row,
                            value_rows=instance_n,
                            value_data_row=table_rows["data"],
                        )
                        # step
                        self._add_step_table(
                            col=col,
                            row=row,
                            value_rows=instance_n,
                            value_data_row=table_rows["data"],
                            step_data_row=table_rows["step"],
                        )
                    self._add_stepped_tables(
                        sheet=sheet, col=col, row=row, setting_idx=setting, value_rows=instance_n, table_rows=table_rows
                    )
                col += 4
            col += 1

        col = self._add_solvable_table(col, setting_ref_row)
        self._add_matrix_table(col, setting_ref_row)

        if self._cell_buffer:
            row_count = max(row for row, _ in self._cell_buffer) + 1
            col_count = max(col for _, col in self._cell_buffer) + 1
            content = [[None] * col_count for _ in range(row_count)]
            for (row, col), value in self._cell_buffer.items():
                content[row][col] = value
            self.content = pd.DataFrame(content, dtype=object)
        else:
            self.content = pd.DataFrame(dtype=object)
        self.content = self.content.where(self.content.notna(), None)

    def write_sheet(self, xlsxdoc: "XLSXDoc") -> None:
        """
        Write sheet to XLSX document.

        Attributes:
            xlsxdoc (XLSXDoc): XLSX document.
        """
        if xlsxdoc.workbook is None:
            raise ValueError("Trying to write to uninitialized workbook.")
        sheet = xlsxdoc.workbook.add_worksheet(self.name)
        # hide sheet, can be unhidden via UI
        sheet.hide()
        # write from sparse cell buffer
        for (row, col), cell in self._cell_buffer.items():
            val = cell
            if isinstance(val, Formula):
                val = str(val)
            if isinstance(val, (int, float, str, bool)) or val is None:
                sheet.write(row, col, val)
