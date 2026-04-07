"""
Test cases for ClassSheet.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result import parser, result
from benchmarktool.result.xlsx_gen import spreadsheet
from benchmarktool.result.xlsx_gen.result_sheets.class_sheet import ClassSheet
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from tests.result.xlsx_gen.test_result_sheet import TestResultSheet


# pylint: disable=protected-access
class TestClassSheet(TestResultSheet):
    """
    Test cases for Sheet class with class benchmark runs (classSheet).
    """

    def setUp(self) -> None:
        self.bm = MagicMock(spec=result.BenchmarkMerge)
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.ref_result_offset = 2
        self.ref_sheet = InstanceSheet("Instances", self.bm, self.measures)
        self.sheet = ClassSheet("TestSheet", self.bm, self.measures, self.ref_sheet)
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        super().test_init()

        self.assertEqual(self.sheet.ref_sheet, self.ref_sheet)
        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: pd.Series(
                        [None, None, None, "SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"], dtype=object
                    )
                }
            ),
        )

        bench_merge = self.res.merge(self.res.projects.values())
        ref_sheet = InstanceSheet("Instances", bench_merge, self.measures)
        sheet = ClassSheet("TestSheet", bench_merge, self.measures, ref_sheet)
        self.assertEqual(sheet.result_offset, 4)
        pd.testing.assert_frame_equal(
            sheet.content,
            pd.DataFrame(
                {
                    0: pd.Series(
                        [
                            None,
                            None,
                            "test_class0",
                            "test_class1",
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
        Test add_runspec, _add_benchclass_summary,
        and _add_instance_results_to_benchclass_summary method.
        """
        run_specs = self.res.projects["test_proj0"].runspecs
        bench_merge = self.res.merge(self.res.projects.values())
        ref_sheet = InstanceSheet("Instances", bench_merge, self.measures)
        ref_sheet.add_runspec(run_specs[0])
        sheet = ClassSheet("TestSheet", bench_merge, self.measures, ref_sheet)

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
                        {"inst_start": 0, "inst_end": 1, "value": 8.5},
                        {"inst_start": 2, "inst_end": 5, "value": 1.275},
                    ],
                    "timeout": [
                        "timeout",
                        {"inst_start": 0, "inst_end": 1, "value": 0.0},
                        {"inst_start": 2, "inst_end": 5, "value": 0.0},
                    ],
                    "status": ["status", np.nan, np.nan],
                    "models": ["models", np.nan, {"inst_start": 2, "inst_end": 5, "value": 1.0}],
                },
                index=[1, 2, 3],
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
                    {"inst_start": 0, "inst_end": 1, "value": 8.5},
                    {"inst_start": 2, "inst_end": 5, "value": 1.275},
                ],
                2: [np.nan, "col2", np.nan, np.nan],
            }
        )
        self.sheet.types = {"time": "classresult", "col2": "None"}

        self.sheet._finalize_results()

        pd.testing.assert_frame_equal(
            self.sheet.content,
            pd.DataFrame(
                {
                    0: [np.nan, "header", 1, 2],
                    1: [
                        np.nan,
                        "time",
                        spreadsheet.Formula("=AVERAGE(Instances!B3:Instances!B4)"),
                        spreadsheet.Formula("=AVERAGE(Instances!B5:Instances!B8)"),
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
                    1: [8.5, 1.275],
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
                    spreadsheet.Formula("=AVERAGE(Instances!B3:Instances!B4)"),
                    spreadsheet.Formula("=AVERAGE(Instances!B5:Instances!B8)"),
                ],
                2: [np.nan, "col2", np.nan, np.nan],
            }
        )
        self.sheet.values = pd.DataFrame(
            {
                1: [8.5, 1.275],
            },
            index=[2, 3],
        )

        self.sheet._obtain_values()

        pd.testing.assert_frame_equal(
            self.sheet.values,
            pd.DataFrame(
                {
                    1: [np.nan, "time", 8.5, 1.275],
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
                1: [np.nan, "time", 8.5, 1.275],
                2: [np.nan, "col2", np.nan, np.nan],
                3: [np.nan, "col3", np.nan, np.nan],
            }
        )
        self.sheet.result_offset = 4
        self.sheet.types = {"col1": "classresult", "col2": "None", "col3": "classresult"}
        self.sheet.summary_refs = {
            "min": {"col": 4, "col1": (5, "$E$3$E$6")},
            "median": {"col1": (6, "$F$3$F$6")},
            "max": {"col1": (7, "$G$3$G$6")},
        }

        with (
            patch.object(ClassSheet, "_add_default_col_summary_formulas") as add_def_sum,
            patch.object(ClassSheet, "_add_default_col_summary_values") as add_def_val,
        ):
            self.sheet.add_col_summary()
            add_def_sum.assert_called_once_with(1, [(0, "B$3:B$4", "$E$3$E$6", "$F$3$F$6", "$G$3$G$6")])
            args, _ = add_def_val.call_args
            self.assertEqual(args[0], 1)
            self.assertEqual(args[1], "col1")
            np.testing.assert_array_equal(args[2], np.array([8.5, 1.275]))
