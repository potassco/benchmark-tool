"""
Test cases for HelperSheet.
"""

from unittest.mock import MagicMock, call, patch

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
        self.assertEqual(self.sheet.name, "TestSheet")
        self.assertEqual(self.sheet.benchmark, self.bm)
        self.assertDictEqual(self.sheet.measures, self.measures)
        self.assertEqual(self.sheet.setting_n, 0)
        self.assertEqual(self.sheet.instance_n, 0)
        self.assertDictEqual(self.sheet.float_occur, {})
        self.assertDictEqual(self.sheet.start_cols, {})
        self.assertDictEqual(self.sheet.clean_rows, {})
        self.assertEqual(self.sheet.plot_row, 0)
        self.assertEqual(self.sheet.matrix_row, 0)
        self.assertDictEqual(self.sheet._cell_buffer, {})

    def test_setup_table_structure(self):
        """
        Test _setup_table_structure method.
        """
        self.ref_inst_sheet.result_offset = 4

        table_rows, inst_n = self.sheet._setup_table_structure(self.ref_inst_sheet.name, self.ref_inst_sheet, 0, 0)

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {(1, 0): "data", (2, 0): "index", (3, 0): 1, (4, 0): 2, (6, 0): "step", (13, 0): "sort", (19, 0): "clean"},
        )
        self.assertDictEqual(table_rows, {"data": 3, "step": 7, "sort": 14, "clean": 20})
        self.assertEqual(inst_n, 2)

        self.setUp()  # reset sheet
        self.sheet.instance_n = 3

        table_rows, inst_n = self.sheet._setup_table_structure("plot", self.ref_inst_sheet, 0, 0)

        self.assertDictEqual(self.sheet._cell_buffer, {(2, 0): "plot"})
        self.assertDictEqual(table_rows, {"plot": 3})
        self.assertEqual(inst_n, 3)

        self.setUp()  # reset sheet
        self.sheet.instance_n = 3

        table_rows, inst_n = self.sheet._setup_table_structure("solvable", self.ref_inst_sheet, 0, 0)

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {(1, 0): "solvable", (2, 0): "index", (3, 0): 1, (4, 0): 2, (5, 0): 3},
        )
        self.assertDictEqual(table_rows, {"solvable": 3})
        self.assertEqual(inst_n, 3)

        self.setUp()  # reset sheet
        self.sheet.instance_n = 3

        table_rows, inst_n = self.sheet._setup_table_structure("matrix", self.ref_inst_sheet, 0, 0)

        self.assertDictEqual(self.sheet._cell_buffer, {(1, 0): "matrix", (2, 0): "i\\j"})
        self.assertDictEqual(table_rows, {"matrix": 3})
        self.assertEqual(inst_n, 3)

    def test_class_lookup_and_filters(self):
        """
        Use the same reporting labels for choices, raw rows, and merged rows.
        """
        benchmark = result.Benchmark("bench")
        for index, name in enumerate(('planning/small/a"b', "planning/small/c")):
            benchclass = result.Class(benchmark, name, index)
            benchmark.classes[index] = benchclass
            instance = result.Instance(benchclass, "case01", 0)
            instance.values["max_runs"] = index + 1
            benchclass.instances[0] = instance
        for depth, labels in (
            (None, ['bench/planning/small/a"b', "bench/planning/small/c"]),
            (2, ["bench/planning/small"] * 2),
        ):
            with self.subTest(depth=depth):
                helper = HelperSheet(
                    name="Helper",
                    benchmark=result.BenchmarkMerge({benchmark}, class_group_depth=depth),
                    measures=self.measures,
                    instance_sheet=self.ref_inst_sheet,
                    merged_run_sheet=self.ref_run_sheet,
                    chart_sheet=self.ref_chart_sheet,
                )
                self.assertEqual(helper._instance_classes, [labels[0], labels[1], labels[1]])
                self.assertEqual(helper._merged_classes, labels)
                helper._add_class_lookup(4)
                choices = list(dict.fromkeys(labels))
                self.assertEqual(helper.class_range, f"$A$5:$A${5 + len(choices)}")
                self.assertEqual(
                    helper._cell_buffer,
                    {(row, 0): label for row, label in enumerate(["All classes"] + choices, 4)},
                )
                for merged, row in ((False, 2), (True, 1), (False, 0)):
                    label = labels[1 if row else 0].replace('"', '""')
                    self.assertEqual(
                        helper._filter_class("A1", row, merged=merged),
                        f'IF(OR(Charts!$J$3="All classes",Charts!$J$3="{label}"),A1,"")',
                    )

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

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {
                (0, 1): spreadsheet.Formula("=VLOOKUP(Charts!m_select,A1:B2,2,FALSE)"),
                (1, 1): spreadsheet.Formula("=Instances!B1"),
                (0, 2): spreadsheet.Formula("=B1+1"),
                (1, 2): spreadsheet.Formula("=Instances!C1"),
                (0, 3): spreadsheet.Formula("=B1"),
                (1, 3): spreadsheet.Formula("=B2"),
            },
        )

    def test_add_table_headers(self):
        """
        Test _add_table_headers method.
        """
        table_rows = {"data": 3, "step": 7, "plot": 14}
        self.sheet._add_table_headers(table_rows=table_rows, sheet=self.ref_inst_sheet.name, col=0)

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {
                (2, 0): "values",
                (2, 1): "sorted",
                (2, 3): "aggregated",
                (6, 0): "index",
                (6, 1): "sorted",
                (6, 2): "index",
                (6, 3): "aggregated",
            },
        )

    def test_add_data_table(self):
        """
        Test _add_data_table method.
        """
        self.sheet.start_cols = {self.sheet.instance_sheet.name: 1, self.sheet.merged_run_sheet.name: 3, "plot": 5}
        self.sheet.merged_run_sheet.run_refs = {3: {"inst_start": 2, "inst_end": 3}}
        self.sheet._instance_classes = ["bench/a"] * 2
        self.sheet._merged_classes = ["bench/a"] * 3

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

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {
                (2, 0): spreadsheet.Formula(
                    '=IF(OR(Charts!$J$3="All classes",Charts!$J$3="bench/a"),'
                    'IF(INDIRECT(ADDRESS($A3+2,A$1+1,,,"Instances"))="","",'
                    'INDIRECT(ADDRESS($A3+2,A$1+1,,,"Instances"))),"")'
                ),
                (2, 1): spreadsheet.Formula('=IFERROR(SMALL(A2:A3,ROW()-ROW($B$2)+1),"")'),
                (2, 3): spreadsheet.Formula('=IFERROR(SUM(B2:B3),"")'),
                (3, 0): spreadsheet.Formula(
                    '=IF(OR(Charts!$J$3="All classes",Charts!$J$3="bench/a"),'
                    'SWITCH(Charts!$B$3,"average", AVERAGE(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                    '& ":" & ADDRESS(3+3,A$1+1))),"median", MEDIAN(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                    '& ":" & ADDRESS(3+3,A$1+1))),"min", MIN(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                    '& ":" & ADDRESS(3+3,A$1+1))),"max", MAX(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                    '& ":" & ADDRESS(3+3,A$1+1))),"diff", MAX(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                    '& ":" & ADDRESS(3+3,A$1+1)))-MIN(INDIRECT(ADDRESS(2+3,A$1+1,,,"Instances") '
                    '& ":" & ADDRESS(3+3,A$1+1)))),"")'
                ),
                (3, 1): spreadsheet.Formula('=IFERROR(SMALL(A2:A3,ROW()-ROW($B$2)+1),"")'),
                (3, 3): spreadsheet.Formula('=IFERROR(SUM(B2:B4),"")'),
            },
        )

    def test_add_step_table(self):
        """
        Test _add_step_table method.
        """
        self.sheet._add_step_table(col=0, row=0, value_rows=2, value_data_row=0, step_data_row=3)
        self.sheet._add_step_table(col=0, row=1, value_rows=2, value_data_row=0, step_data_row=3)

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {
                (3, 1): spreadsheet.Formula("=B1"),
                (3, 3): spreadsheet.Formula("=D1"),
                (3, 0): 1,
                (3, 2): 1,
                (7, 0): 1,
                (7, 1): 0,
                (7, 2): 1,
                (7, 3): 0,
                (6, 0): 0,
                (6, 1): 0,
                (6, 2): 0,
                (6, 3): 0,
                (5, 1): spreadsheet.Formula('=IF(B2="","",B1)'),
                (5, 3): spreadsheet.Formula("=D1"),
                (4, 1): spreadsheet.Formula("=B2"),
                (4, 3): spreadsheet.Formula("=D2"),
                (4, 0): 2,
                (4, 2): 2,
                (5, 0): 2,
                (5, 2): 2,
            },
        )

    def test_add_sorted_table(self):
        """
        Test _add_sorted_table method.
        """
        self.sheet._add_sorted_table(
            col=0, col_offset=1, row=0, row_offset=1, value_rows=2, step_data_row=2, sorted_data_row=5
        )

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {(6, 1): spreadsheet.Formula('=IFERROR(SMALL(B3:B7,ROW()-ROW($B$6)+1),"")')},
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

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {
                (8, 0): spreadsheet.Formula("=IF(ISNA(B9),NA(),A6)"),
                (8, 1): spreadsheet.Formula('=IF(B6="",NA(),B6)'),
                (9, 1): spreadsheet.Formula('=IF(OR(B7="",AND(B7=B6,B7=B8)),NA(), B7)'),
                (11, 1): spreadsheet.Formula('=IF(B9="",NA(),B9)'),
            },
        )

    def test_add_plot_table(self):
        """
        Test _add_plot_table method.
        """
        self.sheet.plot_row = 3
        self.sheet.chart_sheet.merge_select = "m_select"
        self.sheet.clean_rows = {self.ref_inst_sheet.name: 8, self.ref_run_sheet.name: 5}
        self.sheet._add_plot_table(col=0, col_offset=1, row=0, row_offset=1, instances_col=0, merged_col=1)

        self.assertDictEqual(
            self.sheet._cell_buffer,
            {(4, 1): spreadsheet.Formula('=IF(Charts!m_select="none",B10,IF(C7="",NA(),C7))')},
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
            patch.object(HelperSheet, "_add_solvable_table", return_value=40) as mock_solvable,
            patch.object(HelperSheet, "_add_matrix_table") as mock_matrix,
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
            mock_solvable.assert_called_once_with(33, 1)
            mock_matrix.assert_called_once_with(40, 1)

        self.assertDictEqual(self.sheet.float_occur, {"time": [1, 3], "timeout": [2, 4]})
        self.assertEqual(self.sheet.setting_n, 2)
        self.assertDictEqual(
            self.sheet._cell_buffer,
            {(1, 0): "time", (1, 1): 1.0, (2, 0): "timeout", (2, 1): 2.0, (4, 0): "All classes"},
        )
        self.assertIsInstance(self.sheet.content, pd.DataFrame)
        self.assertEqual(self.sheet.content.at[1, 0], self.sheet._cell_buffer[(1, 0)])
        self.assertEqual(self.sheet.content.at[2, 1], self.sheet._cell_buffer[(2, 1)])

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
            patch.object(HelperSheet, "_add_solvable_table", return_value=40) as mock_solvable,
            patch.object(HelperSheet, "_add_matrix_table") as mock_matrix,
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
            mock_solvable.assert_called_once_with(21, 1)
            mock_matrix.assert_called_once_with(40, 1)

        self.assertDictEqual(self.sheet.float_occur, {"time": [1], "timeout": [2]})
        self.assertEqual(self.sheet.setting_n, 1)
        self.assertDictEqual(
            self.sheet._cell_buffer,
            {(1, 0): "time", (1, 1): 1.0, (2, 0): "timeout", (2, 1): 2.0, (4, 0): "All classes"},
        )
        self.assertIsInstance(self.sheet.content, pd.DataFrame)

        # Class choices remain available without numeric measures.
        self.setUp()
        with (
            patch.object(HelperSheet, "_setup_table_structure", return_value=(ref_tables, ref_inst_n)),
            patch.object(HelperSheet, "_add_solvable_table", return_value=40),
            patch.object(HelperSheet, "_add_matrix_table"),
        ):
            self.sheet.finalize()

        self.assertDictEqual(self.sheet._cell_buffer, {(2, 0): "All classes"})
        self.assertEqual(self.sheet.class_range, "$A$3:$A$3")
        self.assertIsInstance(self.sheet.content, pd.DataFrame)

    def test_finalize_empty_buffer(self):
        """
        Test the defensive empty-buffer branch.
        """
        with (
            patch.object(HelperSheet, "_add_class_lookup"),
            patch.object(HelperSheet, "_setup_table_structure", return_value=({}, 0)),
            patch.object(HelperSheet, "_add_solvable_table", return_value=0),
            patch.object(HelperSheet, "_add_matrix_table"),
        ):
            self.sheet.finalize()
        self.assertDictEqual(self.sheet._cell_buffer, {})
        self.assertIsInstance(self.sheet.content, pd.DataFrame)
        self.assertTrue(self.sheet.content.empty)

    def test_add_solvable_table(self) -> None:
        """
        Test _add_solvable_table method.
        """
        benchmark = self.res.merge(self.res.projects.values())
        instances = InstanceSheet("Instances", benchmark, {"time": "t"})
        specs = self.res.projects["test_proj0"].runspecs
        specs[0].classresults[0].instresults[0].runs[0].measures["timeout"] = ("int", "1")
        for spec in reversed(specs):
            instances.add_runspec(spec)
        self.sheet.instance_sheet = instances
        self.sheet.instance_n = 6
        self.sheet._instance_classes = ["bench/a"] * 6
        self.sheet.start_cols["Instances"] = 4

        next_col = self.sheet._add_solvable_table(20, 1)

        self.assertEqual(next_col, 24)
        self.assertEqual(self.sheet.start_cols["solvable"], 21)
        for setting, block in enumerate(sorted(instances.system_blocks.values())):
            for row in (1, 2):
                self.assertEqual(
                    self.sheet._cell_buffer[(row, 21 + setting)],
                    spreadsheet.Formula(f"={spreadsheet.get_cell_index(4 + setting * 4, row)}"),
                )
            expected = instances.solvable[(block.setting, block.machine)]
            for row in range(6):
                value = expected[row]
                filtered = (
                    spreadsheet.Formula(f'=IF(OR(Charts!$J$3="All classes",Charts!$J$3="bench/a"),{value},"")')
                    if value is not None
                    else None
                )
                self.assertEqual(self.sheet._cell_buffer[(4 + row, 21 + setting)], filtered)
            self.assertIsNone(self.sheet._cell_buffer[(5, 21)])

    def test_add_matrix_table(self) -> None:
        """
        Test _add_matrix_table method.
        """
        for setting_count in (0, 1, 3):
            with self.subTest(settings=setting_count):
                self.setUp()
                self.sheet.setting_n = setting_count
                self.sheet.instance_n = 2
                self.sheet.start_cols = {"Instances": 4, "solvable": 20}

                self.sheet._add_matrix_table(25, 1)

                self.assertEqual(self.sheet.matrix_row, 4)
                self.assertEqual(self.sheet.start_cols["matrix"], 26)
                for setting in range(setting_count):
                    header = spreadsheet.Formula(f"={spreadsheet.get_cell_index(4 + setting * 4, 2)}")
                    self.assertEqual(self.sheet._cell_buffer[(4 + setting, 25)], header)
                    self.assertEqual(self.sheet._cell_buffer[(3, 26 + setting)], header)
                for setting_i in range(setting_count):
                    for setting_j in range(setting_count):
                        cell = self.sheet._cell_buffer[(4 + setting_i, 26 + setting_j)]
                        if setting_i == setting_j:
                            self.assertIsInstance(cell, int)
                            self.assertEqual(cell, 0)
                            continue
                        value_i, value_j = [
                            f"{spreadsheet.get_cell_index(4 + setting * 4, 4, True, True)}:"
                            f"{spreadsheet.get_cell_index(4 + setting * 4, 5, True, True)}"
                            for setting in (setting_i, setting_j)
                        ]
                        solvable_i, solvable_j = [
                            f"{spreadsheet.get_cell_index(20 + setting, 4, True, True)}:"
                            f"{spreadsheet.get_cell_index(20 + setting, 5, True, True)}"
                            for setting in (setting_i, setting_j)
                        ]
                        numeric = f"--ISNUMBER({value_i}),--ISNUMBER({value_j})"
                        smaller_ij = (
                            f"SUMPRODUCT({numeric},--({value_i}<{value_j}))"
                            f'+SUMPRODUCT(--ISNUMBER({value_i}),--({value_j}=""))'
                        )
                        smaller_ji = (
                            f"SUMPRODUCT({numeric},--({value_j}<{value_i}))"
                            f'+SUMPRODUCT(--ISNUMBER({value_j}),--({value_i}=""))'
                        )
                        denominator = (
                            f"(COUNTIF({solvable_i},1)+COUNTIF({solvable_j},1)"
                            f"-COUNTIFS({solvable_i},1,{solvable_j},1))"
                        )
                        self.assertEqual(
                            cell,
                            spreadsheet.Formula(f"IF({denominator}=0,0,(({smaller_ij})-({smaller_ji}))/{denominator})"),
                        )

    def test_write_sheet(self) -> None:
        """
        Test write_sheet method.
        """
        doc = xlsx_gen.XLSXDoc(MagicMock(spec=result.BenchmarkMerge), {})
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)

        self.sheet._cell_buffer = {
            (0, 0): 1,
            (1, 0): 2.0,
            (2, 0): True,
            (0, 1): spreadsheet.Formula("=IF(ISNA(B9),NA(),A6)"),
            (1, 1): "test",
            (2, 1): None,
        }

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
