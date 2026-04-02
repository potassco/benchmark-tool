"""
Test cases for MergedRunSheet.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result import parser, result
from benchmarktool.result.xlsx_gen import spreadsheet
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.result_sheets.merged_sheet import MergedRunSheet
from tests.result.xlsx_gen.test_result_sheet import TestResultSheet


# pylint: disable=protected-access
class TestMergedSheet(TestResultSheet):
    """
    Test cases for Sheet class with merged benchmark runs (mergedSheet).
    """

    def setUp(self) -> None:
        self.bm = MagicMock(spec=result.BenchmarkMerge)
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.ref_result_offset = 2
        self.ref_sheet = InstanceSheet("Instances", self.bm, self.measures)
        self.sheet = MergedRunSheet("TestSheet", self.bm, self.measures, self.ref_sheet)
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        super().test_init()
        select_merge = spreadsheet.DataValidation(
            {
                "validate": "list",
                "source": ["average", "median", "min", "max", "diff"],
                "input_message": "Select merge criteria",
            },
            "median",
            "input",
        )
        self.assertEqual(self.sheet.ref_sheet, self.ref_sheet)
        self.assertDictEqual(self.sheet.run_refs, {})
        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: pd.Series(
                        [
                            "Merge criteria:",
                            select_merge,
                            None,
                            "SUM",
                            "AVG",
                            "DEV",
                            "DST",
                            "BEST",
                            "BETTER",
                            "WORSE",
                            "WORST",
                        ],
                        dtype=object,
                    )
                }
            ),
        )

        bench_merge = self.res.merge(self.res.projects.values())
        ref_sheet = InstanceSheet("Instances", bench_merge, self.measures)
        sheet = MergedRunSheet("TestSheet", bench_merge, self.measures, ref_sheet)
        self.assertEqual(sheet.result_offset, 5)
        pd.testing.assert_frame_equal(
            sheet.content,
            pd.DataFrame(
                {
                    0: pd.Series(
                        [
                            "Merge criteria:",
                            select_merge,
                            "test_class0/test_inst00",
                            "test_class1/test_inst10",
                            "test_class1/test_inst11",
                            None,
                            "SUM",
                            "AVG",
                            "DEV",
                            "DST",
                            "BEST",
                            "BETTER",
                            "WORSE",
                            "WORST",
                        ],
                        dtype=object,
                    )
                }
            ),
        )

    def test_set_col_summary_headers(self) -> None:
        """
        Tested via test_init, as it is called in prepare method.
        """
        return

    def test_add_runspec(self) -> None:
        """
        Test add_runspec, _add_merged_instance_results
        and _add_instance_result_to_instance_summary method.
        """
        run_specs = self.res.projects["test_proj0"].runspecs
        bench_merge = self.res.merge(self.res.projects.values())
        ref_sheet = InstanceSheet("Instances", bench_merge, self.measures)
        ref_sheet.add_runspec(run_specs[0])
        sheet = MergedRunSheet("TestSheet", bench_merge, self.measures, ref_sheet)

        sheet.add_runspec(run_specs[0])

        self.assertIsInstance(
            sheet.system_blocks[(run_specs[0].setting, run_specs[0].machine)], spreadsheet.SystemBlock
        )
        self.assertSetEqual(sheet.machines, set([run_specs[0].machine]))
        pd.testing.assert_frame_equal(
            sheet.system_blocks[(run_specs[0].setting, run_specs[0].machine)].content,
            pd.DataFrame(
                {
                    "time": [
                        "time",
                        {"inst_start": 0, "inst_end": 1, "value": 1},
                        {"inst_start": 2, "inst_end": 3, "value": 1},
                        {"inst_start": 4, "inst_end": 5, "value": 1},
                    ],
                    "timeout": [
                        "timeout",
                        {"inst_start": 0, "inst_end": 1, "value": 1},
                        {"inst_start": 2, "inst_end": 3, "value": 1},
                        {"inst_start": 4, "inst_end": 5, "value": 1},
                    ],
                    "status": ["status", np.nan, np.nan, np.nan],
                    "models": [
                        "models",
                        np.nan,
                        {"inst_start": 2, "inst_end": 3, "value": 1},
                        {"inst_start": 4, "inst_end": 5, "value": 1},
                    ],
                },
                index=[1, 2, 3, 4],
            ),
            check_dtype=False,
        )

    def test_finalize_results(self) -> None:
        """
        Test _finalize_results method.
        """
        self.sheet.result_offset = 4
        self.sheet.content = pd.DataFrame(
            {
                0: [np.nan, "header", 1, 2],
                1: [
                    np.nan,
                    "time",
                    {"inst_start": 0, "inst_end": 1, "value": 1},
                    {"inst_start": 2, "inst_end": 3, "value": 1},
                ],
                2: [np.nan, "col2", np.nan, np.nan],
            }
        )
        self.sheet.types = {"time": "merged_runs", "col2": "None"}

        self.sheet._finalize_results()

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: [np.nan, "header", 1, 2],
                    1: [
                        np.nan,
                        "time",
                        spreadsheet.Formula(
                            '=SWITCH($A$2,"average", AVERAGE(Instances!B3:Instances!B4),'
                            '"median", MEDIAN(Instances!B3:Instances!B4),'
                            '"min", MIN(Instances!B3:Instances!B4),'
                            '"max", MAX(Instances!B3:Instances!B4),'
                            '"diff", MAX(Instances!B3:Instances!B4)-MIN(Instances!B3:Instances!B4))'
                        ),
                        spreadsheet.Formula(
                            '=SWITCH($A$2,"average", AVERAGE(Instances!B5:Instances!B6),'
                            '"median", MEDIAN(Instances!B5:Instances!B6),'
                            '"min", MIN(Instances!B5:Instances!B6),'
                            '"max", MAX(Instances!B5:Instances!B6),'
                            '"diff", MAX(Instances!B5:Instances!B6)-MIN(Instances!B5:Instances!B6))'
                        ),
                    ],
                    2: [np.nan, "col2", np.nan, np.nan],
                }
            ),
            check_dtype=False,
        )
        pd.testing.assert_frame_equal(
            self.sheet.values,
            pd.DataFrame(
                {
                    1: [1.0, 1.0],
                },
                index=[2, 3],
            ),
        )
        self.assertDictEqual(
            self.sheet.float_occur,
            {"time": set([1])},
        )

    def test_obtain_values(self) -> None:
        """
        Test _obtain_values method.
        """
        self.sheet.content = pd.DataFrame(
            {
                1: [
                    np.nan,
                    "time",
                    spreadsheet.Formula(
                        '=SWITCH($A$2,"average", AVERAGE(Instances!B3:Instances!B4),'
                        '"median", MEDIAN(Instances!B3:Instances!B4),'
                        '"min", MIN(Instances!B3:Instances!B4),'
                        '"max", MAX(Instances!B3:Instances!B4),'
                        '"diff", MAX(Instances!B3:Instances!B4)-MIN(Instances!B3:Instances!B4))'
                    ),
                    spreadsheet.Formula(
                        '=SWITCH($A$2,"average", AVERAGE(Instances!B5:Instances!B6),'
                        '"median", MEDIAN(Instances!B5:Instances!B6),'
                        '"min", MIN(Instances!B5:Instances!B6),'
                        '"max", MAX(Instances!B5:Instances!B6),'
                        '"diff", MAX(Instances!B5:Instances!B6)-MIN(Instances!B5:Instances!B6))'
                    ),
                ],
                2: [np.nan, "col2", np.nan, np.nan],
            }
        )
        self.sheet.values = pd.DataFrame(
            {
                1: [1.0, 1.0],
            },
            index=[2, 3],
        )

        self.sheet._obtain_values()

        pd.testing.assert_frame_equal(
            self.sheet.values,
            pd.DataFrame(
                {
                    1: [np.nan, "time", 1.0, 1.0],
                    2: [np.nan, "col2", np.nan, np.nan],
                }
            ),
            check_dtype=False,
        )

    def test_add_col_summary(self) -> None:
        """
        Test add_col_summary method.
        """
        self.sheet.content = pd.DataFrame(
            {
                0: [np.nan, "header", 1, 2],
                1: [
                    None,
                    "col1",
                    spreadsheet.Formula("=AVERAGE(Instances!B3:Instances!B4)"),
                    spreadsheet.Formula("=AVERAGE(Instances!B5:Instances!B8)"),
                ],
                2: [
                    None,
                    "col2",
                    spreadsheet.Formula("=AVERAGE(Instances!C3:Instances!C4)"),
                    spreadsheet.Formula("=AVERAGE(Instances!C5:Instances!C8)"),
                ],
                3: [None, "col3", None, None],
            }
        )
        self.sheet.values = pd.DataFrame(
            {
                0: [np.nan, "header", 1, 2],
                1: [np.nan, "time", 1.0, 1.0],
                2: [np.nan, "col2", np.nan, np.nan],
                3: [np.nan, "col3", np.nan, np.nan],
            }
        )
        self.sheet.result_offset = 4
        self.sheet.types = {"col1": "merged_runs", "col2": "None", "col3": "merged_runs"}
        self.sheet.summary_refs = {
            "min": {"col": 4, "col1": (5, "$E$3$E$6")},
            "median": {"col1": (6, "$F$3$F$6")},
            "max": {"col1": (7, "$G$3$G$6")},
        }

        with patch.object(MergedRunSheet, "_add_default_col_summary_formulas") as add_def_sum:
            self.sheet.add_col_summary()
            add_def_sum.assert_called_once_with(1, [(0, "B$3:B$4", "$E$3$E$6", "$F$3$F$6", "$G$3$G$6")])
