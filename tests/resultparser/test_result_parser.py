"""
Tests for result parsers.
"""

import importlib
from io import StringIO
from unittest import TestCase, mock

from benchmarktool.resultparser import clasp, open_results
from benchmarktool.runscript import runscript

common_stats = {
    "rules_f": ("float", 4036.0),
    "rules_o": ("float", 2924.0),
    "choice_rules_f": ("float", 80.0),
    "choice_rules_o": ("float", 80.0),
    "atoms_f": ("float", 1474.0),
    "atoms_o": ("float", 1474.0),
    "bodies_f": ("float", 3512.0),
    "bodies_o": ("float", 2656.0),
    "count_f": ("float", 32.0),
    "count_o": ("float", 280.0),
    "tight": ("float", 1.0),
    "variables": ("float", 3590.0),
    "constraints": ("float", 11773.0),
}

ref_stats = {
    "finished": {
        **common_stats,
        "choices": ("float", 20048.0),
        "conflicts": ("float", 15698.0),
        "error": ("float", 0),
        "mem": ("float", 12.0),
        "memout": ("float", 0),
        "models": ("float", 12.0),
        "optimum": ("float", 0.0),
        "restarts": ("float", 76.0),
        "rstatus": ("string", "ok"),
        "status": ("string", "OPTIMUM FOUND"),
        "time": ("float", 0.44),
        "timeout": ("float", 0),
    },
    "timeout": {
        **common_stats,
        "choices": ("float", 215295.0),
        "conflicts": ("float", 99457.0),
        "error": ("float", 0),
        "mem": ("float", 19.0),
        "memout": ("float", 0),
        "models": ("float", 18.0),
        "optimum": ("float", 0.0),
        "restarts": ("float", 327.0),
        "rstatus": ("string", "out of time"),
        "status": ("string", "SATISFIABLE"),
        "time": ("float", 10),
        "timeout": ("float", 1),
    },
    "memout": {
        **common_stats,
        "choices": ("float", 1666.0),
        "conflicts": ("float", 950.0),
        "error": ("float", 0),
        "mem": ("float", 11.0),
        "memout": ("float", 1),
        "models": ("float", 9.0),
        "optimum": ("float", 0.0),
        "restarts": ("float", 6.0),
        "rstatus": ("string", "out of memory"),
        "status": ("string", "UNKNOWN"),
        "time": ("float", 10),
        "timeout": ("float", 1),
    },
    "clasp_error": {
        "error": ("float", 1),
        "memout": ("float", 0),
        "models": ("float", 4.0),
        "time": ("float", 10),
        "timeout": ("float", 1),
    },
    "missing": {
        "error": ("float", 1),
        "memout": ("float", 0),
        "time": ("float", 10),
        "timeout": ("float", 1),
    },
}


class TestHelperFunctions(TestCase):
    """
    Test cases for helper functions in resultparser.
    """

    def test_open_results(self):
        """
        Test open_results helper function.
        """

        path = "tests/ref/results/clasp_default/finished"
        file_name = "runsolver.solver"
        with open_results(path, file_name) as f:
            self.assertIsNotNone(f)

        path = "tests/ref/results/clasp_default/gzip"
        file_name = "runsolver.solver"
        with open_results(path, file_name) as f:
            self.assertIsNotNone(f)


class _ClaspParserTestCase(TestCase):
    """
    Shared setup for clasp parser tests.
    """

    def setUp(self):
        self.root = "tests/ref/results/clasp_default/finished"
        self.rs = mock.Mock(spec=runscript.Runspec)
        proj = mock.Mock(spec=runscript.Project)
        job = mock.Mock(spec=runscript.Job)
        sys = mock.Mock(spec=runscript.System)
        self.timeout = 10
        job.timeout = self.timeout
        proj.job = job
        self.rs.project = proj
        self.rs.system = sys
        sys.name = "system"
        sys.version = "1.2.3"
        self.ins = mock.Mock(spec=runscript.Benchmark.Instance)
        self.ins.name = "instance1"
        self.parser = clasp


class TestClaspParser(_ClaspParserTestCase):
    """Test cases for the text clasp result parser."""

    def parse(self, name):
        """
        Parse helper.
        """
        return self.parser.parse(f"tests/ref/results/clasp_default/{name}", self.rs, self.ins, 1)

    def test_parse_finished(self):
        """
        Test parsing of a finished run.
        """
        self.assertDictEqual(self.parse("finished"), ref_stats["finished"])

    def test_parse_gzip(self):
        """
        Test parsing of a gzip-compressed run.
        """
        self.assertDictEqual(self.parse("gzip"), ref_stats["finished"])

    def test_parse_timeout(self):
        """
        Test parsing of a run that timed out.
        """
        self.assertDictEqual(self.parse("timeout"), ref_stats["timeout"])

    def test_parse_memout(self):
        """
        Test parsing of a run that ran out of memory.
        """
        self.assertDictEqual(self.parse("memout"), ref_stats["memout"])

    def test_parse_clasp_error(self):
        """
        Test parsing of a run that resulted in a clasp error.
        """
        with mock.patch("sys.stderr", new=StringIO()) as e:
            self.assertDictEqual(self.parse("clasp_error"), ref_stats["clasp_error"])
        self.assertEqual(
            e.getvalue(),
            "*** WARNING: Run 1 of instance 'instance1' for system 'system-1.2.3' "
            "failed with unrecognized status or error! (tests/ref/results/clasp_default/clasp_error)\n",
        )

    def test_parse_missing_files(self):
        """
        Test parsing of a run with missing result files.
        """
        with mock.patch("sys.stderr", new=StringIO()) as e:
            self.assertDictEqual(self.parse("missing"), ref_stats["missing"])
        self.assertEqual(
            e.getvalue(),
            "*** WARNING: Result file 'runsolver.solver' or 'runsolver.solver.gz' not found for run 1 of instance "
            "'instance1' for system 'system-1.2.3'! (tests/ref/results/clasp_default/missing)\n"
            "*** WARNING: Result file 'runsolver.watcher' or 'runsolver.watcher.gz' not found for run 1 of instance "
            "'instance1' for system 'system-1.2.3'! (tests/ref/results/clasp_default/missing)\n"
            "*** WARNING: Run 1 of instance 'instance1' for system 'system-1.2.3' failed "
            "with unrecognized status or error! (tests/ref/results/clasp_default/missing)\n",
        )


class TestClaspJsonParser(_ClaspParserTestCase):
    """Test cases for the JSON clasp result parser."""

    ref_root = "tests/ref/results/clasp_json"

    def setUp(self):
        super().setUp()
        self.parser = importlib.import_module("benchmarktool.resultparser.clasp_json")

    def parse(self, name):
        """
        Parse helper.
        """
        return self.parser.parse(f"{self.ref_root}/{name}", self.rs, self.ins, 1)

    def test_parse_finished(self):
        """
        Test parsing of a run that finished successfully.
        """
        self.assertDictEqual(self.parse("finished"), ref_stats["finished"])

    def test_parse_timeout_from_runtime(self):
        """
        Test parsing of a run that timed out based on the runtime.
        """
        self.timeout = 0.1
        self.rs.project.job.timeout = self.timeout
        expected = {
            **ref_stats["finished"],
            "time": ("float", self.timeout),
            "timeout": ("float", 1),
        }
        self.assertDictEqual(self.parse("finished"), expected)

    def test_parse_interrupted(self):
        """
        Test parsing of a run that was interrupted.
        """
        expected = ref_stats["timeout"].copy()
        del expected["optimum"]
        self.assertDictEqual(self.parse("interrupted"), expected)

    def test_parse_sat_with_cost(self):
        """
        Test parsing of a satisfiable run with an associated cost.
        """
        self.assertDictEqual(self.parse("sat_optimum"), ref_stats["timeout"])

    def test_parse_memout(self):
        """
        Test parsing of a run that ran out of memory.
        """
        self.assertDictEqual(self.parse("memout"), ref_stats["memout"])

    def test_parse_sparse_json(self):
        """
        Test parsing of a sparse JSON result file.
        """
        with mock.patch("sys.stderr", new=StringIO()) as stderr:
            result = self.parse("sparse")
        self.assertDictEqual(
            result,
            {
                "error": ("float", 1),
                "timeout": ("float", 1),
                "memout": ("float", 0),
                "tight": ("float", 0.0),
                "time": ("float", self.timeout),
                "rules_f": ("float", 0.0),
                "rules_o": ("float", 0.0),
                "rstatus": ("string", "ok"),
            },
        )
        self.assertIn("failed with unrecognized status or error", stderr.getvalue())

    def test_parse_invalid_json(self):
        """
        Test parsing of an invalid JSON result file.
        """
        with mock.patch("sys.stderr", new=StringIO()) as stderr:
            result = self.parse("invalid_json")
        self.assertDictEqual(
            result,
            {
                "error": ("float", 1),
                "timeout": ("float", 1),
                "memout": ("float", 0),
                "time": ("float", self.timeout),
                "rstatus": ("string", "ok"),
            },
        )
        self.assertIn("failed with unrecognized status or error", stderr.getvalue())

    def test_missing_result_files(self):
        """
        Test parsing when result files are missing.
        """
        with mock.patch("sys.stderr", new=StringIO()) as stderr:
            result = self.parser.parse("tests/ref/results/clasp_default/missing", self.rs, self.ins, 1)
        self.assertDictEqual(
            result,
            {
                "error": ("float", 1),
                "timeout": ("float", 1),
                "memout": ("float", 0),
                "time": ("float", self.timeout),
            },
        )
        self.assertEqual(stderr.getvalue().count("not found"), 2)
        self.assertIn("failed with unrecognized status or error", stderr.getvalue())
