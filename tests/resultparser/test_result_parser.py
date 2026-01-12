"""
Tests for result parsers.
"""

from io import StringIO
from unittest import TestCase, mock

from benchmarktool.resultparser import clasp
from benchmarktool.runscript import runscript


class TestClaspParser(TestCase):
    """
    Test cases for clasp result parser.
    """

    def setUp(self):
        self.root = "tests/ref/results/finished"
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

    def test_parse(self):
        """
        Test parse method.
        """
        ref_f = {
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
        }
        ref_to = {
            "choices": ("float", 215295.0),
            "conflicts": ("float", 99457.0),
            "error": ("float", 0),
            "mem": ("float", 19.0),
            "memout": ("float", 0),
            "models": ("float", 18.0),
            "optimum": ("float", 7.0),
            "restarts": ("float", 327.0),
            "rstatus": ("string", "out of time"),
            "status": ("string", "SATISFIABLE"),
            "time": ("float", self.timeout),
            "timeout": ("float", 1),
        }
        ref_mo = {
            "choices": ("float", 1666.0),
            "conflicts": ("float", 950.0),
            "error": ("float", 0),
            "mem": ("float", 11.0),
            "memout": ("float", 1),
            "models": ("float", 9.0),
            "optimum": ("float", 4.0),
            "restarts": ("float", 6.0),
            "rstatus": ("string", "out of memory"),
            "status": ("string", "UNKNOWN"),
            "time": ("float", self.timeout),
            "timeout": ("float", 1),
        }
        ref_ce = {
            "error": ("float", 1),
            "memout": ("float", 0),
            "models": ("float", 4.0),
            "time": ("float", self.timeout),
            "timeout": ("float", 1),
        }
        ref_ms = {
            "error": ("float", 1),
            "memout": ("float", 0),
            "time": ("float", self.timeout),
            "timeout": ("float", 1),
        }

        self.assertDictEqual(self.parser.parse(self.root, self.rs, self.ins, 1), ref_f)
        self.root = "tests/ref/results/timeout"
        self.assertDictEqual(self.parser.parse(self.root, self.rs, self.ins, 1), ref_to)
        self.root = "tests/ref/results/memout"
        self.assertDictEqual(self.parser.parse(self.root, self.rs, self.ins, 1), ref_mo)
        self.root = "tests/ref/results/clasp_error"
        with mock.patch("sys.stderr", new=StringIO()) as e:
            self.assertDictEqual(self.parser.parse(self.root, self.rs, self.ins, 1), ref_ce)
        self.assertEqual(
            e.getvalue(),
            "*** WARNING: Run 1 of instance 'instance1' for system 'system-1.2.3' "
            "failed with unrecognized status or error! (tests/ref/results/clasp_error)\n",
        )
        self.root = "tests/ref/results/missing"
        with mock.patch("sys.stderr", new=StringIO()) as e:
            self.assertDictEqual(self.parser.parse(self.root, self.rs, self.ins, 1), ref_ms)
        self.assertEqual(
            e.getvalue(),
            "*** WARNING: Result file 'runsolver.solver' not found for run 1 of instance "
            "'instance1' for system 'system-1.2.3'! (tests/ref/results/missing)\n"
            "*** WARNING: Result file 'runsolver.watcher' not found for run 1 of instance "
            "'instance1' for system 'system-1.2.3'! (tests/ref/results/missing)\n"
            "*** WARNING: Run 1 of instance 'instance1' for system 'system-1.2.3' failed "
            "with unrecognized status or error! (tests/ref/results/missing)\n",
        )
