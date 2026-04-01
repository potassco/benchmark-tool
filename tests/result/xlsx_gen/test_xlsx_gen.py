"""
Test cases for xlsx file generation.
"""

import os
from unittest import TestCase
from unittest.mock import MagicMock, Mock, call, patch

import pandas as pd  # type: ignore[import-untyped]
import xlsxwriter

from benchmarktool.result import result
from benchmarktool.result.xlsx_gen import spreadsheet, xlsx_gen
from benchmarktool.result.xlsx_gen.plot_sheets.chart_sheet import ChartSheet
from benchmarktool.result.xlsx_gen.plot_sheets.helper_sheet import HelperSheet
from benchmarktool.result.xlsx_gen.result_sheets.class_sheet import ClassSheet
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.result_sheets.merged_sheet import MergedRunSheet
from benchmarktool.result.xlsx_gen.result_sheets.result_sheet import ResultSheet


class TestSheet(TestCase):
    """
    Test cases for Sheet class.
    """

    def setUp(self) -> None:
        self.bm = Mock(spec=result.BenchmarkMerge)
        self.measures = {"time": "t"}
        self.sheet = spreadsheet.Sheet("TestSheet", self.bm, self.measures)

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        self.assertEqual(self.sheet.name, "TestSheet")
        self.assertEqual(self.sheet.benchmark, self.bm)
        self.assertIsInstance(self.sheet.content, pd.DataFrame)
        self.assertDictEqual(self.sheet.measures, self.measures)

    def test_finalize(self) -> None:
        """
        Test finalize method.
        """
        with self.assertRaises(NotImplementedError):
            self.sheet.finalize()

    def test_write_sheet(self) -> None:
        """
        Test write_sheet method.
        """
        with self.assertRaises(NotImplementedError):
            self.sheet.write_sheet(MagicMock(spec=xlsx_gen.XLSXDoc))


class TestFormula(TestCase):
    """
    Test cases for Formula class.
    """

    def test_init(self) -> None:
        """
        Test formula initialization.
        """
        ref = "formula"
        f = spreadsheet.Formula(ref)
        self.assertEqual(f.formula_string, ref)

    def test_str(self) -> None:
        """
        Test __str__ method.
        """
        f = spreadsheet.Formula("=SUM($A23:AA$4)")
        self.assertEqual(str(f), "=SUM($A23:AA$4)")
        f = spreadsheet.Formula("SUM(test!A2:A4)")
        self.assertEqual(str(f), "=SUM(test!A2:A4)")
        f = spreadsheet.Formula("{SUM(test!A2:A4)}")
        self.assertEqual(str(f), "{SUM(test!A2:A4)}")

    def test_eq(self) -> None:
        """
        Test __eq__ method.
        """
        f1 = spreadsheet.Formula("=SUM($A23:AA$4)")
        f2 = spreadsheet.Formula("=SUM($A23:AA$4)")
        self.assertEqual(f1, f2)

        f2 = spreadsheet.Formula("=MIN($A23:AA$4)")
        self.assertNotEqual(f1, f2)

        with self.assertRaises(TypeError):
            f1 == "not a Formula object"  # pylint: disable=pointless-statement


class TestDataValidation(TestCase):
    """
    Test cases for DataValidation class.
    """

    def test_init(self) -> None:
        """
        Test DataValidation initialization.
        """
        dv = spreadsheet.DataValidation()
        self.assertDictEqual(dv.params, {})
        self.assertIsNone(dv.default)
        self.assertIsNone(dv.color)

        params = {
            "validate": "list",
            "source": [1, 2, 3],
            "input_message": "Select run number",
        }
        dv = spreadsheet.DataValidation(params, 1, "cellInput")
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
        dv = spreadsheet.DataValidation(params, 3, "cellInput")
        doc = MagicMock(spec=xlsx_gen.XLSXDoc)
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        doc.colors = {"cellInput": "#ffeeaa"}
        sheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        with patch.object(sheet, "data_validation") as mock_data_validation, patch.object(sheet, "write") as mock_write:
            dv.write(doc, sheet, 1, 2)
            mock_write.assert_called_once()
            mock_data_validation.assert_called_once_with(1, 2, 1, 2, params)

        dv = spreadsheet.DataValidation(params, 3)
        with patch.object(sheet, "data_validation") as mock_data_validation, patch.object(sheet, "write") as mock_write:
            dv.write(doc, sheet, 1, 2)
            mock_write.assert_called_once_with(1, 2, 3)
            mock_data_validation.assert_called_once_with(1, 2, 1, 2, params)

        dv = spreadsheet.DataValidation(params)
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
        dv1 = spreadsheet.DataValidation(params, 1, "cellInput")
        dv2 = spreadsheet.DataValidation(params, 1, "cellInput")
        self.assertEqual(dv1, dv2)

        dv2 = spreadsheet.DataValidation(
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
            dv1 == "not a DataValidation object"  # pylint: disable=pointless-statement


class TestChart(TestCase):
    """
    Test cases for Chart class.
    """

    def test_init(self) -> None:
        """
        Test Chart initialization.
        """
        chart = spreadsheet.Chart("test_chart", "line", "stacked")
        self.assertEqual(chart.title, "test_chart")
        self.assertEqual(chart.chart_type, "line")
        self.assertEqual(chart.chart_subtype, "stacked")
        self.assertListEqual(chart.series, [])
        self.assertIsNone(chart.x_axis_params)
        self.assertIsNone(chart.y_axis_params)
        self.assertIsNone(chart.size_params)
        self.assertIsNone(chart.legend_params)
        self.assertEqual(chart.style, 2)

    def test_add_series(self) -> None:
        """
        Test add_series method.
        """
        chart = spreadsheet.Chart("test_chart", "line", "stacked")
        chart.add_series({"name": "Series 1", "categories": "=Sheet1!$A$1:$A$5", "values": "=Sheet1!$B$1:$B$5"})
        self.assertEqual(len(chart.series), 1)
        self.assertEqual(chart.series[0]["name"], "Series 1")
        self.assertEqual(chart.series[0]["categories"], "=Sheet1!$A$1:$A$5")
        self.assertEqual(chart.series[0]["values"], "=Sheet1!$B$1:$B$5")

    def test_set_params(self) -> None:
        """
        Test set_params method.
        """
        chart = spreadsheet.Chart("test_chart", "line", "stacked")
        chart.set_params(
            x_axis={"name": "X-Axis", "min": 0, "max": 10},
            y_axis={"name": "Y-Axis", "min": 0, "max": 100},
            size={"width": 500, "height": 300},
            legend={"position": "bottom"},
            style=5,
        )
        self.assertEqual(chart.x_axis_params["name"], "X-Axis")
        self.assertEqual(chart.x_axis_params["min"], 0)
        self.assertEqual(chart.x_axis_params["max"], 10)
        self.assertEqual(chart.y_axis_params["name"], "Y-Axis")
        self.assertEqual(chart.y_axis_params["min"], 0)
        self.assertEqual(chart.y_axis_params["max"], 100)
        self.assertEqual(chart.size_params["width"], 500)
        self.assertEqual(chart.size_params["height"], 300)
        self.assertEqual(chart.legend_params["position"], "bottom")
        self.assertEqual(chart.style, 5)

    def test_write(self) -> None:
        """
        Test write method.
        """
        chart = spreadsheet.Chart("test_chart", "line", "stacked")
        chart.add_series({"name": "Series 1", "categories": "=Sheet1!$A$1:$A$5", "values": "=Sheet1!$B$1:$B$5"})
        doc = MagicMock(spec=xlsx_gen.XLSXDoc)
        doc.workbook = MagicMock(spec=xlsxwriter.Workbook)
        sheet = MagicMock(spec=xlsxwriter.worksheet.Worksheet)
        with patch.object(doc.workbook, "add_chart") as mock_add_chart:
            chart.write(doc, sheet, 1, 2)
            mock_add_chart.assert_called_once_with({"type": "line", "subtype": "stacked"})

        chart.chart_subtype = None
        chart.set_params(
            x_axis={"name": "X-Axis", "min": 0, "max": 10},
            y_axis={"name": "Y-Axis", "min": 0, "max": 100},
            size={"width": 500, "height": 300},
            legend={"position": "bottom"},
            style=5,
        )
        with patch.object(doc.workbook, "add_chart") as mock_add_chart:
            chart.write(doc, sheet, 1, 2)
            mock_add_chart.assert_called_once_with({"type": "line"})

        doc.workbook = None
        with self.assertRaises(ValueError):
            chart.write(doc, sheet, 1, 2)

    def test_eq(self) -> None:
        """
        Test __eq__ method.
        """
        chart1 = spreadsheet.Chart("test_chart", "line", "stacked")
        chart1.add_series({"name": "Series 1", "categories": "=Sheet1!$A$1:$A$5", "values": "=Sheet1!$B$1:$B$5"})
        chart2 = spreadsheet.Chart("test_chart", "line", "stacked")
        chart2.add_series({"name": "Series 1", "categories": "=Sheet1!$A$1:$A$5", "values": "=Sheet1!$B$1:$B$5"})
        self.assertEqual(chart1, chart2)

        chart2.add_series({"name": "Series 2", "categories": "=Sheet1!$A$1:$A$5", "values": "=Sheet1!$C$1:$C$5"})
        self.assertNotEqual(chart1, chart2)

        chart2 = spreadsheet.Chart("test_chart", "line", "stacked")
        chart2.set_params(x_axis={"name": "X-Axis"})
        self.assertNotEqual(chart1, chart2)

        with self.assertRaises(TypeError):
            chart1 == "not a Chart object"  # pylint: disable=pointless-statement


class TestUtils(TestCase):
    """
    Test cases for utility functions.
    """

    def test_try_float(self) -> None:
        """
        Test try_float function.
        """
        self.assertEqual(spreadsheet.try_float("4"), 4.0)
        self.assertEqual(spreadsheet.try_float(int(4)), 4.0)
        self.assertEqual(spreadsheet.try_float("a"), "a")
        x = spreadsheet.Formula("f")
        self.assertEqual(spreadsheet.try_float(x), x)

    def test_get_cell_index(self) -> None:
        """
        Test get_cell_index function.
        """
        self.assertEqual(spreadsheet.get_cell_index(1, 1), "B2")
        self.assertEqual(spreadsheet.get_cell_index(1, 2, True), "$B3")
        self.assertEqual(spreadsheet.get_cell_index(2, 1, abs_row=True), "C$2")
        self.assertEqual(spreadsheet.get_cell_index(2, 2, True, True), "$C$3")


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
        block = spreadsheet.SystemBlock(None, None)
        self.assertIsNone(block.setting)
        self.assertIsNone(block.machine)
        self.assertIsInstance(block.content, pd.DataFrame)
        self.assertDictEqual(block.columns, {})
        self.assertIsNone(block.offset)

        block = spreadsheet.SystemBlock(self.setting, self.machine)
        self.assertEqual(block.setting, self.setting)
        self.assertEqual(block.machine, self.machine)

    def test_gen_name(self) -> None:
        """
        Test gen_name method.
        """
        block = spreadsheet.SystemBlock(None, None)
        self.assertEqual(block.gen_name(False), "")
        self.sys.name = "test_sys"
        self.sys.version = "test_ver"
        self.setting.name = "test_setting"
        self.machine.name = "test_machine"
        block = spreadsheet.SystemBlock(self.setting, self.machine)
        self.assertEqual(block.gen_name(False), "test_sys-test_ver/test_setting")
        self.assertEqual(block.gen_name(True), "test_sys-test_ver/test_setting (test_machine)")

    def test_add_cell(self) -> None:
        """
        Test add_cell method.
        """
        block = spreadsheet.SystemBlock(None, None)
        pd.testing.assert_frame_equal(block.content, pd.DataFrame())
        block.add_cell(1, "test", "string", "val")
        ref = pd.DataFrame()
        ref.at[1, "test"] = "test"
        ref.at[3, "test"] = "val"
        ref = ref.astype(object)
        pd.testing.assert_frame_equal(block.content, ref, check_dtype=False)
        self.assertDictEqual(block.columns, {"test": "string"})


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
        self.assertIsInstance(self.doc.inst_sheet, InstanceSheet)
        self.assertIsInstance(self.doc.class_sheet, ClassSheet)
        self.assertIsInstance(self.doc.merged_sheet, MergedRunSheet)
        self.assertIsInstance(self.doc.helper_sheet, HelperSheet)
        self.assertIsInstance(self.doc.chart_sheet, ChartSheet)

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

    def test_finalize(self) -> None:
        """
        Test finalize method.
        """
        self.doc.inst_sheet.finalize = Mock()
        self.doc.class_sheet.finalize = Mock()
        self.doc.merged_sheet.finalize = Mock()
        self.doc.helper_sheet.finalize = Mock()
        self.doc.chart_sheet.finalize = Mock()
        self.doc.finalize()
        self.doc.inst_sheet.finalize.assert_called_once()
        self.doc.class_sheet.finalize.assert_called_once()
        self.doc.merged_sheet.finalize.assert_called_once()
        self.doc.helper_sheet.finalize.assert_called_once()
        self.doc.chart_sheet.finalize.assert_called_once_with(self.doc.helper_sheet)

    def test_make_xlsx(self) -> None:
        """
        Test make_xlsx and write_col method.
        """
        self.doc.inst_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.merged_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.class_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.helper_sheet.content = pd.DataFrame([None, None, "test"])
        self.doc.chart_sheet.content = pd.DataFrame([None, None, "test"])

        with (
            patch.object(ResultSheet, "write_sheet", autospec=True) as res_write_sheet,
            patch.object(ChartSheet, "write_sheet", autospec=True) as chart_write_sheet,
            patch.object(HelperSheet, "write_sheet", autospec=True) as helper_write_sheet,
        ):
            self.doc.make_xlsx("./tests/ref/new_xlsx.xlsx")
            res_write_sheet.assert_has_calls(
                [
                    (call(self.doc.inst_sheet, self.doc)),
                    (call(self.doc.merged_sheet, self.doc)),
                    (call(self.doc.class_sheet, self.doc)),
                ]
            )
            chart_write_sheet.assert_called_once_with(self.doc.chart_sheet, self.doc)
            helper_write_sheet.assert_called_once_with(self.doc.helper_sheet, self.doc)
        os.remove("./tests/ref/new_xlsx.xlsx")
