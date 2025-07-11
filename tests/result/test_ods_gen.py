"""
Test cases for ods file generation.
"""

import os
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result import ods_gen, parser, result


class TestFormula(TestCase):
    """
    Test cases for main application functionality.
    """

    def test_init(self) -> None:
        """
        Test formula initialization.
        """
        ref = "formula"
        f = ods_gen.Formula(ref)
        self.assertEqual(f.formula_string, ref)

    def test_str(self) -> None:
        """
        Test __str__ method.
        """
        f = ods_gen.Formula("=SUM($A23:AA$4)")
        self.assertEqual(str(f), "of:=SUM([.$A23:.AA$4])")
        f = ods_gen.Formula("SUM(test.A2:.A4)")
        self.assertEqual(str(f), "of:=SUM([test.A2:.A4])")


class TestUtils(TestCase):
    """
    Test cases for utility functions.
    """

    def test_try_float(self) -> None:
        """
        Test try_float function.
        """
        self.assertEqual(ods_gen.try_float("4"), 4.0)
        self.assertEqual(ods_gen.try_float(int(4)), 4.0)
        self.assertEqual(ods_gen.try_float("a"), "a")
        x = ods_gen.Formula("f")
        self.assertEqual(ods_gen.try_float(x), x)

    def test_get_cell_index(self) -> None:
        """
        Test get_cell_index function.
        """
        self.assertEqual(ods_gen.get_cell_index(1, 1), "B2")
        self.assertEqual(ods_gen.get_cell_index(1, 2, True), "$B3")
        self.assertEqual(ods_gen.get_cell_index(2, 1, abs_row=True), "C$2")
        self.assertEqual(ods_gen.get_cell_index(2, 2, True, True), "$C$3")


class TestODSDoc(TestCase):
    """
    Test cases for ODSDoc class.
    """

    def setUp(self):
        self.doc = ods_gen.ODSDoc(MagicMock(spec=result.BenchmarkMerge), [("test", None)])

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        self.assertIsInstance(self.doc.inst_sheet, ods_gen.Sheet)
        self.assertIsInstance(self.doc.class_sheet, ods_gen.Sheet)

    def test_add_runspec(self) -> None:
        """
        Test add_runspec method.
        """
        runspec = Mock(spec=result.Runspec)
        self.doc.inst_sheet.add_runspec = Mock()
        self.doc.class_sheet.add_runspec = Mock()
        self.doc.add_runspec(runspec)
        self.doc.inst_sheet.add_runspec.assert_called_once_with(runspec)
        self.doc.class_sheet.add_runspec.assert_called_once_with(runspec)

    def test_finish(self) -> None:
        """
        Test finish method.
        """
        self.doc.inst_sheet.finish = Mock()
        self.doc.class_sheet.finish = Mock()
        self.doc.finish()
        self.doc.inst_sheet.finish.assert_called_once()
        self.doc.class_sheet.finish.assert_called_once()

    def test_make_ods(self) -> None:
        """
        Test make_ods method.
        """
        self.doc.inst_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.class_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.make_ods("./tests/ref/new_ods.ods")
        self.assertTrue(os.path.isfile("./tests/ref/new_ods.ods"))
        os.remove("./tests/ref/new_ods.ods")


# pylint: disable=too-many-instance-attributes
class TestInstSheet(TestCase):
    """
    Test cases for Sheet class without reference sheet (instSheet).
    """

    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.bench_merge = self.res.merge(self.res.projects.values())
        self.run_spec = self.res.projects["test_proj"].runspecs
        self.measures = [("time", "t"), ("timeout", "to"), ("status", None), ("steps", None)]
        self.name = "Instances"
        self.ref_sheet = None
        self.ref_row_n = ["test_class/test_inst", np.nan]
        # system block
        self.ref_block = pd.DataFrame()
        self.ref_block["time"] = ["time", 7.0, 10.0]
        self.ref_block["timeout"] = ["timeout", 0.0, np.nan]
        self.ref_block["status"] = ["status", "test11", "test12"]
        self.ref_block["steps"] = ["steps", 50, 40]
        self.ref_block.index = [1, 2, 3]
        # results
        self.ref_res = pd.DataFrame()
        self.ref_res[0] = [None, None, "test_class/test_inst"]
        self.ref_res[1] = ["test_sys-1.0.0/test_setting", "time", 7.0]
        self.ref_res[2] = [None, "timeout", 0.0]
        self.ref_res[3] = [None, "status", "test11"]
        self.ref_res[4] = [None, "steps", 50]
        # row summary
        self.ref_res[9] = ["min", "time", ods_gen.Formula("=MIN($B3;$F3)")]
        self.ref_res[10] = [None, "timeout", ods_gen.Formula("=MIN($C3;$G3)")]
        self.ref_res[11] = [None, "steps", ods_gen.Formula("=MIN($E3;$I3)")]
        self.ref_res[12] = ["median", "time", ods_gen.Formula("=MEDIAN($B3;$F3)")]
        self.ref_res[13] = [None, "timeout", ods_gen.Formula("=MEDIAN($C3;$G3)")]
        self.ref_res[14] = [None, "steps", ods_gen.Formula("=MEDIAN($E3;$I3)")]
        self.ref_res[15] = ["max", "time", ods_gen.Formula("=MAX($B3;$F3)")]
        self.ref_res[16] = [None, "timeout", ods_gen.Formula("=MAX($C3;$G3)")]
        self.ref_res[17] = [None, "steps", ods_gen.Formula("=MAX($E3;$I3)")]
        # col summary
        self.ref_sum = pd.DataFrame()
        self.ref_sum[0] = [
            None,
            None,
            "test_class/test_inst",
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
        ]
        self.ref_sum[1] = [
            "test_sys-1.0.0/test_setting",
            "time",
            7.0,
            10.0,
            None,
            ods_gen.Formula("=SUM($B3:$B4)"),
            ods_gen.Formula("=AVERAGE($B3:$B4)"),
            ods_gen.Formula("=STDEV($B3:$B4)"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B4-$J3:$J4)^2)^0.5"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B4=$J3:$J4))"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B4<$M3:$M4))"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B4>$M3:$M4))"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B4=$P3:$P4))"),
        ]
        # values
        self.ref_val = pd.DataFrame()
        self.ref_val[0] = [np.nan, np.nan, "test_class/test_inst"]
        self.ref_val[1] = ["test_sys-1.0.0/test_setting", "time", 7]
        self.ref_val[2] = [np.nan, "timeout", 0]
        self.ref_val[3] = [np.nan, "status", "test11"]
        self.ref_val[4] = [np.nan, "steps", 50]
        # values row summary
        self.ref_val[9] = ["min", "time", 7]
        self.ref_val[10] = [np.nan, "timeout", 0]
        self.ref_val[11] = [np.nan, "steps", 49]
        self.ref_val[12] = ["median", "time", 8.5]
        self.ref_val[13] = [np.nan, "timeout", 0.5]
        self.ref_val[14] = [np.nan, "steps", 49.5]
        self.ref_val[15] = ["max", "time", 10]
        self.ref_val[16] = [np.nan, "timeout", 1]
        self.ref_val[17] = [np.nan, "steps", 50]
        # values col summary
        self.ref_val_sum = pd.DataFrame()
        self.ref_val_sum[0] = [
            np.nan,
            np.nan,
            "test_class/test_inst",
            np.nan,
            np.nan,
            "SUM",
            "AVG",
            "DEV",
            "DST",
            "BEST",
            "BETTER",
            "WORSE",
            "WORST",
        ]
        self.ref_val_sum[1] = [
            "test_sys-1.0.0/test_setting",
            "time",
            7,
            10,
            np.nan,
            17,
            8.5,
            2.1213203435596424,
            0,
            -2,
            -1,
            0,
            1,
        ]

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        ref_content = pd.DataFrame(
            [np.nan, np.nan] + self.ref_row_n + [np.nan, "SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"]
        )
        sheet = ods_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        pd.testing.assert_frame_equal(sheet.content, ref_content)
        self.assertEqual(sheet.name, self.name)
        self.assertEqual(sheet.benchmark, self.bench_merge)
        self.assertDictEqual(sheet.system_blocks, {})
        self.assertDictEqual(sheet.types, {})
        self.assertEqual(sheet.measures, self.measures)
        self.assertEqual(sheet.machines, set())
        self.assertEqual(sheet.ref_sheet, self.ref_sheet)
        self.assertDictEqual(sheet.summary_refs, {})
        pd.testing.assert_frame_equal(sheet.values, pd.DataFrame())

    def test_add_runspec(self) -> None:
        """
        Test add_runspec method.

        More in-depth testing required.
        (add_instance_results, add_benchclass_summary)
        """
        sheet = ods_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_spec[0])
        self.assertIsInstance(
            sheet.system_blocks[(self.run_spec[0].setting, self.run_spec[0].machine)], ods_gen.SystemBlock
        )
        self.assertSetEqual(sheet.machines, set([self.run_spec[0].machine]))
        pd.testing.assert_frame_equal(
            sheet.system_blocks[(self.run_spec[0].setting, self.run_spec[0].machine)].content, self.ref_block
        )

    def test_finish(self) -> None:
        """
        Test finish method.
        """
        sheet = ods_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_spec[0])
        with (
            patch.object(ods_gen.Sheet, "add_row_summary") as add_row_sum,
            patch.object(ods_gen.Sheet, "add_col_summary") as add_col_sum,
            patch.object(ods_gen.Sheet, "add_styles") as add_styles,
        ):
            sheet.finish()
            add_row_sum.assert_called_once()
            add_col_sum.assert_called_once()
            add_styles.assert_called_once()
        for row in range(3):
            for col in range(5):
                test, ref = sheet.content.at[row, col], self.ref_res.at[row, col]
                test_val, ref_val = sheet.values.at[row, col], self.ref_val.at[row, col]
                if isinstance(ref, ods_gen.Formula):
                    self.assertIsInstance(test, ods_gen.Formula)
                    self.assertEqual(str(test), str(ref))
                else:
                    self.assertEqual(test, ref)
                if pd.isna(ref_val):
                    self.assertTrue(pd.isna(test_val))
                else:
                    self.assertEqual(test_val, ref_val)

    def test_add_row_summary(self) -> None:
        """
        Test add_row_summary method.
        """
        sheet = ods_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_spec[0])
        sheet.add_runspec(self.run_spec[1])
        with patch.object(ods_gen.Sheet, "add_styles"):
            sheet.finish()
        for row in range(3):
            for col in range(9, 18):
                test, ref = sheet.content.at[row, col], self.ref_res.at[row, col]
                test_val, ref_val = sheet.values.at[row, col], self.ref_val.at[row, col]
                if isinstance(ref, ods_gen.Formula):
                    self.assertIsInstance(test, ods_gen.Formula)
                    self.assertEqual(str(test), str(ref))
                else:
                    self.assertEqual(test, ref)
                if pd.isna(ref_val):
                    self.assertTrue(pd.isna(test_val))
                else:
                    self.assertEqual(test_val, ref_val)
        sheet = ods_gen.Sheet(self.bench_merge, "", self.name, self.ref_sheet)
        sheet.add_runspec(self.run_spec[0])
        sheet.finish()
        self.assertEqual(len(sheet.content.columns), 26)

    def test_add_col_summary(self) -> None:
        """
        Test add_col_summary method.
        """
        sheet = ods_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_spec[0])
        sheet.add_runspec(self.run_spec[1])
        with patch.object(ods_gen.Sheet, "add_styles"):
            sheet.finish()
        for row in range(len(sheet.content.index)):
            for col in range(2):
                test, ref = sheet.content.at[row, col], self.ref_sum.at[row, col]
                test_val, ref_val = sheet.values.at[row, col], self.ref_val_sum.at[row, col]
                if isinstance(ref, ods_gen.Formula):
                    self.assertIsInstance(test, ods_gen.Formula)
                    self.assertEqual(str(test), str(ref))
                else:
                    self.assertEqual(test, ref)
                if pd.isna(ref_val):
                    self.assertTrue(pd.isna(test_val))
                else:
                    self.assertEqual(test_val, ref_val)

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        sheet = ods_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_spec[0])
        sheet.add_runspec(self.run_spec[1])
        sheet.finish()
        # selective testing
        self.assertEqual(sheet.content.at[2, 1][1], "cellBest")
        self.assertNotIsInstance(sheet.content.at[3, 1], tuple)
        self.assertEqual(sheet.content.at[2, 2][1], "cellBest")
        self.assertEqual(sheet.content.at[2, 6][1], "cellWorst")
        self.assertEqual(sheet.content.at[5, 1][1], "cellBest")


# pylint: disable=too-many-instance-attributes,too-many-statements
class TestClassSheet(TestInstSheet):
    """
    Test cases for Sheet class with reference sheet (classSheet).
    """

    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.bench_merge = self.res.merge(self.res.projects.values())
        self.run_spec = self.res.projects["test_proj"].runspecs
        self.measures = [("time", "t"), ("timeout", "to"), ("status", None), ("steps", None)]
        self.name = "Classes"
        self.ref_sheet = ods_gen.Sheet(self.bench_merge, self.measures, "Instances")
        self.ref_row_n = ["test_class"]
        self.ref_block = pd.DataFrame()
        # system block
        bench_cl = self.run_spec[0].classresults[0].benchclass
        self.ref_block["time"] = ["time", (bench_cl, 8.5)]
        self.ref_block["timeout"] = ["timeout", (bench_cl, 0)]
        self.ref_block["status"] = ["status", np.nan]
        self.ref_block["steps"] = ["steps", (bench_cl, 45)]
        self.ref_block.index = [1, 2]
        # results
        self.ref_res = pd.DataFrame()
        self.ref_res[0] = [None, None, "test_class"]
        self.ref_res[1] = [
            "test_sys-1.0.0/test_setting",
            "time",
            ods_gen.Formula("=AVERAGE(Instances.B3:Instances.B4)"),
        ]
        self.ref_res[2] = [None, "timeout", ods_gen.Formula("=SUM(Instances.C3:Instances.C4)")]
        self.ref_res[3] = [None, "status", None]
        self.ref_res[4] = [None, "steps", ods_gen.Formula("=AVERAGE(Instances.E3:Instances.E4)")]
        # row summary
        self.ref_row_sum = pd.DataFrame()
        self.ref_res[9] = ["min", "time", ods_gen.Formula("=MIN($B3;$F3)")]
        self.ref_res[10] = [None, "timeout", ods_gen.Formula("=MIN($C3;$G3)")]
        self.ref_res[11] = [None, "steps", ods_gen.Formula("=MIN($E3;$I3)")]
        self.ref_res[12] = ["median", "time", ods_gen.Formula("=MEDIAN($B3;$F3)")]
        self.ref_res[13] = [None, "timeout", ods_gen.Formula("=MEDIAN($C3;$G3)")]
        self.ref_res[14] = [None, "steps", ods_gen.Formula("=MEDIAN($E3;$I3)")]
        self.ref_res[15] = ["max", "time", ods_gen.Formula("=MAX($B3;$F3)")]
        self.ref_res[16] = [None, "timeout", ods_gen.Formula("=MAX($C3;$G3)")]
        self.ref_res[17] = [None, "steps", ods_gen.Formula("=MAX($E3;$I3)")]
        # col summary
        self.ref_sum = pd.DataFrame()
        self.ref_sum[0] = [
            None,
            None,
            "test_class",
            None,
            "SUM",
            "AVG",
            "DEV",
            "DST",
            "BEST",
            "BETTER",
            "WORSE",
            "WORST",
        ]
        self.ref_sum[1] = [
            "test_sys-1.0.0/test_setting",
            "time",
            ods_gen.Formula("=AVERAGE(Instances.B3:Instances.B4)"),
            None,
            ods_gen.Formula("=SUM($B3:$B3)"),
            ods_gen.Formula("=AVERAGE($B3:$B3)"),
            ods_gen.Formula("=STDEV($B3:$B3)"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B3-$J3:$J3)^2)^0.5"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B3=$J3:$J3))"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B3<$M3:$M3))"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B3>$M3:$M3))"),
            ods_gen.Formula("=SUMPRODUCT(--($B3:$B3=$P3:$P3))"),
        ]
        # values
        self.ref_val = pd.DataFrame()
        self.ref_val[0] = [np.nan, np.nan, "test_class"]
        self.ref_val[1] = ["test_sys-1.0.0/test_setting", "time", 8.5]
        self.ref_val[2] = [np.nan, "timeout", 0]
        self.ref_val[3] = [np.nan, "status", np.nan]
        self.ref_val[4] = [np.nan, "steps", 45]
        # values ro summary
        self.ref_val[9] = ["min", "time", 8.5]
        self.ref_val[10] = [np.nan, "timeout", 0]
        self.ref_val[11] = [np.nan, "steps", 29.5]
        self.ref_val[12] = ["median", "time", 9.25]
        self.ref_val[13] = [np.nan, "timeout", 1]
        self.ref_val[14] = [np.nan, "steps", 37.25]
        self.ref_val[15] = ["max", "time", 10]
        self.ref_val[16] = [np.nan, "timeout", 2]
        self.ref_val[17] = [np.nan, "steps", 45]
        # values col summary
        self.ref_val_sum = pd.DataFrame()
        self.ref_val_sum[0] = [
            np.nan,
            np.nan,
            "test_class",
            np.nan,
            "SUM",
            "AVG",
            "DEV",
            "DST",
            "BEST",
            "BETTER",
            "WORSE",
            "WORST",
        ]
        self.ref_val_sum[1] = [
            "test_sys-1.0.0/test_setting",
            "time",
            8.5,
            np.nan,
            8.5,
            8.5,
            np.nan,
            0,
            -1,
            -1,
            0,
            0,
        ]

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        sheet = ods_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_spec[0])
        sheet.add_runspec(self.run_spec[1])
        sheet.finish()
        # selective testing
        self.assertEqual(sheet.content.at[2, 2][1], "cellBest")
        self.assertNotIsInstance(sheet.content.at[2, 1], tuple)
        self.assertEqual(sheet.content.at[2, 6][1], "cellWorst")
        self.assertEqual(sheet.content.at[5, 2][1], "cellBest")


class TestSystemBlock(TestCase):
    """
    Test cases for SystemBlock class.
    """

    def setUp(self):
        self.sys = Mock(spec=result.System)
        self.setting = Mock(spec=result.Setting)
        self.setting.system = self.sys
        self.machine = Mock(spec=result.Machine)

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        block = ods_gen.SystemBlock(None, None)
        self.assertIsNone(block.setting)
        self.assertIsNone(block.machine)
        self.assertIsInstance(block.content, pd.DataFrame)
        self.assertDictEqual(block.columns, {})
        self.assertIsNone(block.offset)

        block = ods_gen.SystemBlock(self.setting, self.machine)
        self.assertEqual(block.setting, self.setting)
        self.assertEqual(block.machine, self.machine)

    def test_gen_name(self) -> None:
        """
        Test gen_name method.
        """
        block = ods_gen.SystemBlock(None, None)
        self.assertEqual(block.gen_name(False), "")
        self.sys.name = "test_sys"
        self.sys.version = "test_ver"
        self.setting.name = "test_setting"
        self.machine.name = "test_machine"
        block = ods_gen.SystemBlock(self.setting, self.machine)
        self.assertEqual(block.gen_name(False), "test_sys-test_ver/test_setting")
        self.assertEqual(block.gen_name(True), "test_sys-test_ver/test_setting (test_machine)")

    def test_add_cell(self) -> None:
        """
        Test add_cell method.
        """
        block = ods_gen.SystemBlock(None, None)
        pd.testing.assert_frame_equal(block.content, pd.DataFrame())
        block.add_cell(1, "test", "string", "val")
        ref = pd.DataFrame()
        ref.at[1, "test"] = "test"
        ref.at[3, "test"] = "val"
        pd.testing.assert_frame_equal(block.content, ref)
        self.assertDictEqual(block.columns, {"test": "string"})
