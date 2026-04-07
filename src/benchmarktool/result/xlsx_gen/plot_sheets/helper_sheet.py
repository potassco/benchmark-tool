"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any

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
        # support mixed columns -> object dtype
        if col not in self.content.columns:
            self.content[col] = None

        table_rows: dict[str, int] = {}
        if sheet == "plot":
            instance_n = self.instance_n
            plot_row = setting_ref_row + 3
            self.content.loc[plot_row - 1, col] = "plot"
            self.plot_row = plot_row

            table_rows["plot"] = plot_row
        else:
            instance_n = sheet_ref.result_offset - 2
            if sheet == self.instance_sheet.name:
                self.instance_n = instance_n
            # get values + sorted + aggregated
            data_row = setting_ref_row + 3
            self.content.loc[data_row - 2, col] = "data"
            # index
            self.content.loc[data_row - 1, col] = "index"
            for row in range(instance_n):
                self.content.loc[data_row + row, col] = row + 1
            # add step
            step_row = data_row + instance_n + 2
            self.content.loc[step_row - 1, col] = "step"
            # sort data
            sort_row = step_row + 2 * instance_n + 3
            self.content.loc[sort_row - 1, col] = "sort"
            # clean data
            clean_row = sort_row + 2 * instance_n + 2
            self.content.loc[clean_row - 1, col] = "clean"
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
                self.content.loc[setting_ref_row, col] = Formula(
                    "VLOOKUP("
                    f"Charts!{self.chart_sheet.measure_select},{get_cell_index(0, setting_ref_row)}"
                    f":{get_cell_index(1, last_lookup_row - 1)},2,FALSE"
                    ")"
                )
            # other settings
            # get column from first setting + offset
            else:
                self.content.loc[setting_ref_row, col] = Formula(
                    f"={get_cell_index(self.start_cols[sheet_ref.name], setting_ref_row)}"
                    f"+{setting_idx * setting_offset}"
                )
            # get setting name
            self.content.loc[setting_ref_row + 1, col] = Formula(
                f"={sheet_ref.name}!{get_cell_index(1 + setting_idx * setting_offset, 0)}"
            )
        elif isinstance(sheet_ref, MergedRunSheet):
            self.content.loc[setting_ref_row, col] = Formula(
                f"={get_cell_index(self.start_cols[self.instance_sheet.name] + setting_idx * 4, setting_ref_row)}"
            )
            self.content.loc[setting_ref_row + 1, col] = Formula(
                f"={get_cell_index(self.start_cols[self.instance_sheet.name] + setting_idx * 4, setting_ref_row + 1)}"
            )

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
                self.content.loc[row - 1, col] = "values"
            elif table == "plot" and sheet != "plot":
                continue
            else:
                self.content.loc[row - 1, col] = "index"
                self.content.loc[row - 1, col + 2] = "index"
            self.content.loc[row - 1, col + 1] = "sorted"
            self.content.loc[row - 1, col + 3] = "aggregated"

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
        # values
        # if sheet == self.instance_sheet.name:
        if isinstance(sheet_ref, InstanceSheet):
            ref = (
                "INDIRECT("
                f"ADDRESS({get_cell_index(self.start_cols[sheet_ref.name] - 1, value_data_row + row, True, False)}+2,"
                f'{get_cell_index(col, setting_ref_row, False, True)}+1,,,"{sheet_ref.name}")'
                ")"
            )
            # get values from instance sheet, empty if no value
            self.content.loc[value_data_row + row, col] = Formula(f'=IF({ref}="","",{ref})')
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
            self.content.loc[value_data_row + row, col] = Formula(
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
        self.content.loc[value_data_row + row, col + 1] = Formula(
            "IFERROR("
            f"SMALL({get_cell_index(col, value_data_row)}"
            f":{get_cell_index(col, value_data_row + value_rows - 1)},"
            f'ROW()-ROW({get_cell_index(col + 1, value_data_row, True, True)})+1),""'
            ")"
        )
        # aggregated
        # aggregate values from sorted column, empty if no value
        self.content.loc[value_data_row + row, col + 3] = Formula(
            "IFERROR("
            f"SUM({get_cell_index(col + 1, value_data_row,)}"
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
        self.content.loc[step_data_row + row, col + 1] = Formula(f"={get_cell_index(col + 1, value_data_row + row)}")
        # aggregated
        self.content.loc[step_data_row + row, col + 3] = Formula(f"={get_cell_index(col + 3, value_data_row + row)}")

        # add step index
        for col_offset in (0, 2):
            self.content.loc[step_data_row + row, col + col_offset] = row + 1
            if row != 0:
                self.content.loc[step_data_row + row + value_rows - 1, col + col_offset] = row + 1
            # add 0 step
            else:
                self.content.loc[step_data_row + 2 * value_rows, col + col_offset] = 1
                self.content.loc[step_data_row + 2 * value_rows, col + col_offset + 1] = 0
                self.content.loc[step_data_row + 2 * value_rows - 1, col + col_offset] = 0
                self.content.loc[step_data_row + 2 * value_rows - 1, col + col_offset + 1] = 0

        # add step values
        if row != value_rows - 1:
            # sorted
            self.content.loc[step_data_row + row + value_rows, col + 1] = Formula(
                f'=IF({get_cell_index(col + 1, value_data_row + row + 1)}="","",'
                f"{get_cell_index(col + 1, value_data_row + row)})"
            )
            # aggregated
            self.content.loc[step_data_row + row + value_rows, col + 3] = Formula(
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
        self.content.loc[sorted_data_row + row + row_offset, c] = Formula(
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
            self.content.loc[clean_row_ref, c] = Formula(
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
                self.content.loc[clean_row_ref, c] = Formula(
                    "IF(" f'{get_cell_index(c, sorted_row_ref)}="",' f"NA()," f"{get_cell_index(c, sorted_row_ref)}" ")"
                )
            else:
                # if adjacent values in sorted table are the same or value is empty, return NA,
                # else copy value
                self.content.loc[clean_row_ref, c] = Formula(
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
        self.content.loc[self.plot_row + plot_row_offset, c] = Formula(
            f'=IF(Charts!{self.chart_sheet.merge_select}="none",'
            f"""{get_cell_index(
                instances_col + col_offset,
                self.clean_rows[self.instance_sheet.name] + plot_row_offset,
            )},"""
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

    def finalize(self) -> None:
        """
        Finalize sheet.
        """
        for measure, cols in self.instance_sheet.float_occur.items():
            s_cols = sorted(cols)
            self.float_occur[measure] = s_cols
            if self.setting_n == 0:
                self.setting_n = len(s_cols)
            if len(s_cols) > 1:
                setting_offset = s_cols[1] - s_cols[0]
            else:
                setting_offset = 0
        self.content[0] = None

        # lookup table, col 0,1
        lookup_row = 1
        for measure, ref in self.float_occur.items():
            self.content.loc[lookup_row, 0] = measure
            self.content.loc[lookup_row, 1] = min(ref)
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
                # defragmentation (temporary workaround)
                self.content = self.content.copy()
                col += 4
            col += 1

        self.content = self.content.reindex(
            index=list(range(self.content.index.max() + 1)), columns=list(range(self.content.columns.max() + 1))
        )
        # replace all undefined cells with None (empty cell)
        self.content = self.content.astype(object).where(self.content.notna(), None)

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
        for col in range(len(self.content.columns)):
            for row, cell in enumerate(list(self.content.iloc[:, col])):
                val = cell
                if isinstance(val, Formula):
                    val = str(val)
                if isinstance(val, (int, float, str, bool)) or val is None:
                    sheet.write(row, col, val)
