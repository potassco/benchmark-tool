"""
Tests for result parsers.
"""

from contextlib import redirect_stderr
from io import StringIO
from unittest import TestCase, mock

from benchmarktool.resultparser import clasp
from benchmarktool.runscript import runscript


class TestClaspParser(TestCase):
    """
    Test cases for clasp result parser.
    """

    def setUp(self):
        self.root = "tests/ref/run_valid"
        self.rs = mock.Mock(spec=runscript.Runspec)
        proj = mock.Mock(spec=runscript.Project)
        job = mock.Mock(spec=runscript.Job)
        self.timeout = 10
        job.timeout = self.timeout
        proj.job = job
        self.rs.project = proj
        self.ins = mock.Mock(spec=runscript.Benchmark.Instance)
        self.parser = clasp

    def test_parse(self):
        """
        Test parse method.
        """
        ref = [
            ("error", "float", 0),
            ("timeout", "float", 0),
            ("memout", "float", 0),
            ("optimum", "float", 0.0),
            ("time", "float", 0.088461),
            ("status", "string", "OPTIMUM FOUND"),
            ("models", "float", 4.0),
            ("choices", "float", 52.0),
            ("restarts", "float", 0.0),
        ]
        refb1 = [
            ("error", "float", 0),
            ("timeout", "float", 1),
            ("memout", "float", 1),
            ("time", "float", self.timeout),
            ("models", "float", 4.0),
            ("status", "string", "UNKNOWN"),
        ]
        refb2 = [
            ("error", "float", 1),
            ("timeout", "float", 1),
            ("memout", "float", 0),
            ("time", "float", self.timeout),
            ("models", "float", 4.0),
        ]

        self.assertListEqual(self.parser.parse(self.root, self.rs, self.ins), ref)
        self.root = "tests/ref/run_error/case1"
        self.assertListEqual(self.parser.parse(self.root, self.rs, self.ins), refb1)
        self.root = "tests/ref/run_error/case2"
        e = StringIO()
        with redirect_stderr(e):
            self.assertListEqual(self.parser.parse(self.root, self.rs, self.ins), refb2)
        self.assertEqual(
            e.getvalue(), "*** ERROR: Run tests/ref/run_error/case2 failed with unrecognized status or error!\n"
        )
