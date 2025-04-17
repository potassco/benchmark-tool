"""
Test cases for ods file generation.
"""

from unittest import TestCase
from benchmarktool.result import result, ods_gen, parser
from unittest.mock import patch, MagicMock, Mock
import pandas as pd
import numpy as np
import filecmp
import os

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
        f = ods_gen.Formula("=SUM(A2:A4)")
        self.assertEqual(f.__str__(), "of:=SUM([.A2:.A4])")
        f = ods_gen.Formula("SUM(test.A2:test.A4)")
        self.assertEqual(f.__str__(), "of:=SUM([test.A2:test.A4])")
    
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
    
class TestODSDoc(TestCase):
    """
    Test cases for ODSDoc class.
    """
    def test_init(self) -> None:
        """
        Test class initialization.
        """
        with patch('benchmarktool.result.result.BenchmarkMerge') as mock:
            bm = result.BenchmarkMerge()
            doc = ods_gen.ODSDoc(bm, [("test", None)])
            self.assertIsInstance(doc.instSheet, ods_gen.Sheet)
            self.assertIsInstance(doc.classSheet, ods_gen.Sheet)
    
    def test_addRunspec(self) -> None:
        """
        Test addRunspec method.
        """
        with patch('benchmarktool.result.result.BenchmarkMerge') as mock:
            bm = result.BenchmarkMerge()
            doc = ods_gen.ODSDoc(bm, [("test", None)])
            runspec = result.Runspec(Mock(result.System), Mock(result.Machine), Mock(result.Benchmark), Mock(result.Setting))
            doc.instSheet.addRunspec = MagicMock()
            doc.classSheet.addRunspec = MagicMock()
            doc.addRunspec(runspec)
            doc.instSheet.addRunspec.assert_called_once_with(runspec)
            doc.classSheet.addRunspec.assert_called_once_with(runspec)
    
    def test_finish(self) -> None:
        """
        Test finish method.
        """
        with patch('benchmarktool.result.result.BenchmarkMerge') as mock:
            bm = result.BenchmarkMerge()
            doc = ods_gen.ODSDoc(bm, [("test", None)])
            doc.instSheet.finish = MagicMock()
            doc.classSheet.finish = MagicMock()
            doc.finish()
            doc.instSheet.finish.assert_called_once()
            doc.classSheet.finish.assert_called_once()
    
    def test_make_ods(self) -> None:
        """
        Test make_ods method.
        """
        with patch('benchmarktool.result.result.BenchmarkMerge') as mock:
            bm = result.BenchmarkMerge()
            doc = ods_gen.ODSDoc(bm, [("test", None)])
            ref = pd.DataFrame([None, None, "test"])
            doc.instSheet.content = pd.DataFrame([np.nan, np.nan, "test"])
            doc.classSheet.content = pd.DataFrame([np.nan, np.nan, "test"])
            doc.make_ods("./tests/ref/new_ods.ods")
            pd.testing.assert_frame_equal(doc.instSheet.content, ref)
            pd.testing.assert_frame_equal(doc.classSheet.content, ref)
            self.assertTrue(os.path.isfile("./tests/ref/new_ods.ods"))
            os.remove("./tests/ref/new_ods.ods")
    
class TestInstSheet(TestCase):
    """
    Test cases for Sheet class without reference sheet (instSheet).
    """
    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.benchMerge = self.res.merge(self.res.projects.values())
        self.runSpec = self.res.projects["test_proj"].runspecs[0]
        self.measures = [("time", None), ("timeout", None)]
        self.name = "Instances"
        self.refSheet = None
        self.ref_row_n = "test_class/test_inst"

    def test_init(self) -> None:
        """
        Test class initialization.
        """
        ref_content = pd.DataFrame([np.nan, np.nan, self.ref_row_n, np.nan, "SUM", "AVG", "DEV", "DST", "BEST", "BETTER", "WORSE", "WORST"])
        Sheet = ods_gen.Sheet(self.benchMerge, self.measures, self.name, self.refSheet)
        pd.testing.assert_frame_equal(Sheet.content, ref_content)
        self.assertEqual(Sheet.name, self.name)
        self.assertEqual(Sheet.benchmark, self.benchMerge)
        self.assertDictEqual(Sheet.systemBlocks, {})
        self.assertDictEqual(Sheet.types, {})
        self.assertEqual(Sheet.measures, self.measures)
        self.assertEqual(Sheet.machines, set())
        self.assertEqual(Sheet.refSheet, self.refSheet)
        self.assertDictEqual(Sheet.summaryRefs, {})

class TestInstSheet(TestInstSheet):
    """
    Test cases for Sheet class with reference sheet (classSheet).
    """
    def setUp(self) -> None:
        self.res = parser.Parser().parse("./tests/ref/test_eval.xml")
        self.benchMerge = self.res.merge(self.res.projects.values())
        self.runSpec = self.res.projects["test_proj"].runspecs[0]
        self.measures = [("time", None), ("timeout", None)]
        self.name = "Classes"
        self.refSheet = ods_gen.Sheet(self.benchMerge, self.measures, "Instances")
        self.ref_row_n = "test_class"




