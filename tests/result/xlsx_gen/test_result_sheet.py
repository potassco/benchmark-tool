"""
Test cases for ResultSheet.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import xlsxwriter  # type: ignore[import-untyped]

from benchmarktool.result import result
from benchmarktool.result.xlsx_gen import spreadsheet, xlsx_gen
from benchmarktool.result.xlsx_gen.result_sheets.result_sheet import ResultSheet
from benchmarktool.result.xlsx_gen.spreadsheet import SystemBlock
from tests.result.xlsx_gen.test_xlsx_gen import TestSheet


# pylint: disable=protected-access
class TestResultSheet(TestSheet):
    """
    Test cases for ResultSheet.
    """

    def setUp(self):
        self.bm = MagicMock(spec=result.BenchmarkMerge)
        self.measures = {"time": "t"}
        self.ref_result_offset = 0
        with self.assertRaises(NotImplementedError):
            ResultSheet("TestSheet", self.bm, self.measures)
        with patch.object(ResultSheet, "prepare") as mock_prepare:
            self.sheet = ResultSheet("TestSheet", self.bm, self.measures)
            mock_prepare.assert_called_once()

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        super().test_init()
        self.assertDictEqual(self.sheet.system_blocks, {})
        self.assertDictEqual(self.sheet.types, {})
        self.assertSetEqual(self.sheet.machines, set())
        self.assertDictEqual(self.sheet.summary_refs, {})
        self.assertIsInstance(self.sheet.values, pd.DataFrame)
        self.assertDictEqual(self.sheet.float_occur, {})
        self.assertEqual(self.sheet.result_offset, self.ref_result_offset)
        self.assertEqual(self.sheet.col_offset, 0)
        self.assertDictEqual(self.sheet.formats, {})

    def test_add_runspec(self) -> None:
        """
        Test add_runspec method.
        """
        with self.assertRaises(NotImplementedError):
            self.sheet.add_runspec(MagicMock(spec=result.Runspec))

    def test_finalize(self) -> None:
        """
        Test finalize method.
        """
        block = SystemBlock(None, None)
        block.add_cell(0, "time", "float", 1.0)
        block.add_cell(1, "time", "float", 4.0)
        block.add_cell(0, "timeout", "int", 0)
        self.sheet.content = pd.DataFrame({0: [1, 2, 3, 4]})
        self.sheet.system_blocks[("setting", "machine")] = block

        with (
            patch.object(self.sheet, "_finalize_results") as mock_finalize_results,
            patch.object(self.sheet, "_obtain_values") as mock_obtain_values,
            patch.object(self.sheet, "add_row_summary") as mock_add_row_summary,
            patch.object(self.sheet, "add_col_summary") as mock_add_col_summary,
            patch.object(self.sheet, "add_styles") as mock_add_styles,
            patch.object(block, "gen_name") as mock_gen_name,
        ):
            mock_gen_name.return_value = "s1"
            self.sheet.finalize()
            mock_finalize_results.assert_called_once()
            mock_obtain_values.assert_called_once()
            mock_add_row_summary.assert_called_once()
            mock_add_col_summary.assert_called_once()
            mock_add_styles.assert_called_once()

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {0: [1, 2, 3, 4], 1: ["s1", "time", 1.0, 4.0], 2: pd.Series([None, "timeout", 0, None], dtype=object)},
                dtype=object,
            ),
        )

    def test_finalize_results(self) -> None:
        """
        Test _finalize_results method.
        """
        with self.assertRaises(NotImplementedError):
            self.sheet._finalize_results()

    def test_obtain_values(self) -> None:
        """
        Test _obtain_values method.
        """
        with self.assertRaises(NotImplementedError):
            self.sheet._obtain_values()

    def test_add_row_summary(self) -> None:
        """
        Test add_row_summary method.
        """
        self.test_finalize()
        self.sheet.result_offset = 4
        self.sheet.float_occur = {"time": {1}, "timeout": {2}}

        with patch.object(self.sheet, "_add_summary_formula") as mock_add_summary_formula:
            mock_add_summary_formula.side_effect = lambda block, operator, measure, float_occur, col: block.add_cell(
                0, measure, "formula", f"test_formula_{operator}"
            )
            self.sheet.add_row_summary()

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: [1, 2, 3, 4],
                    1: ["s1", "time", 1.0, 4.0],
                    2: [None, "timeout", 0, None],
                    3: ["min", "time", "test_formula_min", np.nan],
                    4: [np.nan, "timeout", "test_formula_min", np.nan],
                    5: ["median", "time", "test_formula_median", np.nan],
                    6: [np.nan, "timeout", "test_formula_median", np.nan],
                    7: ["max", "time", "test_formula_max", np.nan],
                    8: [np.nan, "timeout", "test_formula_max", np.nan],
                }
            ),
            check_dtype=False,
        )
        pd.testing.assert_frame_equal(
            self.sheet.values,
            pd.DataFrame(
                {
                    3: ["min", "time"],
                    4: [np.nan, "timeout"],
                    5: ["median", "time"],
                    6: [np.nan, "timeout"],
                    7: ["max", "time"],
                    8: [np.nan, "timeout"],
                }
            ),
            check_dtype=False,
        )
        self.assertDictEqual(
            self.sheet.summary_refs,
            {
                "min": {"col": 3, "time": (3, "$D$3:$D$4"), "timeout": (4, "$E$3:$E$4")},
                "median": {"col": 5, "time": (5, "$F$3:$F$4"), "timeout": (6, "$G$3:$G$4")},
                "max": {"col": 7, "time": (7, "$H$3:$H$4"), "timeout": (8, "$I$3:$I$4")},
            },
        )

    def test_add_summary_formula(self) -> None:
        """
        Test _add_summary_formula method.
        """
        block = SystemBlock(None, None)
        block.offset = 3
        self.sheet.values = pd.DataFrame(
            {
                0: [1, 2, 3, 4],
                1: ["s1", "time", 1.0, np.nan],
                2: ["s2", "time", 0, np.nan],
                3: ["min", "time", np.nan, np.nan],
            }
        )
        self.sheet.result_offset = 4
        self.sheet.float_occur = {"time": {1, 2}}

        self.sheet._add_summary_formula(block, "min", "time", self.sheet.float_occur, 3)

        self.assertEqual(str(block.content.loc[2, "time"]), "=MIN($B3,$C3)")
        pd.testing.assert_frame_equal(
            self.sheet.values,
            pd.DataFrame(
                {
                    0: [1, 2, 3, 4],
                    1: ["s1", "time", 1.0, np.nan],
                    2: ["s2", "time", 0, np.nan],
                    3: ["min", "time", 0.0, np.nan],
                }
            ),
            check_dtype=False,
        )

    def test_add_col_summary(self) -> None:
        """
        Test add_col_summary method.
        """
        with self.assertRaises(NotImplementedError):
            self.sheet.add_col_summary()

    def test_add_default_col_summary_formulas(self) -> None:
        """
        Test _add_default_col_summary_formulas method.
        """
        self.test_finalize()
        self.sheet.summary_refs = {"min": {"col": 3}}
        self.sheet.result_offset = 4
        summaries = [(0, "A1:A4", "C1:C4", "E1:E4", "G1:G4")]

        self.sheet._add_default_col_summary_formulas(1, summaries)

        ref = [
            "=SUM(A1:A4)",
            "=AVERAGE(A1:A4)",
            "=STDEV(A1:A4)",
            "=SUMPRODUCT(--(A1:A4-C1:C4)^2)^0.5",
            "=SUMPRODUCT(NOT(ISBLANK(A1:A4))*(A1:A4=C1:C4))",
            "=SUMPRODUCT(NOT(ISBLANK(A1:A4))*(A1:A4<E1:E4))",
            "=SUMPRODUCT((NOT(ISBLANK(A1:A4))*(A1:A4>E1:E4))+ISBLANK(A1:A4))",
            "=SUMPRODUCT((NOT(ISBLANK(A1:A4))*(A1:A4=G1:G4))+ISBLANK(A1:A4))",
        ]
        for i, value in enumerate(ref):
            self.assertEqual(str(self.sheet.content.at[self.sheet.result_offset + 1 + i, 1]), value)

    def test_add_default_col_summary_values(self) -> None:
        """
        Test _add_default_col_summary_values method.
        """
        self.sheet.values = pd.DataFrame(
            {
                0: [1, 2, 3, 4],
                1: ["s1", "time", 1, 2],
                2: ["s2", "time", 0, np.nan],
                3: ["min", "time", 0.0, 2.0],
                4: ["median", "time", 0.5, 2.0],
                5: ["max", "time", 1.0, 2.0],
            }
        )
        self.sheet.summary_refs = {
            "min": {"col": 3, "time": (3, "-")},
            "median": {"col": 4, "time": (4, "-")},
            "max": {"col": 5, "time": (5, "-")},
        }
        self.sheet.result_offset = 4

        self.sheet._add_default_col_summary_values(1, "time", [1, 2])

        values = [3, 1.5, 0.7071067811865476, 1.0, -1, 0, 1, 2]
        for i, value in enumerate(values):
            self.assertEqual(self.sheet.values.at[self.sheet.result_offset + 1 + i, 1], value)

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        self.sheet.measures = {"time": "t", "timeout": "to", "status": None}
        self.sheet.float_occur = {"time": {1, 3}, "timeout": {2, 4}, "status": {5}}
        self.sheet.values = pd.DataFrame(
            {
                0: [1, 2, 3, 4],
                1: ["s1", "time", 1.0, 1],
                2: [np.nan, "timeout", 0, 1],
                3: ["s2", "time", 0, 5],
                4: [np.nan, "timeout", 0, 0],
                5: ["s3", "status", 1, 2],
            }
        )
        self.sheet.content = pd.DataFrame(
            {
                0: [1, 2, 3, 4],
                1: ["s1", "time", 1.0, 1],
                2: [None, "timeout", 0, 1],
                3: ["s2", "time", 0, 5],
                4: [None, "timeout", 0, 0],
                5: ["s3", "status", 1, 2],
            }
        )

        self.sheet.add_styles()

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: [1, 2, 3, 4],
                    1: ["s1", "time", 1.0, (1.0, "best")],
                    2: [None, "timeout", 0, (1, "worst")],
                    3: ["s2", "time", 0.0, 5.0],
                    4: [None, "timeout", 0, (0, "best")],
                    5: ["s3", "status", 1, 2],
                }
            ),
            check_dtype=False,
        )
        self.assertDictEqual(self.sheet.formats, {2: "to", 4: "to"})

    def test_write_sheet(self) -> None:
        """
        Test write_sheet method.
        """
        doc = xlsx_gen.XLSXDoc(MagicMock(spec=result.BenchmarkMerge), {})
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        self.sheet.content = pd.DataFrame(
            {
                0: [1, 2, 3, 4],
                1: ["s1", "time", (1.0, "best"), spreadsheet.DataValidation()],
                2: [None, "timeout", spreadsheet.Formula("=F3"), None],
            }
        )
        self.sheet.measures = {"time": "t", "timeout": "to"}
        self.sheet.formats = {2: "to"}
        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        self.sheet.write_sheet(doc)

        # # no measures (should never occur in practice)
        self.sheet.measures = {}
        self.sheet.write_sheet(doc)

        # # invalid workbook
        doc.workbook = None
        with self.assertRaises(ValueError):
            self.sheet.write_sheet(doc)
