"""
Test cases for runscript parser
"""

import platform
from unittest import TestCase

from lxml import etree  # type: ignore[import-untyped]

from benchmarktool.runscript import parser, runscript

# pylint: disable=protected-access


class TestParser(TestCase):
    """
    Test class for runscript parser.
    """

    # pylint: disable=too-many-statements
    def test_parse(self):
        """
        Test parse method.
        """
        p = parser.Parser()
        run = p.parse("tests/ref/test_runscript.xml")
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
        self.assertEqual(seq_job.parallel, 8)
        dist_job = run.jobs["dist-generic"]
        self.assertIsInstance(dist_job, runscript.DistJob)
        self.assertEqual(dist_job.name, "dist-generic")
        self.assertEqual(dist_job.timeout, 120)
        self.assertEqual(dist_job.runs, 1)
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
        self.assertEqual(system.settings["default"].cmdline, "--stats 1")
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
        self.assertEqual(setting.disttemplate, "templates/impi.dist")
        self.assertEqual(setting.slurm_options, "--test=1 --opt=test")
        self.assertDictEqual(setting.attr, {})
        self.assertDictEqual(setting.encodings, {"_default_": {"def.lp"}, "test": {"test1.lp", "test2.lp"}})
        setting = system.settings["min"]
        self.assertIsInstance(setting, runscript.Setting)
        self.assertEqual(setting.name, "min")
        self.assertEqual(setting.cmdline, "--stats")
        self.assertSetEqual(setting.tag, set())
        self.assertEqual(setting.order, 2)
        self.assertEqual(setting.disttemplate, "templates/single.dist")
        self.assertEqual(setting.slurm_options, "")
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
        self.assertEqual(len(run.benchmarks), 2)
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

    def test_filter_attr(self):
        """
        Test _filter_attr method.
        """
        p = parser.Parser()
        node = etree.Element("node", attr1="test1", attr2="test2")
        self.assertDictEqual(p._filter_attr(node, ["attr1"]), {"attr2": "test2"})
