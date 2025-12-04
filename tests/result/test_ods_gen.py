"""
Test cases for ods file generation.
"""

import os
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result import parser, result, xlsx_gen


class TestFormula(TestCase):
    """
    Test cases for main application functionality.
    """

    def test_init(self) -> None:
        """
        Test formula initialization.
        """
        ref = "formula"
        f = xlsx_gen.Formula(ref)
        self.assertEqual(f.formula_string, ref)

    def test_str(self) -> None:
        """
        Test __str__ method.
        """
        f = xlsx_gen.Formula("=SUM($A23:AA$4)")
        self.assertEqual(str(f), "=SUM($A23:AA$4)")
        f = xlsx_gen.Formula("SUM(test!A2:A4)")
        self.assertEqual(str(f), "=SUM(test!A2:A4)")


class TestUtils(TestCase):
    """
    Test cases for utility functions.
    """

    def test_try_float(self) -> None:
        """
        Test try_float function.
        """
        self.assertEqual(xlsx_gen.try_float("4"), 4.0)
        self.assertEqual(xlsx_gen.try_float(int(4)), 4.0)
        self.assertEqual(xlsx_gen.try_float("a"), "a")
        x = xlsx_gen.Formula("f")
        self.assertEqual(xlsx_gen.try_float(x), x)

    def test_get_cell_index(self) -> None:
        """
        Test get_cell_index function.
        """
        self.assertEqual(xlsx_gen.get_cell_index(1, 1), "B2")
        self.assertEqual(xlsx_gen.get_cell_index(1, 2, True), "$B3")
        self.assertEqual(xlsx_gen.get_cell_index(2, 1, abs_row=True), "C$2")
        self.assertEqual(xlsx_gen.get_cell_index(2, 2, True, True), "$C$3")


class TestXLSXDoc(TestCase):
    """
    Test cases for XLSXDoc class.
    """

    def setUp(self):
        self.doc = xlsx_gen.XLSXDoc(MagicMock(spec=result.BenchmarkMerge), [("test", None)])

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        self.assertIsInstance(self.doc.inst_sheet, xlsx_gen.Sheet)
        self.assertIsInstance(self.doc.class_sheet, xlsx_gen.Sheet)

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
        Test make_ods and write_row method.
        """
        self.doc.inst_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.class_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.make_xlsx("./tests/ref/new_xlsx.xlsx")
        self.assertTrue(os.path.isfile("./tests/ref/new_xlsx.xlsx"))
        os.remove("./tests/ref/new_xlsx.xlsx")


# pylint: disable=too-many-instance-attributes, too-many-statements
class TestInstSheet(TestCase):
    """
    Test cases for Sheet class without reference sheet (instSheet).
    """

    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.bench_merge = self.res.merge(self.res.projects.values())
        self.project = self.res.projects["test_proj0"]
        self.run_specs = self.project.runspecs + self.res.projects["test_proj1"].runspecs
        self.measures = [("time", "t"), ("timeout", "to"), ("status", None), ("models", None)]
        self.name = "Instances"
        self.ref_sheet = None
        self.ref_row_n = [
            "test_class0/test_inst00",
            np.nan,
            "test_class1/test_inst10",
            np.nan,
            "test_class1/test_inst11",
            np.nan,
        ]
        # system block
        self.ref_block = pd.DataFrame()
        self.ref_block["time"] = ["time", 7.0, 10.0, 0.0, 3.0, 2.0, 0.1]
        self.ref_block["timeout"] = ["timeout", 0.0, np.nan, 0.0, 0.0, 0.0, 0.0]
        self.ref_block["status"] = [
            "status",
            "UNSATISFIABLE",
            "5",
            "SATISFIABLE",
            "SATISFIABLE",
            "SATISFIABLE",
            "SATISFIABLE",
        ]
        self.ref_block["models"] = ["models", 0, 0, 1, 1, 1, 1]
        self.ref_block.index = [1, 2, 3, 4, 5, 6, 7]
        # results
        self.ref_res = pd.DataFrame()
        self.ref_res[0] = [None, None, "test_class0/test_inst00"]
        self.ref_res[1] = ["test_sys-1.0.0/test_setting0", "time", 7.0]
        self.ref_res[2] = [None, "timeout", 0.0]
        self.ref_res[3] = [None, "status", "UNSATISFIABLE"]
        self.ref_res[4] = [None, "models", 0]
        # row summary
        self.ref_res[13] = ["min", "time", xlsx_gen.Formula("=MIN($B3,$F3,$J3)")]
        self.ref_res[14] = [None, "timeout", xlsx_gen.Formula("=MIN($C3,$G3,$K3)")]
        self.ref_res[15] = [None, "models", xlsx_gen.Formula("=MIN($E3,$I3,$M3)")]
        self.ref_res[16] = ["median", "time", xlsx_gen.Formula("=MEDIAN($B3,$F3,$J3)")]
        self.ref_res[17] = [None, "timeout", xlsx_gen.Formula("=MEDIAN($C3,$G3,$K3)")]
        self.ref_res[18] = [None, "models", xlsx_gen.Formula("=MEDIAN($E3,$I3,$M3)")]
        self.ref_res[19] = ["max", "time", xlsx_gen.Formula("=MAX($B3,$F3,$J3)")]
        self.ref_res[20] = [None, "timeout", xlsx_gen.Formula("=MAX($C3,$G3,$K3)")]
        self.ref_res[21] = [None, "models", xlsx_gen.Formula("=MAX($E3,$I3,$M3)")]
        # col summary
        self.ref_sum = pd.DataFrame()
        self.ref_sum[0] = [
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
        ]
        self.ref_sum[1] = [
            "test_sys-1.0.0/test_setting0",
            "time",
            7.0,
            10.0,
            0.0,
            3.0,
            2.0,
            0.1,
            None,
            xlsx_gen.Formula("=SUM($B3:$B8)"),
            xlsx_gen.Formula("=AVERAGE($B3:$B8)"),
            xlsx_gen.Formula("=STDEV($B3:$B8)"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B8-$N3:$N8)^2)^0.5"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B8=$N3:$N8))"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B8<$Q3:$Q8))"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B8>$Q3:$Q8))"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B8=$T3:$T8))"),
        ]
        # values
        self.ref_val = pd.DataFrame()
        self.ref_val[0] = [np.nan, np.nan, "test_class0/test_inst00"]
        self.ref_val[1] = ["test_sys-1.0.0/test_setting0", "time", 7]
        self.ref_val[2] = [np.nan, "timeout", 0]
        self.ref_val[3] = [np.nan, "status", "UNSATISFIABLE"]
        self.ref_val[4] = [np.nan, "models", 0]
        # values row summary
        self.ref_val[13] = ["min", "time", 0.1]
        self.ref_val[14] = [np.nan, "timeout", 0]
        self.ref_val[15] = [np.nan, "models", 0]
        self.ref_val[16] = ["median", "time", 3.55]
        self.ref_val[17] = [np.nan, "timeout", 0]
        self.ref_val[18] = [np.nan, "models", 0]
        self.ref_val[19] = ["max", "time", 7]
        self.ref_val[20] = [np.nan, "timeout", 0]
        self.ref_val[21] = [np.nan, "models", 0]
        # values col summary
        self.ref_val_sum = pd.DataFrame()
        self.ref_val_sum[0] = [
            np.nan,
            np.nan,
            "test_class0/test_inst00",
            np.nan,
            "test_class1/test_inst10",
            np.nan,
            "test_class1/test_inst11",
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
            "test_sys-1.0.0/test_setting0",
            "time",
            7.0,
            10.0,
            0.0,
            3.0,
            2.0,
            0.1,
            np.nan,
            22.1,
            3.6833333333333336,
            4.015179531062922,
            12.367772636978739,
            -2,
            -2,
            4,
            4,
        ]
        self.all_measure_size = 34

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        ref_content = pd.DataFrame(
            [np.nan, np.nan] + self.ref_row_n + [np.nan, "SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"]
        )
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
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
        self.assertDictEqual(sheet.float_occur, {})

    def test_add_runspec(self) -> None:
        """
        Test add_runspec method.

        More in-depth testing required.
        (add_instance_results, add_benchclass_summary)
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        if sheet.ref_sheet is not None:
            sheet.ref_sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[0])
        self.assertIsInstance(
            sheet.system_blocks[(self.run_specs[0].setting, self.run_specs[0].machine)], xlsx_gen.SystemBlock
        )
        self.assertSetEqual(sheet.machines, set([self.run_specs[0].machine]))
        pd.testing.assert_frame_equal(
            sheet.system_blocks[(self.run_specs[0].setting, self.run_specs[0].machine)].content, self.ref_block
        )

    def test_finish(self) -> None:
        """
        Test finish method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        if sheet.ref_sheet is not None:
            sheet.ref_sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[0])
        with (
            patch.object(xlsx_gen.Sheet, "add_row_summary") as add_row_sum,
            patch.object(xlsx_gen.Sheet, "add_col_summary") as add_col_sum,
            patch.object(xlsx_gen.Sheet, "add_styles") as add_styles,
        ):
            sheet.finish()
            add_row_sum.assert_called_once()
            add_col_sum.assert_called_once()
            add_styles.assert_called_once()
        for row in range(3):
            for col in range(5):
                test, ref = sheet.content.at[row, col], self.ref_res.at[row, col]
                test_val, ref_val = sheet.values.at[row, col], self.ref_val.at[row, col]
                if isinstance(ref, xlsx_gen.Formula):
                    self.assertIsInstance(test, xlsx_gen.Formula)
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
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        for run_spec in self.run_specs:
            if sheet.ref_sheet is not None:
                sheet.ref_sheet.add_runspec(run_spec)
            sheet.add_runspec(run_spec)
        with patch.object(xlsx_gen.Sheet, "add_styles"):
            sheet.finish()
        for row in range(3):
            for col in range(13, 22):
                test, ref = sheet.content.at[row, col], self.ref_res.at[row, col]
                test_val, ref_val = sheet.values.at[row, col], self.ref_val.at[row, col]
                if isinstance(ref, xlsx_gen.Formula):
                    self.assertIsInstance(test, xlsx_gen.Formula)
                    self.assertEqual(str(test), str(ref))
                else:
                    self.assertEqual(test, ref)
                if pd.isna(ref_val):
                    self.assertTrue(pd.isna(test_val))
                else:
                    self.assertEqual(test_val, ref_val)
        sheet = xlsx_gen.Sheet(self.bench_merge, "", self.name, self.ref_sheet)
        if sheet.ref_sheet is not None:
            sheet.ref_sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[0])
        sheet.finish()
        self.assertEqual(len(sheet.content.columns), self.all_measure_size)

    def test_add_col_summary(self) -> None:
        """
        Test add_col_summary method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        for run_spec in self.run_specs:
            if sheet.ref_sheet is not None:
                sheet.ref_sheet.add_runspec(run_spec)
            sheet.add_runspec(run_spec)
        with patch.object(xlsx_gen.Sheet, "add_styles"):
            sheet.finish()
        for row in range(len(sheet.content.index)):
            for col in range(2):
                test, ref = sheet.content.at[row, col], self.ref_sum.at[row, col]
                test_val, ref_val = sheet.values.at[row, col], self.ref_val_sum.at[row, col]
                if isinstance(ref, xlsx_gen.Formula):
                    self.assertIsInstance(test, xlsx_gen.Formula)
                    self.assertEqual(str(test), str(ref))
                else:
                    self.assertEqual(test, ref)
                if pd.isna(ref_val):
                    self.assertTrue(pd.isna(test_val))
                else:
                    self.assertEqual(test_val, ref_val)
        # dont gen summary for empty columns while other settings have results
        for row in range(2, len(sheet.content.index)):
            self.assertTrue(pd.isna(sheet.content.at[row, 9]))

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[1])
        sheet.finish()
        # selective testing
        self.assertEqual(sheet.content.at[2, 1][1], "cellWorst")
        self.assertNotIsInstance(sheet.content.at[2, 2], tuple)
        self.assertEqual(sheet.content.at[2, 5][1], "cellBest")
        self.assertEqual(sheet.content.at[9, 1][1], "cellWorst")
        self.assertEqual(sheet.content.at[9, 5][1], "cellBest")

    def test_export_values(self) -> None:
        """
        Test export_values methods.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[1])
        sheet.finish()
        name = "file.ipynb"
        md = {"test": [1, 2, 3]}
        with patch.object(pd.DataFrame, "to_parquet") as tp:
            sheet.export_values(name, md)
            tp.assert_called_once_with(name)


# pylint: disable=too-many-instance-attributes,too-many-statements
class TestClassSheet(TestInstSheet):
    """
    Test cases for Sheet class with reference sheet (classSheet).
    """

    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.bench_merge = self.res.merge(self.res.projects.values())
        self.project = self.res.projects["test_proj0"]
        self.run_specs = self.project.runspecs + self.res.projects["test_proj1"].runspecs
        self.measures = [("time", "t"), ("timeout", "to"), ("status", None), ("models", None)]
        self.name = "Classes"
        self.ref_sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, "Instances")
        self.ref_row_n = ["test_class0", "test_class1"]
        self.ref_block = pd.DataFrame()
        # system block
        self.ref_block["time"] = [
            "time",
            {"inst_start": 0, "inst_end": 1, "value": 8.5},
            {"inst_start": 2, "inst_end": 5, "value": 1.275},
        ]
        self.ref_block["timeout"] = [
            "timeout",
            {"inst_start": 0, "inst_end": 1, "value": 0},
            {"inst_start": 2, "inst_end": 5, "value": 0},
        ]
        self.ref_block["status"] = ["status", np.nan, np.nan]
        self.ref_block["models"] = [
            "models",
            {"inst_start": 0, "inst_end": 1, "value": 0},
            {"inst_start": 2, "inst_end": 5, "value": 1},
        ]
        self.ref_block.index = [1, 2, 3]
        # results
        self.ref_res = pd.DataFrame()
        self.ref_res[0] = [None, None, "test_class0"]
        self.ref_res[1] = [
            "test_sys-1.0.0/test_setting0",
            "time",
            xlsx_gen.Formula("=AVERAGE(Instances!B3:Instances!B4)"),
        ]
        self.ref_res[2] = [None, "timeout", xlsx_gen.Formula("=SUM(Instances!C3:Instances!C4)")]
        self.ref_res[3] = [None, "status", None]
        self.ref_res[4] = [None, "models", xlsx_gen.Formula("=AVERAGE(Instances!E3:Instances!E4)")]
        # row summary
        self.ref_row_sum = pd.DataFrame()
        self.ref_res[13] = ["min", "time", xlsx_gen.Formula("=MIN($B3,$F3,$J3)")]
        self.ref_res[14] = [None, "timeout", xlsx_gen.Formula("=MIN($C3,$G3,$K3)")]
        self.ref_res[15] = [None, "models", xlsx_gen.Formula("=MIN($E3,$I3,$M3)")]
        self.ref_res[16] = ["median", "time", xlsx_gen.Formula("=MEDIAN($B3,$F3,$J3)")]
        self.ref_res[17] = [None, "timeout", xlsx_gen.Formula("=MEDIAN($C3,$G3,$K3)")]
        self.ref_res[18] = [None, "models", xlsx_gen.Formula("=MEDIAN($E3,$I3,$M3)")]
        self.ref_res[19] = ["max", "time", xlsx_gen.Formula("=MAX($B3,$F3,$J3)")]
        self.ref_res[20] = [None, "timeout", xlsx_gen.Formula("=MAX($C3,$G3,$K3)")]
        self.ref_res[21] = [None, "models", xlsx_gen.Formula("=MAX($E3,$I3,$M3)")]
        # col summary
        self.ref_sum = pd.DataFrame()
        self.ref_sum[0] = [
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
        ]
        self.ref_sum[1] = [
            "test_sys-1.0.0/test_setting0",
            "time",
            xlsx_gen.Formula("=AVERAGE(Instances!B3:Instances!B4)"),
            xlsx_gen.Formula("=AVERAGE(Instances!B5:Instances!B8)"),
            None,
            xlsx_gen.Formula("=SUM($B3:$B4)"),
            xlsx_gen.Formula("=AVERAGE($B3:$B4)"),
            xlsx_gen.Formula("=STDEV($B3:$B4)"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B4-$N3:$N4)^2)^0.5"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B4=$N3:$N4))"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B4<$Q3:$Q4))"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B4>$Q3:$Q4))"),
            xlsx_gen.Formula("=SUMPRODUCT(--($B3:$B4=$T3:$T4))"),
        ]
        # values
        self.ref_val = pd.DataFrame()
        self.ref_val[0] = [np.nan, np.nan, "test_class0"]
        self.ref_val[1] = ["test_sys-1.0.0/test_setting0", "time", 8.5]
        self.ref_val[2] = [np.nan, "timeout", 0]
        self.ref_val[3] = [np.nan, "status", np.nan]
        self.ref_val[4] = [np.nan, "models", 0]
        # values ro summary
        self.ref_val[13] = ["min", "time", 0.20500000000000002]
        self.ref_val[14] = [np.nan, "timeout", 0]
        self.ref_val[15] = [np.nan, "models", 0]
        self.ref_val[16] = ["median", "time", 4.3525]
        self.ref_val[17] = [np.nan, "timeout", 0]
        self.ref_val[18] = [np.nan, "models", 0]
        self.ref_val[19] = ["max", "time", 8.5]
        self.ref_val[20] = [np.nan, "timeout", 0]
        self.ref_val[21] = [np.nan, "models", 0]
        # values col summary
        self.ref_val_sum = pd.DataFrame()
        self.ref_val_sum[0] = [
            np.nan,
            np.nan,
            "test_class0",
            "test_class1",
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
            "test_sys-1.0.0/test_setting0",
            "time",
            8.5,
            1.275,
            np.nan,
            9.775,
            4.8875,
            5.1088464940728056,
            8.3689381046821,
            0,
            0,
            2,
            2,
        ]
        self.all_measure_size = 19

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        for run_spec in self.run_specs:
            self.ref_sheet.add_runspec(run_spec)
            sheet.add_runspec(run_spec)
        sheet.finish()
        # selective testing
        self.assertEqual(sheet.content.at[2, 1][1], "cellWorst")
        self.assertNotIsInstance(sheet.content.at[2, 2], tuple)
        self.assertEqual(sheet.content.at[2, 5][1], "cellBest")
        self.assertEqual(sheet.content.at[5, 1][1], "cellWorst")
        self.assertEqual(sheet.content.at[5, 5][1], "cellBest")

    def test_export_values(self) -> None:
        """
        Test export_values methods.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet)
        for run_spec in self.run_specs:
            self.ref_sheet.add_runspec(run_spec)
            sheet.add_runspec(run_spec)
        sheet.finish()
        name = "file.ipynb"
        md = {"test": [1, 2, 3]}
        with patch.object(pd.DataFrame, "to_parquet") as tp:
            sheet.export_values(name, md)
            tp.assert_not_called()


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
        block = xlsx_gen.SystemBlock(None, None)
        self.assertIsNone(block.setting)
        self.assertIsNone(block.machine)
        self.assertIsInstance(block.content, pd.DataFrame)
        self.assertDictEqual(block.columns, {})
        self.assertIsNone(block.offset)

        block = xlsx_gen.SystemBlock(self.setting, self.machine)
        self.assertEqual(block.setting, self.setting)
        self.assertEqual(block.machine, self.machine)

    def test_gen_name(self) -> None:
        """
        Test gen_name method.
        """
        block = xlsx_gen.SystemBlock(None, None)
        self.assertEqual(block.gen_name(False), "")
        self.sys.name = "test_sys"
        self.sys.version = "test_ver"
        self.setting.name = "test_setting"
        self.machine.name = "test_machine"
        block = xlsx_gen.SystemBlock(self.setting, self.machine)
        self.assertEqual(block.gen_name(False), "test_sys-test_ver/test_setting")
        self.assertEqual(block.gen_name(True), "test_sys-test_ver/test_setting (test_machine)")

    def test_add_cell(self) -> None:
        """
        Test add_cell method.
        """
        block = xlsx_gen.SystemBlock(None, None)
        pd.testing.assert_frame_equal(block.content, pd.DataFrame())
        block.add_cell(1, "test", "string", "val")
        ref = pd.DataFrame()
        ref.at[1, "test"] = "test"
        ref.at[3, "test"] = "val"
        pd.testing.assert_frame_equal(block.content, ref)
        self.assertDictEqual(block.columns, {"test": "string"})
