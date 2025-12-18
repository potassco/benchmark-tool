"""
Test cases for xlsx file generation.
"""

from unittest import TestCase
from unittest.mock import MagicMock, Mock, call, patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import xlsxwriter

from benchmarktool.result import parser, result, xlsx_gen

# pylint: disable=too-many-lines

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


class TestDataValidation(TestCase):
    """
    Test cases for DataValidation class.
    """

    def test_init(self) -> None:
        """
        Test DataValidation initialization.
        """
        params = {
            "validate": "list",
            "source": [1, 2, 3],
            "input_message": "Select run number",
        }
        dv = xlsx_gen.DataValidation(params, 1, "cellInput")
        self.assertDictEqual(dv.params, params)
        self.assertEqual(dv.default, 1)
        self.assertEqual(dv.color, "cellInput")

    def test_write(self) -> None:
        """
        Test write method.
        """
        params = {
            "validate": "list",
            "source": [1, 2, 3],
            "input_message": "Select run number",
        }
        dv = xlsx_gen.DataValidation(params, 3, "cellInput")
        doc = MagicMock(spec=result.XLSXDoc)
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        doc.colors = {"cellInput": "#ffeeaa"}
        sheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        with patch.object(sheet, "data_validation") as mock_data_validation, patch.object(sheet, "write") as mock_write:
            dv.write(doc, sheet, 1, 2)
            mock_write.assert_called_once()
            mock_data_validation.assert_called_once_with(1, 2, 1, 2, params)

        dv = xlsx_gen.DataValidation(params, 3)
        with patch.object(sheet, "data_validation") as mock_data_validation, patch.object(sheet, "write") as mock_write:
            dv.write(doc, sheet, 1, 2)
            mock_write.assert_called_once_with(1, 2, 3)
            mock_data_validation.assert_called_once_with(1, 2, 1, 2, params)

        dv = xlsx_gen.DataValidation(params)
        with patch.object(sheet, "data_validation") as mock_data_validation, patch.object(sheet, "write") as mock_write:
            dv.write(doc, sheet, 1, 2)
            mock_write.assert_not_called()
            mock_data_validation.assert_called_once_with(1, 2, 1, 2, params)

        doc.workbook = None
        with self.assertRaises(ValueError):
            dv.write(doc, sheet, 1, 2)

    def test_eq(self) -> None:
        """
        Test __eq__ method.
        """
        params = {
            "validate": "list",
            "source": [1, 2, 3],
            "input_message": "Select run number",
        }
        dv1 = xlsx_gen.DataValidation(params, 1, "cellInput")
        dv2 = xlsx_gen.DataValidation(params, 1, "cellInput")
        self.assertEqual(dv1, dv2)

        dv2 = xlsx_gen.DataValidation(
            {
                "validate": "list",
                "source": [1, 2, 4],
                "input_message": "Select run number",
            },
            1,
            "cellInput",
        )
        self.assertNotEqual(dv1, dv2)

        with self.assertRaises(TypeError):
            dv1 == "not a DataValidation object" # pylint: disable=pointless-statement


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
        self.doc.merged_sheet.add_runspec = Mock()
        self.doc.add_runspec(runspec)
        self.doc.inst_sheet.add_runspec.assert_called_once_with(runspec)
        self.doc.class_sheet.add_runspec.assert_called_once_with(runspec)
        self.doc.merged_sheet.add_runspec.assert_called_once_with(runspec)

    def test_finish(self) -> None:
        """
        Test finish method.
        """
        self.doc.inst_sheet.finish = Mock()
        self.doc.class_sheet.finish = Mock()
        self.doc.merged_sheet.finish = Mock()
        self.doc.finish()
        self.doc.inst_sheet.finish.assert_called_once()
        self.doc.class_sheet.finish.assert_called_once()
        self.doc.merged_sheet.finish.assert_called_once()

    def test_make_xlsx(self) -> None:
        """
        Test make_xlsx and write_col method.
        """
        self.doc.inst_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.merged_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.class_sheet.content = pd.DataFrame([None, None, "test"])

        with patch.object(xlsx_gen.Sheet, "write_sheet", autospec=True) as write_sheet:
            self.doc.make_xlsx("./tests/ref/new_xlsx.xlsx")
            write_sheet.assert_has_calls(
                [
                    (call(self.doc.inst_sheet, self.doc)),
                    (call(self.doc.merged_sheet, self.doc)),
                    (call(self.doc.class_sheet, self.doc)),
                ]
            )


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
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.runs = self.res.jobs["test_seq"].runs
        self.name = "Instances"
        self.sheet_type = "instance"
        self.ref_sheet = None
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
            None,
            "RUN:",
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
            xlsx_gen.Formula("=SUM(B$3:B$8)"),
            xlsx_gen.Formula("=AVERAGE(B$3:B$8)"),
            xlsx_gen.Formula("=STDEV(B$3:B$8)"),
            xlsx_gen.Formula("=SUMPRODUCT(--(B$3:B$8-$N$3:$N$8)^2)^0.5"),
            xlsx_gen.Formula("=SUMPRODUCT(NOT(ISBLANK(B$3:B$8))*(B$3:B$8=$N$3:$N$8))"),
            xlsx_gen.Formula("=SUMPRODUCT(NOT(ISBLANK(B$3:B$8))*(B$3:B$8<$Q$3:$Q$8))"),
            xlsx_gen.Formula("=SUMPRODUCT((NOT(ISBLANK(B$3:B$8))*(B$3:B$8>$Q$3:$Q$8))+ISBLANK(B$3:B$8))"),
            xlsx_gen.Formula("=SUMPRODUCT((NOT(ISBLANK(B$3:B$8))*(B$3:B$8=$T$3:$T$8))+ISBLANK(B$3:B$8))"),
            None,
            xlsx_gen.DataValidation(
                {
                    "validate": "list",
                    "source": list(range(1, self.runs + 1)),
                    "input_message": "Select run number",
                },
                1,
                "cellInput",
            ),
            xlsx_gen.Formula("=SUM(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0))"),
            xlsx_gen.Formula("=AVERAGE(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0))"),
            xlsx_gen.Formula("=STDEV(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0))"),
            xlsx_gen.Formula(
                "=SUMPRODUCT(--(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)"
                "-FILTER($N$3:$N$8,MOD(ROW($N$3:$N$8)-CHOOSE($B$19,ROW($N$3),ROW($N$4)),2)=0))^2)^0.5"
            ),
            xlsx_gen.Formula(
                "=SUMPRODUCT(NOT(ISBLANK(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)))"
                "*(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)"
                "=FILTER($N$3:$N$8,MOD(ROW($N$3:$N$8)-CHOOSE($B$19,ROW($N$3),ROW($N$4)),2)=0)))"
            ),
            xlsx_gen.Formula(
                "=SUMPRODUCT(NOT(ISBLANK(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)))"
                "*(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)"
                "<FILTER($Q$3:$Q$8,MOD(ROW($Q$3:$Q$8)-CHOOSE($B$19,ROW($Q$3),ROW($Q$4)),2)=0)))"
            ),
            xlsx_gen.Formula(
                "=SUMPRODUCT((NOT(ISBLANK(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)))"
                "*(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)"
                ">FILTER($Q$3:$Q$8,MOD(ROW($Q$3:$Q$8)-CHOOSE($B$19,ROW($Q$3),ROW($Q$4)),2)=0)))"
                "+ISBLANK(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)))"
            ),
            xlsx_gen.Formula(
                "=SUMPRODUCT((NOT(ISBLANK(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)))"
                "*(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)"
                "=FILTER($T$3:$T$8,MOD(ROW($T$3:$T$8)-CHOOSE($B$19,ROW($T$3),ROW($T$4)),2)=0)))"
                "+ISBLANK(FILTER(B$3:B$8,MOD(ROW(B$3:B$8)-CHOOSE($B$19,ROW(B$3),ROW(B$4)),2)=0)))"
            ),
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
            np.nan,
            "RUN:",
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
        ] + [np.nan] * 10
        # all measures for runspec 0
        self.all_measure_size = 30

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
        pd.testing.assert_frame_equal(sheet.content, self.ref_sum[0].to_frame())
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
        self.assertDictEqual(sheet.formats, {})
        if self.sheet_type in ("instance", "merge"):
            self.assertEqual(sheet.runs, 2)
        else:
            self.assertIsNone(sheet.runs)

    def test_add_runspec(self) -> None:
        """
        Test add_runspec method.

        More in-depth testing required.
        (add_instance_results, add_benchclass_summary)
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
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
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
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
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
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
        sheet = xlsx_gen.Sheet(self.bench_merge, {}, self.name, self.ref_sheet, self.sheet_type)
        if sheet.ref_sheet is not None:
            sheet.ref_sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[0])
        sheet.finish()
        self.assertEqual(len(sheet.content.columns), self.all_measure_size)

    def test_add_col_summary(self) -> None:
        """
        Test add_col_summary method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
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
                elif isinstance(ref, xlsx_gen.DataValidation):
                    self.assertIsInstance(test, xlsx_gen.DataValidation)
                    self.assertDictEqual(test.params, ref.params)
                else:
                    self.assertEqual(test, ref)
                if pd.isna(ref_val):
                    self.assertTrue(pd.isna(test_val))
                else:
                    self.assertEqual(test_val, ref_val)
        # dont gen summary for empty columns while other settings have results
        for row in range(2, len(sheet.content.index)):
            self.assertTrue(pd.isna(sheet.content.at[row, 6]))

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
        sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[1])
        sheet.finish()
        # selective testing
        self.assertEqual(sheet.content.at[2, 1][1], "worst")
        self.assertNotIsInstance(sheet.content.at[2, 2], tuple)
        self.assertEqual(sheet.content.at[2, 5][1], "best")
        self.assertEqual(sheet.content.at[9, 1][1], "worst")
        self.assertEqual(sheet.content.at[9, 5][1], "best")
        self.assertDictEqual(sheet.formats, {2: "to", 6: "to"})

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

    def test_write_sheet(self) -> None:
        """
        Test write_sheet method.
        """
        doc = xlsx_gen.XLSXDoc(self.bench_merge, self.measures)
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
        sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[1])
        sheet.finish()
        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        sheet.write_sheet(doc)

        # all measures
        doc = xlsx_gen.XLSXDoc(self.bench_merge, {})
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
        sheet.add_runspec(self.run_specs[0])
        sheet.add_runspec(self.run_specs[1])
        sheet.finish()
        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        sheet.write_sheet(doc)

        # no measures (should never occur in practice)
        doc = xlsx_gen.XLSXDoc(self.bench_merge, {})
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
        sheet.add_runspec(self.run_specs[0])
        sheet.finish()
        mock_worksheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        doc.workbook.add_worksheet.return_value = mock_worksheet
        sheet.measures = {}
        sheet.write_sheet(doc)

        # invalid workbook
        doc = xlsx_gen.XLSXDoc(self.bench_merge, self.measures)
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, self.sheet_type)
        sheet.add_runspec(self.run_specs[0])
        sheet.finish()
        with self.assertRaises(ValueError):
            sheet.write_sheet(doc)


class TestMergedSheet(TestInstSheet):
    """
    Test cases for Sheet class with merged benchmark runs (mergedSheet).
    """

    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.bench_merge = self.res.merge(self.res.projects.values())
        self.project = self.res.projects["test_proj0"]
        self.run_specs = self.project.runspecs + self.res.projects["test_proj1"].runspecs
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.name = "Merged Runs"
        self.sheet_type = "merge"
        self.ref_sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, "Instances")
        self.ref_block = pd.DataFrame()
        # system block
        self.ref_block["time"] = [
            "time",
            {"inst_start": 0, "inst_end": 1, "value": 1},
            {"inst_start": 2, "inst_end": 3, "value": 1},
            {"inst_start": 4, "inst_end": 5, "value": 1},
        ]
        self.ref_block["timeout"] = [
            "timeout",
            {"inst_start": 0, "inst_end": 1, "value": 1},
            {"inst_start": 2, "inst_end": 3, "value": 1},
            {"inst_start": 4, "inst_end": 5, "value": 1},
        ]
        self.ref_block["status"] = ["status", np.nan, np.nan, np.nan]
        self.ref_block["models"] = [
            "models",
            {"inst_start": 0, "inst_end": 1, "value": 1},
            {"inst_start": 2, "inst_end": 3, "value": 1},
            {"inst_start": 4, "inst_end": 5, "value": 1},
        ]
        self.ref_block.index = [1, 2, 3, 4]
        # results
        select_criteria = xlsx_gen.DataValidation(
                {
                    "validate": "list",
                    "source": ["average", "median", "min", "max"],
                    "input_message": "Select merge criteria",
                },
                "median",
                "input",
            )
        self.ref_res = pd.DataFrame()
        self.ref_res[0] = [
            "Merge criteria:",
            select_criteria,
            "test_class0/test_inst00",
        ]
        self.ref_res[1] = [
            "test_sys-1.0.0/test_setting0",
            "time",
            xlsx_gen.Formula(
                '=SWITCH($A$2,'
                '"average", AVERAGE(Instances!B3:Instances!B4),'
                '"median", MEDIAN(Instances!B3:Instances!B4),'
                '"min", MIN(Instances!B3:Instances!B4),'
                '"max", MAX(Instances!B3:Instances!B4))'
            ),
        ]
        self.ref_res[2] = [
            None,
            "timeout",
            xlsx_gen.Formula(
                '=SWITCH($A$2,'
                '"average", AVERAGE(Instances!C3:Instances!C4),'
                '"median", MEDIAN(Instances!C3:Instances!C4),'
                '"min", MIN(Instances!C3:Instances!C4),'
                '"max", MAX(Instances!C3:Instances!C4))'
            ),
        ]
        self.ref_res[3] = [None, "status", None]
        self.ref_res[4] = [
            None,
            "models",
            xlsx_gen.Formula(
                '=SWITCH($A$2,'
                '"average", AVERAGE(Instances!E3:Instances!E4),'
                '"median", MEDIAN(Instances!E3:Instances!E4),'
                '"min", MIN(Instances!E3:Instances!E4),'
                '"max", MAX(Instances!E3:Instances!E4))'
            ),
        ]
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
            "Merge criteria:",
            select_criteria,
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
        ]
        self.ref_sum[1] = [
            "test_sys-1.0.0/test_setting0",
            "time",
            xlsx_gen.Formula(
                '=SWITCH($A$2,'
                '"average", AVERAGE(Instances!B3:Instances!B4),'
                '"median", MEDIAN(Instances!B3:Instances!B4),'
                '"min", MIN(Instances!B3:Instances!B4),'
                '"max", MAX(Instances!B3:Instances!B4))'
                ),
            xlsx_gen.Formula(
                '=SWITCH($A$2,'
                '"average", AVERAGE(Instances!B5:Instances!B6),'
                '"median", MEDIAN(Instances!B5:Instances!B6),'
                '"min", MIN(Instances!B5:Instances!B6),'
                '"max", MAX(Instances!B5:Instances!B6))'
                ),
            xlsx_gen.Formula(
                '=SWITCH($A$2,'
                '"average", AVERAGE(Instances!B7:Instances!B8),'
                '"median", MEDIAN(Instances!B7:Instances!B8),'
                '"min", MIN(Instances!B7:Instances!B8),'
                '"max", MAX(Instances!B7:Instances!B8))'
                ),
            None,
            xlsx_gen.Formula("=SUM(B$3:B$5)"),
            xlsx_gen.Formula("=AVERAGE(B$3:B$5)"),
            xlsx_gen.Formula("=STDEV(B$3:B$5)"),
            xlsx_gen.Formula("=SUMPRODUCT(--(B$3:B$5-$N$3:$N$5)^2)^0.5"),
            xlsx_gen.Formula("=SUMPRODUCT(NOT(ISBLANK(B$3:B$5))*(B$3:B$5=$N$3:$N$5))"),
            xlsx_gen.Formula("=SUMPRODUCT(NOT(ISBLANK(B$3:B$5))*(B$3:B$5<$Q$3:$Q$5))"),
            xlsx_gen.Formula("=SUMPRODUCT((NOT(ISBLANK(B$3:B$5))*(B$3:B$5>$Q$3:$Q$5))+ISBLANK(B$3:B$5))"),
            xlsx_gen.Formula("=SUMPRODUCT((NOT(ISBLANK(B$3:B$5))*(B$3:B$5=$T$3:$T$5))+ISBLANK(B$3:B$5))"),
        ]
        # values
        self.ref_val = pd.DataFrame()
        self.ref_val[0] = ["Merge criteria:", select_criteria, "test_class0/test_inst00"]
        self.ref_val[1] = ["test_sys-1.0.0/test_setting0", "time", 1]
        self.ref_val[2] = [np.nan, "timeout", 1]
        self.ref_val[3] = [np.nan, "status", np.nan]
        self.ref_val[4] = [np.nan, "models", 1]
        # values ro summary
        self.ref_val[13] = ["min", "time", 1]
        self.ref_val[14] = [np.nan, "timeout", 1]
        self.ref_val[15] = [np.nan, "models", 1]
        self.ref_val[16] = ["median", "time", 1]
        self.ref_val[17] = [np.nan, "timeout", 1]
        self.ref_val[18] = [np.nan, "models", 1]
        self.ref_val[19] = ["max", "time", 1]
        self.ref_val[20] = [np.nan, "timeout", 1]
        self.ref_val[21] = [np.nan, "models", 1]
        # values col summary
        self.ref_val_sum = pd.DataFrame()
        self.ref_val_sum[0] = [
            "Merge criteria:",
            select_criteria,
            "test_class0/test_inst00",
            "test_class1/test_inst10",
            "test_class1/test_inst11",
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
            1,
            1,
            1,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
        ]
        self.all_measure_size = 18

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        with self.assertRaises(ValueError):
            xlsx_gen.Sheet(self.bench_merge, {}, self.name, None, self.sheet_type)
        super().test_init()

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, "merge")
        for run_spec in self.run_specs:
            self.ref_sheet.add_runspec(run_spec)
            sheet.add_runspec(run_spec)
        sheet.finish()
        # no coloring only formatting
        self.assertDictEqual(sheet.formats, {2: "to", 6: "to", 10: "to"})

    def test_export_values(self):
        """
        Test export_values methods.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, "class")
        for run_spec in self.run_specs:
            self.ref_sheet.add_runspec(run_spec)
            sheet.add_runspec(run_spec)
        sheet.finish()
        name = "file.ipynb"
        md = {"test": [1, 2, 3]}
        with patch.object(pd.DataFrame, "to_parquet") as tp:
            sheet.export_values(name, md)
            tp.assert_not_called()


# pylint: disable=too-many-instance-attributes,too-many-statements
class TestClassSheet(TestInstSheet):
    """
    Test cases for Sheet class with merged benchmark classes (classSheet).
    """

    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.bench_merge = self.res.merge(self.res.projects.values())
        self.project = self.res.projects["test_proj0"]
        self.run_specs = self.project.runspecs + self.res.projects["test_proj1"].runspecs
        self.measures = {"time": "t", "timeout": "to", "status": None, "models": None}
        self.name = "Classes"
        self.sheet_type = "class"
        self.ref_sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, "Instances")
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
            xlsx_gen.Formula("=SUM(B$3:B$4)"),
            xlsx_gen.Formula("=AVERAGE(B$3:B$4)"),
            xlsx_gen.Formula("=STDEV(B$3:B$4)"),
            xlsx_gen.Formula("=SUMPRODUCT(--(B$3:B$4-$N$3:$N$4)^2)^0.5"),
            xlsx_gen.Formula("=SUMPRODUCT(NOT(ISBLANK(B$3:B$4))*(B$3:B$4=$N$3:$N$4))"),
            xlsx_gen.Formula("=SUMPRODUCT(NOT(ISBLANK(B$3:B$4))*(B$3:B$4<$Q$3:$Q$4))"),
            xlsx_gen.Formula("=SUMPRODUCT((NOT(ISBLANK(B$3:B$4))*(B$3:B$4>$Q$3:$Q$4))+ISBLANK(B$3:B$4))"),
            xlsx_gen.Formula("=SUMPRODUCT((NOT(ISBLANK(B$3:B$4))*(B$3:B$4=$T$3:$T$4))+ISBLANK(B$3:B$4))"),
        ]
        # values
        self.ref_val = pd.DataFrame()
        self.ref_val[0] = [np.nan, np.nan, "test_class0"]
        self.ref_val[1] = ["test_sys-1.0.0/test_setting0", "time", 8.5]
        self.ref_val[2] = [np.nan, "timeout", 0]
        self.ref_val[3] = [np.nan, "status", np.nan]
        self.ref_val[4] = [np.nan, "models", 0]
        # values row summary
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
            1,
            1,
        ]
        self.all_measure_size = 18

    def test_init(self) -> None:
        with self.assertRaises(ValueError):
            xlsx_gen.Sheet(self.bench_merge, {}, self.name, None, self.sheet_type)
        super().test_init()

    def test_add_styles(self) -> None:
        """
        Test add_styles method.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, "class")
        for run_spec in self.run_specs:
            self.ref_sheet.add_runspec(run_spec)
            sheet.add_runspec(run_spec)
        sheet.finish()
        # selective testing
        self.assertEqual(sheet.content.at[2, 1][1], "worst")
        self.assertNotIsInstance(sheet.content.at[2, 2], tuple)
        self.assertEqual(sheet.content.at[2, 5][1], "best")
        self.assertEqual(sheet.content.at[5, 1][1], "worst")
        self.assertEqual(sheet.content.at[5, 5][1], "best")

    def test_export_values(self) -> None:
        """
        Test export_values methods.
        """
        sheet = xlsx_gen.Sheet(self.bench_merge, self.measures, self.name, self.ref_sheet, "class")
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
