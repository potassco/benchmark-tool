"""
Test cases for HelperSheet.
"""

from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import xlsxwriter  # type: ignore[import-untyped]

from benchmarktool.result import parser, result
from benchmarktool.result.xlsx_gen import spreadsheet, xlsx_gen
from benchmarktool.result.xlsx_gen.plot_sheets.chart_sheet import ChartSheet
from benchmarktool.result.xlsx_gen.plot_sheets.helper_sheet import HelperSheet
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.result_sheets.merged_sheet import MergedRunSheet
from tests.result.xlsx_gen.test_xlsx_gen import TestSheet


# pylint: disable=protected-access
class TestHelperSheet(TestSheet):
    """
    Test cases for HelperSheet.
    """

    def setUp(self):
        self.bm = MagicMock(spec=result.BenchmarkMerge)
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.ref_inst_sheet = InstanceSheet("Instances", self.bm, self.measures)
        self.ref_run_sheet = MergedRunSheet("Merged Runs", self.bm, self.measures, self.ref_inst_sheet)
        self.ref_chart_sheet = ChartSheet("Chart", self.bm, self.measures, self.ref_inst_sheet)
        self.ref_chart_sheet.measure_select = "m_select"
        self.sheet = HelperSheet(
            name="TestSheet",
            benchmark=self.bm,
            measures=self.measures,
            instance_sheet=self.ref_inst_sheet,
            merged_run_sheet=self.ref_run_sheet,
            chart_sheet=self.ref_chart_sheet,
        )
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.sheet.setting_n, 0)
        self.assertEqual(self.sheet.instance_n, 0)
        self.assertDictEqual(self.sheet.float_occur, {})
        self.assertDictEqual(self.sheet.start_cols, {})
        self.assertDictEqual(self.sheet.clean_rows, {})
        self.assertEqual(self.sheet.plot_row, 0)

    def test_setup_table_structure(self):
        """
        Test _setup_table_structure method.
        """
        self.ref_inst_sheet.result_offset = 4

        table_rows, inst_n = self.sheet._setup_table_structure(self.ref_inst_sheet.name, self.ref_inst_sheet, 0, 0)

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame({0: ["data", "index", 1, 2, "step", "sort", "clean"]}, index=[1, 2, 3, 4, 6, 13, 19]),
            check_dtype=False,
        )
        self.assertDictEqual(table_rows, {"data": 3, "step": 7, "sort": 14, "clean": 20})
        self.assertEqual(inst_n, 2)

        self.setUp()  # reset sheet
        self.sheet.instance_n = 3

        table_rows, inst_n = self.sheet._setup_table_structure("plot", self.ref_inst_sheet, 0, 0)

        pd.testing.assert_frame_equal(self.sheet.content, pd.DataFrame({0: ["plot"]}, index=[2]), check_dtype=False)
        self.assertDictEqual(table_rows, {"plot": 3})
        self.assertEqual(inst_n, 3)

    def test_add_setting_headers(self):
        """
        Test _add_setting_headers method.
        """
        self.sheet.start_cols = {self.sheet.instance_sheet.name: 1, self.sheet.merged_run_sheet.name: 3, "plot": 5}
        self.sheet._add_setting_headers(
            sheet_ref=self.ref_inst_sheet, col=1, setting_idx=0, setting_ref_row=0, setting_offset=1, last_lookup_row=2
        )
        self.sheet._add_setting_headers(
            sheet_ref=self.ref_inst_sheet, col=2, setting_idx=1, setting_ref_row=0, setting_offset=1, last_lookup_row=2
        )
        self.sheet._add_setting_headers(
            sheet_ref=self.ref_run_sheet, col=3, setting_idx=0, setting_ref_row=0, setting_offset=1, last_lookup_row=2
        )

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    1: [
                        spreadsheet.Formula("=VLOOKUP(Charts!m_select,A1:B2,2,FALSE)"),
                        spreadsheet.Formula("=Instances!B1"),
                    ],
                    2: [spreadsheet.Formula("=B1+1"), spreadsheet.Formula("=Instances!C1")],
                    3: [spreadsheet.Formula("=B1"), spreadsheet.Formula("=B2")],
                }
            ),
            check_dtype=False,
        )

    def test_add_table_headers(self):
        """
        Test _add_table_headers method.
        """
        table_rows = {"data": 3, "step": 7, "plot": 14}
        self.sheet._add_table_headers(table_rows=table_rows, sheet=self.ref_inst_sheet.name, col=0)

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: ["values", "index"],
                    1: ["sorted", "sorted"],
                    3: ["aggregated", "aggregated"],
                    2: [np.nan, "index"],
                },
                index=[2, 6],
            ),
            check_dtype=False,
        )

    def test_add_data_table(self):
        """
        Test _add_data_table method.
        """
        self.sheet.start_cols = {self.sheet.instance_sheet.name: 1, self.sheet.merged_run_sheet.name: 3, "plot": 5}
        self.sheet.merged_run_sheet.run_refs = {3: {"inst_start": 2, "inst_end": 3}}

        self.sheet._add_data_table(
            sheet_ref=self.ref_inst_sheet,
            col=0,
            row=1,
            setting_ref_row=0,
            value_rows=2,
            value_data_row=1,
        )
        self.sheet._add_data_table(
            sheet_ref=self.ref_run_sheet,
            col=0,
            row=2,
            setting_ref_row=0,
            value_rows=2,
            value_data_row=1,
        )

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: [
                        spreadsheet.Formula(
                            '=IF(INDIRECT(ADDRESS($A3+2,A$1+1,,,"Instances"))="","",'
                            'INDIRECT(ADDRESS($A3+2,A$1+1,,,"Instances")))'
                        ),
                        spreadsheet.Formula(
                            '=SWITCH(Charts!$B$3,"average", AVERAGE(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                            '& ":" & ADDRESS(3+3,A$1+1))),"median", MEDIAN(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                            '& ":" & ADDRESS(3+3,A$1+1))),"min", MIN(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                            '& ":" & ADDRESS(3+3,A$1+1))),"max", MAX(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                            '& ":" & ADDRESS(3+3,A$1+1))),"diff", MAX(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                            '& ":" & ADDRESS(3+3,A$1+1)))-MIN(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                            '& ":" & ADDRESS(3+3,A$1+1))))'
                        ),
                    ],
                    1: [
                        spreadsheet.Formula('=IFERROR(SMALL(A2:A3,ROW()-ROW($B$2)+1),"")'),
                        spreadsheet.Formula('=IFERROR(SMALL(A2:A3,ROW()-ROW($B$2)+1),"")'),
                    ],
                    3: [spreadsheet.Formula('=IFERROR(SUM(B2:B3),"")'), spreadsheet.Formula('=IFERROR(SUM(B2:B4),"")')],
                },
                index=[2, 3],
            ),
            check_dtype=False,
        )

    def test_add_step_table(self):
        """
        Test _add_step_table method.
        """
        self.sheet._add_step_table(col=0, row=0, value_rows=2, value_data_row=0, step_data_row=3)
        self.sheet._add_step_table(col=0, row=1, value_rows=2, value_data_row=0, step_data_row=3)

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    1: [
                        spreadsheet.Formula("=B1"),
                        0,
                        0,
                        spreadsheet.Formula('=IF(B2="","",B1)'),
                        spreadsheet.Formula("=B2"),
                    ],
                    3: [spreadsheet.Formula("=D1"), 0, 0, spreadsheet.Formula("=D1"), spreadsheet.Formula("=D2")],
                    0: [1.0, 1.0, 0.0, 2.0, 2.0],
                    2: [1.0, 1.0, 0.0, 2.0, 2.0],
                },
                index=[3, 7, 6, 5, 4],
            ),
            check_dtype=False,
        )

    def test_add_sorted_table(self):
        """
        Test _add_sorted_table method.
        """
        self.sheet._add_sorted_table(
            col=0, col_offset=1, row=0, row_offset=1, value_rows=2, step_data_row=2, sorted_data_row=5
        )

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    1: [
                        spreadsheet.Formula('=IFERROR(SMALL(B3:B7,ROW()-ROW($B$6)+1),"")'),
                    ],
                },
                index=[6],
            ),
            check_dtype=False,
        )

    def test_add_clean_table(self):
        """
        Test _add_clean_table method.
        """
        self.sheet._add_clean_table(
            col=0, col_offset=0, row=0, row_offset=0, value_rows=2, sorted_data_row=5, clean_data_row=8
        )
        self.sheet._add_clean_table(
            col=0, col_offset=1, row=0, row_offset=0, value_rows=2, sorted_data_row=5, clean_data_row=8
        )
        self.sheet._add_clean_table(
            col=0, col_offset=1, row=1, row_offset=0, value_rows=2, sorted_data_row=5, clean_data_row=8
        )
        self.sheet._add_clean_table(
            col=0, col_offset=1, row=1, row_offset=2, value_rows=2, sorted_data_row=5, clean_data_row=8
        )

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: [
                        spreadsheet.Formula("=IF(ISNA(B9),NA(),A6)"),
                        np.nan,
                        np.nan,
                    ],
                    1: [
                        spreadsheet.Formula('=IF(B6="",NA(),B6)'),
                        spreadsheet.Formula('=IF(OR(B7="",AND(B7=B6,B7=B8)),NA(), B7)'),
                        spreadsheet.Formula('=IF(B9="",NA(),B9)'),
                    ],
                },
                index=[8, 9, 11],
            ),
            check_dtype=False,
        )

    def test_add_plot_table(self):
        """
        Test _add_plot_table method.
        """
        self.sheet.plot_row = 3
        self.sheet.chart_sheet.merge_select = "m_select"
        self.sheet.clean_rows = {self.ref_inst_sheet.name: 8, self.ref_run_sheet.name: 5}
        self.sheet._add_plot_table(col=0, col_offset=1, row=0, row_offset=1, instances_col=0, merged_col=1)

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    1: [
                        spreadsheet.Formula('=IF(Charts!m_select="none",B10,IF(C7="",NA(),C7))'),
                    ],
                },
                index=[4],
            ),
            check_dtype=False,
        )

    def test_add_stepped_tables(self):
        """
        Test _add_stepped_tables method.
        """
        ref_col = 1
        ref_row = 2
        ref_table_rows = {"step": 7, "sort": 14, "clean": 20}
        ref_value_rows = 2
        ref_setting_idx = 1
        ref_inst_start = 1
        ref_merged_start = 3
        self.sheet.start_cols = {
            self.sheet.instance_sheet.name: ref_inst_start,
            self.sheet.merged_run_sheet.name: ref_merged_start,
        }

        with (
            patch.object(HelperSheet, "_add_sorted_table") as mock_sorted,
            patch.object(HelperSheet, "_add_clean_table") as mock_clean,
            patch.object(HelperSheet, "_add_plot_table") as mock_plot,
        ):
            self.sheet._add_stepped_tables(
                sheet=self.ref_inst_sheet.name,
                col=ref_col,
                row=ref_row,
                setting_idx=ref_setting_idx,
                value_rows=ref_value_rows,
                table_rows=ref_table_rows,
            )
            # selective
            mock_sorted.assert_has_calls(
                [
                    call(
                        col=ref_col,
                        col_offset=0,
                        row=ref_row,
                        row_offset=0,
                        value_rows=ref_value_rows,
                        step_data_row=ref_table_rows["step"],
                        sorted_data_row=ref_table_rows["sort"],
                    ),
                    call(
                        col=ref_col,
                        col_offset=3,
                        row=ref_row,
                        row_offset=2,
                        value_rows=ref_value_rows,
                        step_data_row=ref_table_rows["step"],
                        sorted_data_row=ref_table_rows["sort"],
                    ),
                ],
                any_order=True,
            )
            self.assertEqual(mock_sorted.call_count, 8)
            mock_clean.assert_has_calls(
                [
                    call(
                        col=ref_col,
                        col_offset=0,
                        row=ref_row,
                        row_offset=0,
                        value_rows=ref_value_rows,
                        sorted_data_row=ref_table_rows["sort"],
                        clean_data_row=ref_table_rows["clean"],
                    ),
                    call(
                        col=ref_col,
                        col_offset=3,
                        row=ref_row,
                        row_offset=2,
                        value_rows=ref_value_rows,
                        sorted_data_row=ref_table_rows["sort"],
                        clean_data_row=ref_table_rows["clean"],
                    ),
                ],
                any_order=True,
            )
            self.assertEqual(mock_clean.call_count, 8)
            mock_plot.assert_not_called()

        with (
            patch.object(HelperSheet, "_add_sorted_table") as mock_sorted,
            patch.object(HelperSheet, "_add_clean_table") as mock_clean,
            patch.object(HelperSheet, "_add_plot_table") as mock_plot,
        ):
            self.sheet._add_stepped_tables(
                sheet="plot",
                col=ref_col,
                row=ref_row,
                setting_idx=ref_setting_idx,
                value_rows=ref_value_rows,
                table_rows=ref_table_rows,
            )
            mock_sorted.assert_not_called()
            mock_clean.assert_not_called()
            mock_plot.assert_has_calls(
                [
                    call(
                        col=ref_col,
                        col_offset=0,
                        row=ref_row,
                        row_offset=0,
                        instances_col=ref_inst_start + 4,
                        merged_col=ref_merged_start + 4,
                    ),
                    call(
                        col=ref_col,
                        col_offset=3,
                        row=ref_row,
                        row_offset=2,
                        instances_col=ref_inst_start + 4,
                        merged_col=ref_merged_start + 4,
                    ),
                ],
                any_order=True,
            )
            self.assertEqual(mock_plot.call_count, 8)

    def test_finalize(self):
        "Test finalize method."

        self.sheet.instance_sheet.float_occur = {"time": {1, 3}, "timeout": {2, 4}}
        ref_tables = {"data": 3, "step": 7, "sort": 14, "clean": 20}
        ref_inst_n = 2

        with (
            patch.object(HelperSheet, "_setup_table_structure") as mock_setup,
            patch.object(HelperSheet, "_add_setting_headers") as mock_setting_headers,
            patch.object(HelperSheet, "_add_table_headers") as mock_table_headers,
            patch.object(HelperSheet, "_add_data_table") as mock_data,
            patch.object(HelperSheet, "_add_step_table") as mock_step,
            patch.object(HelperSheet, "_add_stepped_tables") as mock_stepped,
        ):
            mock_setup.return_value = (ref_tables, ref_inst_n)
            self.sheet.finalize()

            # inst, merged, plot
            self.assertEqual(mock_setup.call_count, 3)
            # 2 settings for each of the 3 tables -> 6 sub-tables
            self.assertEqual(mock_setting_headers.call_count, 6)
            self.assertEqual(mock_table_headers.call_count, 6)
            # data table for inst and merged sheet for each setting, for each instance -> 2*2*2 = 8
            self.assertEqual(mock_data.call_count, 8)
            # step table for inst and merged sheet for each setting, for each instance -> 2*2*2 = 8
            self.assertEqual(mock_step.call_count, 8)
            # stepped tables for inst and merged sheet + plot table for each setting, for each instance -> 3*2*2 = 12
            self.assertEqual(mock_stepped.call_count, 12)

        self.assertDictEqual(self.sheet.float_occur, {"time": [1, 3], "timeout": [2, 4]})
        self.assertEqual(self.sheet.setting_n, 2)
        pd.testing.assert_series_equal(
            self.sheet.content[0],
            pd.Series([None, "time", "timeout"], dtype=object, name=0),
            check_dtype=False,
        )
        pd.testing.assert_series_equal(
            self.sheet.content[1],
            pd.Series([None, 1.0, 2.0], dtype=object, name=1),
            check_dtype=False,
        )

        # single setting
        self.setUp()
        self.sheet.instance_sheet.float_occur = {"time": {1}, "timeout": {2}}
        with (
            patch.object(HelperSheet, "_setup_table_structure") as mock_setup,
            patch.object(HelperSheet, "_add_setting_headers") as mock_setting_headers,
            patch.object(HelperSheet, "_add_table_headers") as mock_table_headers,
            patch.object(HelperSheet, "_add_data_table") as mock_data,
            patch.object(HelperSheet, "_add_step_table") as mock_step,
            patch.object(HelperSheet, "_add_stepped_tables") as mock_stepped,
        ):
            mock_setup.return_value = (ref_tables, ref_inst_n)
            self.sheet.finalize()

            # inst, merged, plot
            self.assertEqual(mock_setup.call_count, 3)
            # 1 setting for each of the 3 tables -> 3 sub-tables
            self.assertEqual(mock_setting_headers.call_count, 3)
            self.assertEqual(mock_table_headers.call_count, 3)
            # data table for inst and merged sheet for each setting, for each instance -> 2*1*2 = 4
            self.assertEqual(mock_data.call_count, 4)
            # step table for inst and merged sheet for each setting, for each instance -> 2*1*2 = 4
            self.assertEqual(mock_step.call_count, 4)
            # stepped tables for inst and merged sheet + plot table for each setting, for each instance -> 3*1*2 = 6
            self.assertEqual(mock_stepped.call_count, 6)

        self.assertDictEqual(self.sheet.float_occur, {"time": [1], "timeout": [2]})
        self.assertEqual(self.sheet.setting_n, 1)
        pd.testing.assert_series_equal(
            self.sheet.content[0],
            pd.Series([None, "time", "timeout"], dtype=object, name=0),
            check_dtype=False,
        )
        pd.testing.assert_series_equal(
            self.sheet.content[1],
            pd.Series([None, 1.0, 2.0], dtype=object, name=1),
            check_dtype=False,
        )

    def test_write_sheet(self) -> None:
        """
        Test write_sheet method.
        """
        doc = xlsx_gen.XLSXDoc(MagicMock(spec=result.BenchmarkMerge), {})
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)

        self.sheet.content = pd.DataFrame(
            {
                0: [1, 2.0, True],
                1: pd.Series(
                    [
                        spreadsheet.Formula("=IF(ISNA(B9),NA(),A6)"),
                        "test",
                        None,
                    ],
                    dtype=object,
                ),
            },
            dtype=object,
        )

        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        self.sheet.write_sheet(doc)

        # # no measures (should never occur in practice)
        self.sheet.measures = {}
        self.sheet.write_sheet(doc)
        mock_worksheet.write.assert_has_calls(
            [
                call(0, 0, 1),
                call(1, 0, 2.0),
                call(2, 0, True),
                call(0, 1, "=IF(ISNA(B9),NA(),A6)"),
                call(1, 1, "test"),
                call(2, 1, None),
            ],
            any_order=True,
        )

        # # invalid workbook
        doc.workbook = None
        with self.assertRaises(ValueError):
            self.sheet.write_sheet(doc)
