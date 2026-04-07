"""
Test cases for ChartSheet.
"""

from unittest.mock import MagicMock

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
        self.ref_help_sheet.start_cols = {"plot": 1}
        self.ref_help_sheet.plot_row = 2

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

        self.assertEqual(self.sheet.content.loc[4, 10].title, "Cactus")
        self.assertEqual(self.sheet.content.loc[4, 10].chart_type, "scatter")
        self.assertEqual(self.sheet.content.loc[4, 10].chart_subtype, "straight")
        self.assertEqual(len(self.sheet.content.loc[4, 10].series), 2)

        self.assertEqual(self.sheet.content.loc[4, 19].title, "CDF")
        self.assertEqual(self.sheet.content.loc[4, 19].chart_type, "scatter")
        self.assertEqual(self.sheet.content.loc[4, 19].chart_subtype, "straight")
        self.assertEqual(len(self.sheet.content.loc[4, 19].series), 2)

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
            }
        )
        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        self.sheet.write_sheet(doc)

        # # invalid workbook
        doc.workbook = None
        with self.assertRaises(ValueError):
            self.sheet.write_sheet(doc)
