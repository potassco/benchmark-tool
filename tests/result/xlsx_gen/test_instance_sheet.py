"""
Test cases for InstanceSheet.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result import parser, result
from benchmarktool.result.xlsx_gen import spreadsheet
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from tests.result.xlsx_gen.test_result_sheet import TestResultSheet


# pylint: disable=protected-access
class TestInstSheet(TestResultSheet):
    """
    Test cases for InstanceSheet class.
    """

    def setUp(self) -> None:
        self.bm = MagicMock(spec=result.BenchmarkMerge)
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.ref_result_offset = 2
        self.sheet = InstanceSheet("TestSheet", self.bm, self.measures)
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        super().test_init()
        self.assertIsNone(self.sheet.runs)
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
        sheet = InstanceSheet("TestSheet", bench_merge, self.measures)
        self.assertEqual(sheet.result_offset, 8)
        self.assertEqual(sheet.runs, 2)
        select_run = spreadsheet.DataValidation(
            {
                "validate": "list",
                "source": list(range(1, sheet.runs + 1)),
                "input_message": "Select run number",
            },
            1,
            "input",
        )
        pd.testing.assert_frame_equal(
            sheet.content,
            pd.DataFrame(
                {
                    0: pd.Series(
                        [
                            None,
                            None,
                            "test_class0/test_inst00",
                            None,
                            "test_class1/test_inst10",
                            None,
                            "test_class1/test_inst11",
                            None,
                            None,
                            "SUM",
                            "AVG",
                            "DEV",
                            "DST",
                            "BEST",
                            "BETTER",
                            "WORSE",
                            "WORST",
                            None,
                            "Select run:",
                            select_run,
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

    def test_add_runspec(self) -> None:
        """
        Test add_runspec and _add_instance_result method.
        """
        run_specs = self.res.projects["test_proj0"].runspecs
        bench_merge = self.res.merge(self.res.projects.values())
        sheet = InstanceSheet("TestSheet", bench_merge, self.measures)

        sheet.add_runspec(run_specs[0])

        self.assertIsInstance(
            sheet.system_blocks[(run_specs[0].setting, run_specs[0].machine)], spreadsheet.SystemBlock
        )
        self.assertSetEqual(sheet.machines, set([run_specs[0].machine]))
        pd.testing.assert_frame_equal(
            sheet.system_blocks[(run_specs[0].setting, run_specs[0].machine)].content,
            pd.DataFrame(
                {
                    "time": ["time", 7.0, 10.0, 0.0, 3.0, 2.0, 0.1],
                    "timeout": ["timeout", 0.0, np.nan, 0.0, 0.0, 0.0, 0.0],
                    "status": ["status", 5.0, 5.0, "SATISFIABLE", "SATISFIABLE", "SATISFIABLE", "SATISFIABLE"],
                    "models": ["models", np.nan, np.nan, 1.0, 1.0, 1.0, 1.0],
                },
                index=[1, 2, 3, 4, 5, 6, 7],
            ),
            check_dtype=False,
        )

    def test_finalize_results(self) -> None:
        """
        Test _finalize_results method.
        """
        self.sheet.content = pd.DataFrame(
            {
                0: [None, "col1", 2, 3],
                1: [None, "col2", 5, 6],
            }
        )
        self.sheet.types = {"col1": "float", "col2": "string"}

        self.sheet._finalize_results()

        self.assertDictEqual(
            self.sheet.float_occur,
            {"col1": set([0])},
        )

    def test_obtain_values(self) -> None:
        """
        Test _obtain_values method.
        """
        self.sheet.content = pd.DataFrame(
            {
                0: [None, "col1", 2, 3],
                1: [None, "col2", 5, 6],
            }
        )

        self.sheet._obtain_values()

        pd.testing.assert_frame_equal(
            self.sheet.values,
            self.sheet.content,
        )

    def test_add_col_summary(self) -> None:
        """
        Test add_col_summary method.
        """
        self.sheet.content = pd.DataFrame(
            {
                0: [None, "col1", 2, 3],
                1: [None, "col2", 5, 6],
                2: [None, "col3", None, None],
            }
        )
        self.sheet.result_offset = 4
        self.sheet.types = {"col1": "float", "col2": "string", "col3": "float"}
        self.sheet.runs = 2
        self.sheet.summary_refs = {
            "min": {"col": 3, "col1": (5, "$E$3$E$6")},
            "median": {"col1": (6, "$F$3$F$6")},
            "max": {"col1": (7, "$G$3$G$6")},
        }
        self.sheet.values = self.sheet.content.copy().replace({None: np.nan})

        with (
            patch.object(InstanceSheet, "_add_default_col_summary_formulas") as add_def_sum,
            patch.object(InstanceSheet, "_add_default_col_summary_values") as add_def_val,
        ):
            self.sheet.add_col_summary()
            add_def_sum.assert_called_once_with(
                0,
                [
                    (0, "A$3:A$4", "$E$3$E$6", "$F$3$F$6", "$G$3$G$6"),
                    (
                        11,
                        "FILTER(A$3:A$4,MOD(ROW(A$3:A$4)-CHOOSE($A$16,ROW(A$3),ROW(A$4)),2)=0)",
                        "FILTER($E$3$E$6,MOD(ROW($E$3$E$6)-CHOOSE($A$16,ROW($F$3),ROW($F$4)),2)=0)",
                        "FILTER($F$3$F$6,MOD(ROW($F$3$F$6)-CHOOSE($A$16,ROW($G$3),ROW($G$4)),2)=0)",
                        "FILTER($G$3$G$6,MOD(ROW($G$3$G$6)-CHOOSE($A$16,ROW($H$3),ROW($H$4)),2)=0)",
                    ),
                ],
            )
            args, _ = add_def_val.call_args
            self.assertEqual(args[0], 0)
            self.assertEqual(args[1], "col1")
            np.testing.assert_array_equal(args[2], np.array([2.0, 3.0]))
