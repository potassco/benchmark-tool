"""
Test cases for ChartSheet.
"""

from unittest.mock import MagicMock, call

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
class TestChartSheet(TestSheet):
    """
    Test cases for ChartSheet.
    """

    def setUp(self):
        self.bm = MagicMock(spec=result.BenchmarkMerge)
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.ref_inst_sheet = InstanceSheet("Instances", self.bm, self.measures)
        self.ref_run_sheet = MergedRunSheet("Merged Runs", self.bm, self.measures, self.ref_inst_sheet)
        self.sheet = ChartSheet("TestSheet", self.bm, self.measures, self.ref_inst_sheet)
        self.ref_help_sheet = HelperSheet(
            name="Helper",
            benchmark=self.bm,
            measures=self.measures,
            instance_sheet=self.ref_inst_sheet,
            merged_run_sheet=self.ref_run_sheet,
            chart_sheet=self.sheet,
        )

        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.sheet.merge_select, "$B$3")
        self.assertEqual(self.sheet.measure_select, "$F$3")
        self.assertEqual(self.sheet.instance_sheet, self.ref_inst_sheet)
        self.assertIsNone(self.sheet.matrix_range)

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: [np.nan, np.nan],
                    1: [
                        "Select merge criteria:",
                        spreadsheet.DataValidation(
                            {
                                "validate": "list",
                                "source": ["none", "average", "median", "min", "max"],
                                "input_message": "Select how runs should be merged. 'none' means no merging.",
                            },
                            "none",
                            "input",
                        ),
                    ],
                    5: ["Select measure:", "PLACEHOLDER: Measure select"],
                },
                index=[1, 2],
            ),
            check_dtype=False,
        )

    def test_finalize(self):
        """
        Test finalize method.
        """
        with self.assertRaises(ValueError):
            self.sheet.finalize()

        self.ref_inst_sheet.float_occur = {"time": {1, 4}, "timeout": {2, 5}, "models": {3, 6}}
        self.ref_help_sheet.setting_n = 2
        self.ref_help_sheet.instance_n = 4
        self.ref_help_sheet.start_cols = {"plot": 1, "matrix": 12}
        self.ref_help_sheet.plot_row = 2
        self.ref_help_sheet.matrix_row = 4

        self.sheet.finalize(self.ref_help_sheet)

        # measure select
        self.assertEqual(
            self.sheet.content.loc[2, 5],
            spreadsheet.DataValidation(
                {
                    "validate": "list",
                    "source": ["models", "time", "timeout"],
                    "input_message": "Select measure to display.",
                },
                "models",
                "input",
            ),
        )

        self.assertEqual(self.sheet.content.loc[4, 1].title, "Survivor")
        self.assertEqual(self.sheet.content.loc[4, 1].chart_type, "scatter")
        self.assertEqual(self.sheet.content.loc[4, 1].chart_subtype, "straight")
        self.assertEqual(len(self.sheet.content.loc[4, 1].series), 2)

        self.assertEqual(self.sheet.content.loc[4, 10].title, "CDF")
        self.assertEqual(self.sheet.content.loc[4, 10].chart_type, "scatter")
        self.assertEqual(self.sheet.content.loc[4, 10].chart_subtype, "straight")
        self.assertEqual(len(self.sheet.content.loc[4, 10].series), 2)

        self.assertEqual(self.sheet.content.loc[20, 1].title, "Cactus")
        self.assertEqual(self.sheet.content.loc[20, 1].chart_type, "scatter")
        self.assertEqual(self.sheet.content.loc[20, 1].chart_subtype, "straight")
        self.assertEqual(len(self.sheet.content.loc[20, 1].series), 2)
        self.assertEqual(self.sheet.content.at[4, 19], "Win-Difference-Matrix")
        self.assertIsNone(self.sheet.content.at[3, 19])
        self.assertEqual(self.sheet.matrix_range, (5, 20, 6, 21))
        for row in range(3):
            for col in range(3):
                if row == 0 and col == 0:
                    continue
                self.assertIsInstance(self.sheet.content.at[4 + row, 19 + col], spreadsheet.Formula)
                self.assertEqual(
                    self.sheet.content.at[4 + row, 19 + col],
                    spreadsheet.Formula(f"='Helper'!{spreadsheet.get_cell_index(11 + col, 3 + row)}"),
                )

    def test_finalize_without_numeric_measures(self) -> None:
        """Keep a matrix title but no heatmap range when there are no settings to plot."""
        self.ref_help_sheet.start_cols["matrix"] = 12
        self.ref_help_sheet.matrix_row = 4
        self.sheet.finalize(self.ref_help_sheet)
        self.assertIsNone(self.sheet.matrix_range)
        self.assertEqual(self.sheet.content.at[4, 19], "Win-Difference-Matrix")

    def test_write_sheet(self) -> None:
        """
        Test write_sheet method.
        """
        doc = xlsx_gen.XLSXDoc(MagicMock(spec=result.BenchmarkMerge), {})
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        chart = spreadsheet.Chart("Test Chart", "scatter", "straight")
        chart.add_series(
            {
                "name": "Test Series",
                "categories": "A1:A10",
                "values": "B1:B10",
            }
        )
        self.sheet.content = pd.DataFrame(
            {
                0: [1, "test", 3.0, True],
                1: pd.Series([None, spreadsheet.Formula("=F3"), chart, spreadsheet.DataValidation()], dtype=object),
                2: pd.Series([object(), spreadsheet.Chart("Empty", "scatter"), None, None], dtype=object),
            }
        )
        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        self.sheet.write_sheet(doc)
        mock_worksheet.write.assert_has_calls(
            [call(0, 0, 1, None), call(1, 0, "test", None), call(1, 1, "=F3", None)],
            any_order=True,
        )
        mock_worksheet.conditional_format.assert_not_called()
        mock_worksheet.set_column_pixels.assert_not_called()
        mock_worksheet.insert_chart.assert_called_once()
        self.assertFalse(any(args.args[:2] in ((0, 2), (1, 2)) for args in mock_worksheet.write.call_args_list))

        # # invalid workbook
        doc.workbook = None
        with self.assertRaises(ValueError):
            self.sheet.write_sheet(doc)

    def test_write_sheet_with_matrix(self) -> None:
        """
        Test writing of the win-diff- matrix and formatting.
        """
        doc = xlsx_gen.XLSXDoc(MagicMock(spec=result.BenchmarkMerge), {})
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        matrix_format = MagicMock()
        matrix_header_format = MagicMock()
        doc.workbook.add_format.side_effect = [matrix_format, matrix_header_format]

        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        self.sheet.content = pd.DataFrame(None, index=range(7), columns=range(22), dtype=object)
        self.sheet.content.at[4, 19] = "Header"
        self.sheet.content.at[6, 21] = 0.5
        self.sheet.matrix_range = (5, 20, 6, 21)
        self.ref_inst_sheet.system_blocks = {
            0: spreadsheet.SystemBlock(None, None),
            1: spreadsheet.SystemBlock(None, None),
        }
        self.ref_inst_sheet.machines = set()

        self.sheet.write_sheet(doc)

        mock_worksheet.write.assert_any_call(4, 19, "Header", matrix_header_format)
        mock_worksheet.write.assert_any_call(6, 21, 0.5, matrix_format)
        mock_worksheet.set_row_pixels.assert_called_once_with(4, 80)
        mock_worksheet.set_column_pixels.assert_has_calls([call(20, 20, 80), call(21, 21, 80), call(19, 19, 80)])
        mock_worksheet.conditional_format.assert_called_once_with(
            5,
            20,
            6,
            21,
            {
                "type": "3_color_scale",
                "min_type": "min",
                "min_color": "#F8696B",
                "mid_type": "num",
                "mid_value": 0,
                "mid_color": "#FFFFFF",
                "max_type": "max",
                "max_color": "#2F8FDF",
            },
        )
