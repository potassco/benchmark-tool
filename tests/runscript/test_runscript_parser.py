"""
Test cases for runscript parser
"""

import inspect
import io
import os
import platform
from unittest import TestCase, mock

from lxml import etree  # type: ignore[import-untyped]

from benchmarktool.runscript import parser, runscript

# pylint: disable=protected-access


class TestParser(TestCase):
    """
    Test class for runscript parser.
    """

    def test_parse_file(self):
        """
        Test parse_file method.
        """
        p = parser.Parser()
        schemas_dir = os.path.join(os.path.dirname(inspect.getfile(parser)), "schemas")

        # valid file
        tree = p.parse_file("tests/ref/runscripts/test_runscript.xml", schemas_dir, "runscript.xsd")
        self.assertIsInstance(tree, etree._ElementTree)

        # invalid schema
        with mock.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            with self.assertRaises(SystemExit):
                p.parse_file("tests/ref/runscripts/test_runscript.xml", "tests/ref/runscripts/", "invalid_xml.xml")
            self.assertIn(
                "*** ERROR: Failed to load schema file",
                mock_stderr.getvalue(),
            )

        # file not found
        with mock.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            with self.assertRaises(SystemExit):
                p.parse_file("non_existing_file.xml", schemas_dir, "runscript.xsd")
            self.assertEqual(
                mock_stderr.getvalue(),
                "*** ERROR: File 'non_existing_file.xml' not found.\n",
            )

        # xml error
        with mock.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            with self.assertRaises(SystemExit):
                p.parse_file("tests/ref/runscripts/invalid_xml.xml", schemas_dir, "runscript.xsd")
            self.assertIn(
                "*** ERROR: XML Syntax Error in file ",
                mock_stderr.getvalue(),
            )

        # invalid runscript
        with mock.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            with self.assertRaises(SystemExit):
                p.parse_file("tests/ref/runscripts/invalid_runscript.xml", schemas_dir, "runscript.xsd")
            self.assertIn(
                "is invalid: ",
                mock_stderr.getvalue(),
            )

    # pylint: disable=too-many-statements
    def test_parse(self):
        """
        Test parse method.
        """
        p = parser.Parser()

        with mock.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            run = p.parse("tests/ref/runscripts/test_runscript.xml")
        self.assertEqual(
            mock_stderr.getvalue(),
            "*** INFO: Attribute 'extra' in distjob 'dist-generic' is currently unused.\n"
            "*** INFO: Attribute 'other' in seqjob 'seq-generic' is currently unused.\n"
            "*** INFO: Attribute 'opt' in setting 'one-as' is currently unused.\n",
        )

        # runscript
        self.assertIsInstance(run, runscript.Runscript)
        self.assertEqual(run.output, "output")

        # jobs
        self.assertEqual(len(run.jobs), 3)
        seq_job = run.jobs["seq-generic"]
        self.assertIsInstance(seq_job, runscript.SeqJob)
        self.assertEqual(seq_job.name, "seq-generic")
        self.assertEqual(seq_job.timeout, 120)
        self.assertEqual(seq_job.runs, 1)
        self.assertEqual(seq_job.memout, 1000)
        self.assertEqual(seq_job.template_options, "--single")
        self.assertDictEqual(seq_job.attr, {"other": "value"})
        self.assertEqual(seq_job.parallel, 8)
        dist_job = run.jobs["dist-generic"]
        self.assertIsInstance(dist_job, runscript.DistJob)
        self.assertEqual(dist_job.name, "dist-generic")
        self.assertEqual(dist_job.timeout, 120)
        self.assertEqual(dist_job.runs, 1)
        self.assertEqual(dist_job.memout, 1000)
        self.assertEqual(dist_job.template_options, "--single")
        self.assertDictEqual(dist_job.attr, {"extra": "test"})
        self.assertEqual(dist_job.script_mode, "timeout")
        self.assertEqual(dist_job.walltime, 86399)  # = 23:59:59
        self.assertEqual(dist_job.cpt, 1)
        self.assertEqual(dist_job.partition, "kr")  # default
        self.assertEqual(run.jobs["dist-part"].partition, "test")

        # projects
        self.assertEqual(len(run.projects), 3)
        project = run.projects["clasp-big"]
        self.assertIsInstance(project, runscript.Project)
        self.assertEqual(project.name, "clasp-big")
        self.assertTrue("houat" in project.runspecs)
        self.assertEqual(project.runscript, run)
        self.assertIsInstance(project.job, runscript.SeqJob)
        self.assertEqual(project.job.name, "seq-generic")
        project = run.projects["claspar-all-as"]
        self.assertIsInstance(project, runscript.Project)
        self.assertEqual(project.name, "claspar-all-as")
        self.assertTrue("houat" in project.runspecs)
        self.assertEqual(project.runscript, run)
        self.assertIsInstance(project.job, runscript.DistJob)
        self.assertEqual(project.job.name, "dist-generic")
        project = run.projects["claspar-one-as"]
        self.assertIsInstance(project, runscript.Project)
        self.assertEqual(project.name, "claspar-one-as")
        self.assertTrue("zuse" in project.runspecs)
        self.assertEqual(project.runscript, run)
        self.assertIsInstance(project.job, runscript.DistJob)
        self.assertEqual(project.job.name, "dist-generic")

        # machines
        self.assertEqual(len(run.machines), 2)
        machine = run.machines["houat"]
        self.assertIsInstance(machine, runscript.Machine)
        self.assertEqual(machine.name, "houat")
        self.assertEqual(machine.cpu, "8xE5520@2.27GHz")
        self.assertEqual(machine.memory, "24GB")
        machine = run.machines["zuse"]
        self.assertIsInstance(machine, runscript.Machine)
        self.assertEqual(machine.name, "zuse")
        self.assertEqual(machine.cpu, "24x8xE5520@2.27GHz")
        self.assertEqual(machine.memory, "24GB")

        # systems
        self.assertEqual(len(run.systems), 2)
        system = run.systems[("clasp", "1.3.2")]
        self.assertIsInstance(system, runscript.System)
        self.assertEqual(system.name, "clasp")
        self.assertEqual(system.version, "1.3.2")
        self.assertEqual(system.measures, "clasp")
        self.assertEqual(system.order, 0)
        self.assertEqual(len(system.settings), 7)
        self.assertIsInstance(system.config, runscript.Config)
        self.assertEqual(system.config.name, "seq-generic")
        self.assertEqual(system.settings["default"].cmdline, "--sys --stats 1 --sys_post --post")
        system = run.systems[("claspar", "2.1.0")]
        self.assertIsInstance(system, runscript.System)
        self.assertEqual(system.name, "claspar")
        self.assertEqual(system.version, "2.1.0")
        self.assertEqual(system.measures, "claspar")
        self.assertEqual(system.order, 1)
        self.assertEqual(len(system.settings), 3)
        self.assertIsInstance(system.config, runscript.Config)
        self.assertEqual(system.config.name, "dist-generic")

        # settings
        setting = system.settings["one-as"]
        self.assertIsInstance(setting, runscript.Setting)
        self.assertEqual(setting.name, "one-as")
        self.assertEqual(setting.cmdline, "--stats 1")
        self.assertSetEqual(setting.tag, {"par", "one-as"})
        self.assertEqual(setting.order, 0)
        self.assertEqual(setting.dist_template, "templates/impi.dist")
        self.assertEqual(setting.dist_options, "#SBATCH --test=1,#SBATCH --opt=test")
        self.assertDictEqual(setting.attr, {"opt": "attr"})
        self.assertDictEqual(setting.encodings, {"_default_": {"def.lp"}, "test": {"test1.lp", "test2.lp"}})
        setting = system.settings["min"]
        self.assertIsInstance(setting, runscript.Setting)
        self.assertEqual(setting.name, "min")
        self.assertEqual(setting.cmdline, "--stats")
        self.assertSetEqual(setting.tag, set())
        self.assertEqual(setting.order, 2)
        self.assertEqual(setting.dist_template, "templates/single.dist")
        self.assertEqual(setting.dist_options, "")
        self.assertDictEqual(setting.attr, {})
        self.assertDictEqual(setting.encodings, {"_default_": set(), "test": {"test21.lp"}, "test2": {"test22.lp"}})

        # configs
        self.assertEqual(len(run.configs), 2)
        config = run.configs["seq-generic"]
        self.assertIsInstance(config, runscript.Config)
        self.assertEqual(config.name, "seq-generic")
        self.assertEqual(config.template, "templates/seq-generic.sh")
        config = run.configs["dist-generic"]
        self.assertIsInstance(config, runscript.Config)
        self.assertEqual(config.name, "dist-generic")
        self.assertEqual(config.template, "templates/dist-generic.sh")

        # benchmarks
        self.assertEqual(len(run.benchmarks), 3)
        bench = run.benchmarks["seq-suite"]
        self.assertIsInstance(bench, runscript.Benchmark)
        self.assertEqual(bench.name, "seq-suite")
        self.assertEqual(len(bench.elements), 3)
        folder = bench.elements[0]
        self.assertIsInstance(folder, runscript.Benchmark.Folder)
        self.assertEqual(folder.path, "benchmarks/clasp")
        self.assertFalse(folder.group)
        self.assertSetEqual(folder.prefixes, {"pigeons"})
        self.assertEqual(len(folder.encodings), 1)
        if platform.system() == "Linux":
            self.assertSetEqual(folder.encodings, {"benchmarks/no_pigeons.lp"})
        self.assertSetEqual(folder.enctags, {"test", "test-no", "test2"})
        folder = bench.elements[1]
        self.assertIsInstance(folder, runscript.Benchmark.Folder)
        self.assertEqual(folder.path, "test-folder")
        self.assertTrue(folder.group)
        self.assertSetEqual(folder.prefixes, set())
        self.assertSetEqual(folder.encodings, set())
        self.assertSetEqual(folder.enctags, set())
        files = bench.elements[2]
        self.assertIsInstance(files, runscript.Benchmark.Files)
        self.assertEqual(files.path, "benchmarks/clasp")
        self.assertEqual(len(files.files), 2)
        if platform.system() == "Linux":
            self.assertDictEqual(
                files.files,
                {
                    "pigeonhole10-unsat": {"pigeons/pigeonhole10-unsat.lp"},
                    "pigeonhole11-unsat": {"pigeons/pigeonhole11-unsat.lp"},
                },
            )
        self.assertEqual(len(files.encodings), 2)
        self.assertSetEqual(files.enctags, {"test2"})

        # spec-test benchmark
        bench = run.benchmarks["spec-test"]
        self.assertIsInstance(bench, runscript.Benchmark)
        self.assertEqual(bench.name, "spec-test")
        self.assertEqual(len(bench.elements), 4)
        folder = bench.elements[0]
        self.assertIsInstance(folder, runscript.Benchmark.Folder)
        if platform.system() == "Linux":
            self.assertEqual(folder.path, "tests/ref/test_bench/test_folder")
        self.assertEqual(folder.class_name, "folder")
        self.assertTrue(folder.group)
        self.assertEqual(len(folder.encodings), 1)
        if platform.system() == "Linux":
            self.assertSetEqual(folder.encodings, {"tests/ref/test_bench/enc1.lp"})
        self.assertSetEqual(folder.enctags, {"encTag"})
        files = bench.elements[2]
        self.assertIsInstance(files, runscript.Benchmark.Files)
        self.assertEqual(files.path, "tests/ref/test_bench")
        self.assertEqual(files.class_name, "instances")
        self.assertEqual(len(files.files), 2)  # test_f1 grouped, tagC not used
        if platform.system() == "Linux":
            self.assertDictEqual(
                files.files,
                {
                    "test_f1": {"test_f1.2.1.lp", "test_f1.2.2.lp"},
                    "test_foldered": {"test_folder/test_foldered.lp"},
                },
            )
        self.assertEqual(len(files.encodings), 0)
        self.assertSetEqual(files.enctags, set())
        foldered = bench.elements[3]
        if platform.system() == "Linux":
            self.assertEqual(foldered.class_name, "test_folder/foldered")

    def test_filter_attr(self):
        """
        Test _filter_attr method.
        """
        p = parser.Parser()
        node = etree.Element("node", attr1="test1", attr2="test2")
        self.assertDictEqual(p._filter_attr(node, ["attr1"]), {"attr2": "test2"})

    def test_validate_components(self):
        """
        Test _validate_components method.
        """
        p = parser.Parser()
        run = runscript.Runscript("out")

        with mock.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            p.validate_components(run)
            self.assertEqual(
                mock_stderr.getvalue(),
                "*** WARNING: No machine defined in runscript.\n"
                "*** WARNING: No config defined in runscript.\n"
                "*** WARNING: No system defined in runscript.\n"
                "*** WARNING: No job defined in runscript.\n"
                "*** WARNING: No benchmark defined in runscript.\n"
                "*** WARNING: No project defined in runscript.\n",
            )

        run.systems["sys1"] = runscript.System("sys1", "1.0", "time", 0, mock.Mock(spec=runscript.Config))
        run.benchmarks["bench1"] = runscript.Benchmark("bench1")
        with mock.patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            p.validate_components(run)
            self.assertEqual(
                mock_stderr.getvalue(),
                "*** WARNING: No machine defined in runscript.\n"
                "*** WARNING: No config defined in runscript.\n"
                "*** WARNING: No setting defined for system 'sys1-1.0'.\n"
                "*** WARNING: No job defined in runscript.\n"
                "*** WARNING: No spec or instance folders/files defined/used for benchmark 'bench1'.\n"
                "*** WARNING: No project defined in runscript.\n",
            )
