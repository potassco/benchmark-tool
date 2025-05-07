"""
Test cases for runscript classes.
"""

import io
import os
from unittest import TestCase, mock

from benchmarktool.runscript import runscript


class TestMachine(TestCase):
    """
    Test cases for Machine class.
    """

    def setUp(self):
        self.name = "name"
        self.cpu = "cpu"
        self.memory = "memory"
        self.m = runscript.Machine(self.name, self.cpu, self.memory)

    def test_init(self):
        """
        Test class Initialization.
        """
        self.assertEqual(self.m.name, self.name)
        self.assertEqual(self.m.cpu, self.cpu)
        self.assertEqual(self.m.memory, self.memory)

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        o = io.StringIO()
        self.m.to_xml(o, "\t")
        self.assertEqual(o.getvalue(), '\t<machine name="name" cpu="cpu" memory="memory"/>\n')

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.m), hash(self.m.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        m2 = runscript.Machine("name2", "cpu", "memory")
        self.assertEqual(self.m.__cmp__(self.m), 0)
        self.assertNotEqual(self.m.__cmp__(m2), 0)


class TestSystem(TestCase):
    """
    Test cases for System class.
    """

    def setUp(self):
        self.name = "name"
        self.version = "version"
        self.measures = "clasp"
        self.order = 0
        self.config = runscript.Config("config_name", "template")
        self.s = runscript.System(self.name, self.version, self.measures, self.order)

    def test_init(self):
        """
        Test class Initialization.
        """
        self.assertEqual(self.s.name, self.name)
        self.assertEqual(self.s.version, self.version)
        self.assertEqual(self.measures, self.measures)
        self.assertEqual(self.s.order, self.order)
        self.assertDictEqual(self.s.settings, {})
        self.assertIsNone(self.s.config)

    def test_add_setting(self):
        """
        Test add_setting method.
        """
        setting = mock.MagicMock()
        setting.name = "setting_name"
        self.s.add_setting(setting)
        self.assertEqual(setting.system, self.s)
        self.assertDictEqual(self.s.settings, {"setting_name": setting})

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        with mock.patch("benchmarktool.runscript.runscript.Setting", spec=True) as Setting:
            settings = [mock.Mock(name="s1", order=0), mock.Mock(name="s2", order=1)]
            Setting.side_effect = settings
            s1 = Setting()
            s2 = Setting()

        self.s.config = self.config
        o = io.StringIO()
        self.s.add_setting(s1)
        self.s.add_setting(s2)
        self.s.to_xml(o, "\t", None)
        s1.to_xml.assert_called_once_with(o, "\t\t")
        s2.to_xml.assert_called_once_with(o, "\t\t")
        s2.to_xml.assert_called
        self.assertEqual(
            o.getvalue(),
            '\t<system name="name" version="version" measures="clasp" config="config_name">\n\t</system>\n',
        )

        s1.to_xml.reset_mock()
        s2.to_xml.reset_mock()
        self.s.settings = {}
        self.s.add_setting(s2)
        self.s.to_xml(o, "\t", [s2])
        s1.to_xml.assert_not_called()
        s2.to_xml.assert_called_once_with(o, "\t\t")

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.s), hash((self.s.name, self.s.version)))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        s2 = runscript.System("name2", "version", "clasp", 0)
        self.assertEqual(self.s.__cmp__(self.s), 0)
        self.assertNotEqual(self.s.__cmp__(s2), 0)


class TestSetting(TestCase):
    """
    Test cases for Setting class.
    """

    def setUp(self):
        self.name = "name"
        self.cmdline = "cmdline"
        self.tag = {"tag1", "tag2"}
        self.order = 0
        self.procs = 1
        self.ppn = 2
        self.template = "template"
        self.attr = {"key": "val"}
        self.s = runscript.Setting(
            self.name, self.cmdline, self.tag, self.order, self.procs, self.ppn, self.template, self.attr
        )

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.s.name, self.name)
        self.assertEqual(self.s.cmdline, self.cmdline)
        self.assertSetEqual(self.s.tag, self.tag)
        self.assertEqual(self.s.order, self.order)
        self.assertEqual(self.s.procs, self.procs)
        self.assertEqual(self.s.ppn, self.ppn)
        self.assertEqual(self.s.pbstemplate, self.template)
        self.assertDictEqual(self.s.attr, self.attr)

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        o = io.StringIO()
        self.s.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<setting name="name" cmdline="cmdline" tag="tag1 tag2" procs="1" ppn="2" pbstemplate="template" key="val"/>\n',
        )

        o = io.StringIO()
        self.s.procs = None
        self.s.ppn = None
        self.s.attr = {}
        self.s.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<setting name="name" cmdline="cmdline" tag="tag1 tag2" pbstemplate="template"/>\n',
        )

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.s), hash(self.s.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        s2 = runscript.Setting(
            "name2", self.cmdline, self.tag, self.order, self.procs, self.ppn, self.template, self.attr
        )
        self.assertEqual(self.s.__cmp__(self.s), 0)
        self.assertNotEqual(self.s.__cmp__(s2), 0)


class TestJob(TestCase):
    """
    Test cases for Job class.
    """

    def setUp(self):
        self.name = "name"
        self.timeout = 20
        self.runs = 2
        self.attr = {"key": "val"}
        self.j = runscript.Job(self.name, self.timeout, self.runs, self.attr)

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.j.name, self.name)
        self.assertEqual(self.j.timeout, self.timeout)
        self.assertEqual(self.j.runs, self.runs)
        self.assertDictEqual(self.j.attr, self.attr)

    def test_to_xml(self):
        """
        Test _to_xml method.
        """
        o = io.StringIO()
        tag = "tag"
        extra = " extra"
        self.j._to_xml(o, "\t", tag, extra)
        self.assertEqual(
            o.getvalue(),
            '\t<tag name="name" timeout="20" runs="2" extra key="val"/>\n',
        )

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.j), hash(self.j.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        j2 = runscript.Job("name2", self.timeout, self.runs, self.attr)
        self.assertEqual(self.j.__cmp__(self.j), 0)
        self.assertNotEqual(self.j.__cmp__(j2), 0)


class testSeqJob(TestJob):
    """
    Test cases for SeqJob class.
    """

    def setUp(self):
        self.name = "name"
        self.timeout = 20
        self.runs = 2
        self.parallel = 4
        self.attr = {"key": "val"}
        self.j = runscript.SeqJob(self.name, self.timeout, self.runs, self.parallel, self.attr)

    def test_init(self):
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.j.parallel, self.parallel)

    def test_to_xml(self):
        """
        Test _to_xml method.
        """
        o = io.StringIO()
        o2 = io.StringIO()
        self.j._to_xml(o, "\t", "seqjob", ' parallel="4"')
        self.j.to_xml(o2, "\t")
        self.assertEqual(o2.getvalue(), o.getvalue())

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        j2 = runscript.SeqJob("name2", self.timeout, self.runs, self.parallel, self.attr)
        self.assertEqual(self.j.__cmp__(self.j), 0)
        self.assertNotEqual(self.j.__cmp__(j2), 0)

    def test_script_gen(self):
        """
        Test script_gen method.
        """
        ref = runscript.SeqScriptGen
        with mock.patch("benchmarktool.runscript.runscript.SeqScriptGen", spec=True):
            self.assertIsInstance(self.j.script_gen(), ref)


class testPbsJob(TestJob):
    """
    Test cases for PbsJob class.
    """

    def setUp(self):
        self.name = "name"
        self.timeout = 20
        self.runs = 2
        self.scriptmode = "mode"
        self.walltime = 100
        self.cpt = 2
        self.partition = "all"
        self.attr = {"key": "val"}
        self.j = runscript.PbsJob(
            self.name, self.timeout, self.runs, self.scriptmode, self.walltime, self.cpt, self.partition, self.attr
        )

    def test_init(self):
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.j.script_mode, self.scriptmode)
        self.assertEqual(self.j.walltime, self.walltime)
        self.assertEqual(self.j.cpt, self.cpt)
        self.assertEqual(self.j.partition, self.partition)

    def test_to_xml(self):
        """
        Test _to_xml method.
        """
        o = io.StringIO()
        o2 = io.StringIO()
        self.j._to_xml(o, "\t", "pbsjob", ' script_mode="mode" walltime="100" cpt="2" partition="all"')
        self.j.to_xml(o2, "\t")
        self.assertEqual(o2.getvalue(), o.getvalue())

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        j2 = runscript.PbsJob(
            "name2", self.timeout, self.runs, self.scriptmode, self.walltime, self.cpt, self.partition, self.attr
        )
        self.assertEqual(self.j.__cmp__(self.j), 0)
        self.assertNotEqual(self.j.__cmp__(j2), 0)

    def test_script_gen(self):
        """
        Test script_gen method.
        """
        ref = runscript.PbsScriptGen
        with mock.patch("benchmarktool.runscript.runscript.PbsScriptGen", spec=True):
            self.assertIsInstance(self.j.script_gen(), ref)


class TestRun(TestCase):
    """
    Test cases for Run class.
    """

    def setUp(self):
        self.path = "path"
        self.r = runscript.Run(self.path)

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.r.path, self.path)
        self.assertEqual(self.r.root, os.path.relpath(".", self.path))


class TestSeqRun(TestRun):
    """
    Test cases for SeqRun class.
    """

    def setUp(self):
        self.path = "path"
        self.run_var = 1
        self.job = mock.Mock(spec=runscript.Job)
        self.job.timeout = 10
        self.runspec = mock.Mock(spec=runscript.Runspec)
        self.runspec.setting = mock.Mock(spec=runscript.Setting)
        self.runspec.setting.cmdline = "cmdline"
        self.runspec.system = mock.Mock(spec=runscript.System)
        self.runspec.system.name = "sys_name"
        self.runspec.system.version = "sys_version"
        self.instance = mock.Mock(spec=runscript.Benchmark.Instance)
        self.instance.path.return_value = "inst_path"
        self.instance.encodings = {"encoding"}
        self.r = runscript.SeqRun(self.path, self.run_var, self.job, self.runspec, self.instance)

    def test_init(self):
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.r.run, self.run_var)
        self.assertEqual(self.r.job, self.job)
        self.assertEqual(self.r.runspec, self.runspec)
        self.assertEqual(self.r.instance, self.instance)
        self.assertEqual(self.r.file, os.path.relpath(self.instance.path(), self.path))
        self.assertEqual(
            self.r.encodings, " ".join([f'"{os.path.relpath(e, self.path)}"' for e in self.instance.encodings])
        )
        self.assertEqual(self.r.args, self.runspec.setting.cmdline)
        self.assertEqual(self.r.solver, self.runspec.system.name + "-" + self.runspec.system.version)
        self.assertEqual(self.r.timeout, self.job.timeout)


class TestScriptGen(TestCase):
    """
    Test cases for ScriptGen class.
    """

    def setUp(self):
        self.job = mock.Mock(spec=runscript.Job)
        self.sg = runscript.ScriptGen(self.job)

    def setup_obj(self):
        """
        Setup helper objects.
        """
        self.runspec = mock.Mock(spec=runscript.Runspec)
        self.runspec.setting = mock.Mock(spec=runscript.Setting)
        self.runspec.setting.cmdline = "cmdline"
        self.runspec.path.return_value = "runspec_path"
        self.runspec.project = mock.Mock(spec=runscript.Project)
        self.runspec.project.job = self.job
        self.runspec.system = mock.Mock(spec=runscript.System)
        self.runspec.system.name = "sys_name"
        self.runspec.system.version = "sys_version"
        self.runspec.system.config = mock.Mock(spec=runscript.Config)
        self.runspec.system.config.template = "tests/ref/test_template.sh"
        self.runspec.system.measures = "result_parser"

        self.sg.job.runs = 1
        self.sg.job.timeout = 10

        self.instance = mock.Mock(spec=runscript.Benchmark.Instance)
        self.instance.name = "inst_name"
        self.instance.encodings = {"encoding"}
        self.instance.path.return_value = "inst_path"
        self.instance.benchclass = mock.Mock(sepc=runscript.Benchmark.Class)
        self.instance.benchclass.name = "class_name"

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertFalse(self.sg.skip)
        self.assertEqual(self.sg.job, self.job)
        self.assertListEqual(self.sg.startfiles, [])

    def test_set_skip(self):
        """
        Test set_skip method.
        """
        self.assertFalse(self.sg.skip)
        self.sg.set_skip(True)
        self.assertTrue(self.sg.skip)
        self.sg.set_skip(False)
        self.assertFalse(self.sg.skip)

    def test_path(self):
        """
        Test _path method.
        """
        self.setup_obj()
        self.assertEqual(
            self.sg._path(self.runspec, self.instance, 1),
            os.path.join(self.runspec.path(), self.instance.benchclass.name, self.instance.name, "run%d" % 1),
        )

    def test_add_to_script(self):
        """
        Test add_to_script method.
        """
        self.setup_obj()
        with (
            mock.patch("benchmarktool.runscript.runscript.ScriptGen._path", return_value="tests/ref"),
            mock.patch("benchmarktool.tools.mkdir_p") as mkdir,
            mock.patch("benchmarktool.tools.set_executable") as set_exec,
        ):
            self.sg.add_to_script(self.runspec, self.instance)
            p = self.sg._path(self.runspec, self.instance, 1)
            mkdir.assert_called_once_with(p)
            set_exec.assert_called_once_with(os.path.join(p, "start.sh"))
        self.assertListEqual(self.sg.startfiles, [(self.runspec, "tests/ref", "start.sh")])
        self.assertTrue(os.path.isfile("./tests/ref/start.sh"))
        with open("./tests/ref/start.sh", "r", encoding="utf8") as f:
            x = f.read()
        self.assertTrue(
            x
            in [
                '$CAT ../../inst_path ../.. 10 ../../programs/sys_name-sys_version cmdline "../../encoding"',
                '$CAT ..\..\inst_path ..\.. 10 ..\../programs/sys_name-sys_version cmdline "..\..\encoding"',
            ]
        )
        os.remove("./tests/ref/start.sh")

        self.sg.skip = True
        with (
            mock.patch("benchmarktool.runscript.runscript.ScriptGen._path", return_value="tests/ref"),
            mock.patch("benchmarktool.tools.mkdir_p") as mkdir,
            mock.patch("benchmarktool.tools.set_executable") as set_exec,
            mock.patch("os.path.isfile", return_value=True),
        ):
            self.sg.add_to_script(self.runspec, self.instance)
            p = self.sg._path(self.runspec, self.instance, 1)
            mkdir.assert_called_once_with(p)
            set_exec.assert_not_called()
        self.assertListEqual(self.sg.startfiles, [(self.runspec, "tests/ref", "start.sh")])
        self.assertFalse(os.path.isfile("./tests/ref/start.sh"))

    def test_eval_results(self):
        """
        Test eval_results method.
        """
        self.setup_obj()
        o = io.StringIO()
        with mock.patch("benchmarktool.config.result_parser", return_value=[("time", "int", 5)], create=True):
            self.sg.eval_results(o, "\t", self.runspec, self.instance)
        self.assertEqual(o.getvalue(), '\t<run number="1">\n\t\t<measure name="time" type="int" val="5"/>\n\t</run>\n')


class TestSeqScriptGen(TestScriptGen):
    """
    Test cases for SeqScriptGen class.
    """

    def setUp(self):
        self.job = mock.Mock(spec=runscript.SeqJob)
        self.job.parallel = 2
        self.sg = runscript.SeqScriptGen(self.job)

    def test_gen_start_script(self):
        """
        Test gen_start_script method.
        """
        self.setup_obj()
        self.sg.startfiles = [(self.runspec, "tests/ref", "s1.sh"), (self.runspec, "tests/ref", "s2.sh")]
        with (
            mock.patch("benchmarktool.tools.mkdir_p") as mkdir,
            mock.patch("benchmarktool.tools.set_executable") as set_exec,
        ):
            p = "tests/ref"
            self.sg.gen_start_script("tests/ref")
            mkdir.assert_called_once_with(p)
            set_exec.assert_called_once_with(os.path.join(p, "start.py"))

        self.assertTrue(os.path.isfile("./tests/ref/start.py"))
        os.remove("./tests/ref/start.py")


class TestPbsScript(TestCase):
    """
    Test cases for PbsScriptGen.PbsScript class.
    """

    def setUp(self):
        self.runspec = mock.Mock(spec=runscript.Runspec)
        self.path = "tests/ref"
        self.queue = []

    def test_init(self):
        """
        Test class initialization.
        """
        with mock.patch("benchmarktool.runscript.runscript.PbsScriptGen.PbsScript.next") as next:
            ps = runscript.PbsScriptGen.PbsScript(self.runspec, self.path, self.queue)
            next.assert_called_once
        self.assertEqual(ps.runspec, self.runspec)
        self.assertEqual(ps.path, self.path)
        self.assertListEqual(ps.queue, self.queue)
        self.assertEqual(ps.num, 0)
        self.assertEqual(ps.time, 0)
        self.assertEqual(ps.startscripts, "")

    def test_write(self):
        """
        Test write method.
        """
        with mock.patch("benchmarktool.runscript.runscript.PbsScriptGen.PbsScript.next"):
            ps = runscript.PbsScriptGen.PbsScript(self.runspec, self.path, self.queue)
        ps.startscripts = "job.sh"
        ps.num = 1
        ps.runspec.setting = mock.Mock(spec=runscript.Setting)
        ps.runspec.setting.pbstemplate = "tests/ref/test_pbstemplate.pbs"
        ps.runspec.setting.procs = 4
        ps.runspec.setting.ppn = 2

        ps.runspec.project = mock.Mock(spec=runscript.Project)
        ps.runspec.project.job = mock.Mock(spec=runscript.PbsJob)
        ps.runspec.project.job.walltime = 100
        ps.runspec.project.job.cpt = 1
        ps.runspec.project.job.partition = "all"
        ps.write()

        self.assertTrue(ps.queue[0] in ["tests/ref/start0000.pbs", "tests/ref\\start0000.pbs"])
        self.assertTrue(os.path.isfile("./tests/ref/start0000.pbs"))
        with open("./tests/ref/start0000.pbs", "r", encoding="utf8") as f:
            x = f.read()
        self.assertEqual(
            x, '#SBATCH --time=00:01:40\n#SBATCH --cpus-per-task=1\n#SBATCH --partition=all\n\njobs="job.sh"'
        )
        os.remove("./tests/ref/start0000.pbs")

    def test_next(self):
        """
        Test next method.
        """
        with mock.patch("benchmarktool.runscript.runscript.PbsScriptGen.PbsScript.next"):
            ps = runscript.PbsScriptGen.PbsScript(self.runspec, self.path, self.queue)
        ps.startscripts = "test"
        ps.num = 2
        ps.time = 10
        with mock.patch("benchmarktool.runscript.runscript.PbsScriptGen.PbsScript.write") as write:
            ps.next()
            write.assert_called_once()
        self.assertEqual(ps.startscripts, "")
        self.assertEqual(ps.num, 0)
        self.assertEqual(ps.time, 0)

    def test_append(self):
        """
        Test append method.
        """
        with mock.patch("benchmarktool.runscript.runscript.PbsScriptGen.PbsScript.next"):
            ps = runscript.PbsScriptGen.PbsScript(self.runspec, self.path, self.queue)
        self.assertEqual(ps.num, 0)
        self.assertEqual(ps.startscripts, "")
        ps.append("new")
        self.assertEqual(ps.num, 1)
        self.assertEqual(ps.startscripts, "new\n")


class TestPbsScriptGen(TestScriptGen):
    """
    Test cases for PbsScriptGen class.
    """
    def setUp(self):
        self.job = mock.Mock(spec=runscript.PbsJob)
        self.sg = runscript.PbsScriptGen(self.job)

    def test_gen_start_script(self):
        """
        Test gen_start_script method.
        """
        self.setup_obj()
        self.runspec.setting.ppn = 1
        self.runspec.setting.procs = 2
        self.runspec.setting.pbstemplate = "tests/ref/test_pbstemplate.pbs"
        self.runspec.project.job.walltime = 20
        self.runspec.project.job.cpt = 4
        self.runspec.project.job.partition = "all"

        self.sg.startfiles = [(self.runspec, "tests/ref", "s1.sh"), (self.runspec, "tests/ref", "s2.sh")]
        self.job.script_mode = "multi"
        with (
            mock.patch("benchmarktool.tools.mkdir_p") as mkdir,
            mock.patch("benchmarktool.tools.set_executable") as set_exec,
        ):
            p = "tests/ref"
            self.sg.gen_start_script("tests/ref")
            mkdir.assert_called_once_with(p)
            set_exec.assert_called_once_with(os.path.join(p, "start.sh"))

        self.assertTrue(os.path.isfile("./tests/ref/start.sh"))
        with open("./tests/ref/start.sh", "r", encoding="utf8") as f:
            x = f.read()
        self.assertEqual(
            x, '#!/bin/bash\n\ncd "$(dirname $0)"\nsbatch "start0000.pbs"\nsbatch "start0001.pbs"'
        )
        os.remove("./tests/ref/start.sh")
        self.assertTrue(os.path.isfile("./tests/ref/start0000.pbs"))
        os.remove("./tests/ref/start0000.pbs")
        self.assertTrue(os.path.isfile("./tests/ref/start0001.pbs"))
        os.remove("./tests/ref/start0001.pbs")

        self.job.script_mode = "timeout"
        with (
            mock.patch("benchmarktool.tools.mkdir_p") as mkdir,
            mock.patch("benchmarktool.tools.set_executable") as set_exec,
        ):
            p = "tests/ref"
            self.sg.gen_start_script("tests/ref")
            mkdir.assert_called_once_with(p)
            set_exec.assert_called_once_with(os.path.join(p, "start.sh"))

        self.assertTrue(os.path.isfile("./tests/ref/start.sh"))
        with open("./tests/ref/start.sh", "r", encoding="utf8") as f:
            x = f.read()
        self.assertEqual(
            x, '#!/bin/bash\n\ncd "$(dirname $0)"\nsbatch "start0000.pbs"\nsbatch "start0001.pbs"'
        )
        os.remove("./tests/ref/start.sh")
        self.assertTrue(os.path.isfile("./tests/ref/start0000.pbs"))
        os.remove("./tests/ref/start0000.pbs")
        self.assertTrue(os.path.isfile("./tests/ref/start0001.pbs"))
        os.remove("./tests/ref/start0001.pbs")

class TestConfig(TestCase):
    """
    Test cases for Config class.
    """
    def setUp(self):
        self.name = "config"
        self.template = "template"
        self.c = runscript.Config(self.name, self.template)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.c.name, self.name)
        self.assertEqual(self.c.template, self.template)
    
    def test_to_xml(self):
        """
        Test to_xml method.
        """
        o = io.StringIO()
        self.c.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<config name="config" template="template"/>\n',
        )

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.c), hash(self.c.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        c2 = runscript.Config("config2", "template")
        self.assertEqual(self.c.__cmp__(self.c), 0)
        self.assertNotEqual(self.c.__cmp__(c2), 0)


class TestClass(TestCase):
    """
    Test cases for Benchmark.Class class.
    """
    def setUp(self):
        self.name = "name"
        self.c = runscript.Benchmark.Class(self.name)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.c.name, self.name)
        self.assertIsNone(self.c.id)

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.c), hash(self.c.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        c2 = runscript.Benchmark.Class("name2")
        self.assertEqual(self.c.__cmp__(self.c), 0)
        self.assertNotEqual(self.c.__cmp__(c2), 0)

class TestInstance(TestCase):
    """
    Test cases for Benchmark.Instance class.
    """
    def setUp(self):
        self.location = "loc/ation"
        self.benchclass = mock.Mock(spec=runscript.Benchmark.Class)
        self.benchclass.name = "bench_name"
        self.name = "inst_name"
        self.encodings = {"encoding"}
        self.ins = runscript.Benchmark.Instance(self.location, self.benchclass, self.name, self.encodings)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.ins.location, self.location)
        self.assertEqual(self.ins.benchclass, self.benchclass)
        self.assertEqual(self.ins.name, self.name)
        self.assertIsNone(self.ins.id)
        self.assertSetEqual(self.ins.encodings, self.encodings)
    
    def test_to_xml(self):
        """
        Test to_xml method.
        """
        o = io.StringIO()
        self.ins.id = 2
        self.ins.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<instance name="inst_name" id="2"/>\n',
        )

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.ins), hash(self.ins.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        ins2 = runscript.Benchmark.Instance(self.location, self.benchclass, "name2", self.encodings)
        self.assertEqual(self.ins.__cmp__(self.ins), 0)
        self.assertNotEqual(self.ins.__cmp__(ins2), 0)

    def test_path(self):
        """
        Test path method.
        """
        self.assertTrue(self.ins.path() in ["loc/ation/bench_name/inst_name", "loc/ation\\bench_name\\inst_name"])

class TestFolder(TestCase):
    """
    Test cases for Benchmark.Folder class.
    """
    def setUp(self):
        self.path = "tests/ref"
        self.f = runscript.Benchmark.Folder(self.path)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.f.path, self.path)
        self.assertSetEqual(self.f.prefixes, set())
        self.assertSetEqual(self.f.encodings, set())
    
    def test_add_ignore(self):
        """
        Test add_ignore method.
        """
        prefix = "prefix"
        self.f.add_ignore(prefix)
        self.assertSetEqual(self.f.prefixes, {prefix})

    def test_add_encoding(self):
        """
        Test add_encoding method.
        """
        encoding = "encoding"
        self.f.add_encoding(encoding)
        self.assertSetEqual(self.f.encodings, {encoding})
    
    def test_skip(self):
        """
        Test _skip method.
        """
        self.assertTrue(self.f._skip("root", ".svn"))
        self.assertFalse(self.f._skip("root", "test"))
        self.f.add_ignore("root/test")
        self.assertTrue(self.f._skip("root", "test"))

    def test_init_m(self):
        """
        Test init method.
        """
        benchmark = runscript.Benchmark("bench")
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.add_instance") as add_inst:
            self.f.init(benchmark)
            self.assertEqual(add_inst.call_count, 7)

        self.f.add_ignore("test_bench")
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.add_instance") as add_inst:
            self.f.init(benchmark)
            self.assertEqual(add_inst.call_count, 5)
        
        self.f.add_ignore("README.md")
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.add_instance") as add_inst:
            self.f.init(benchmark)
            self.assertEqual(add_inst.call_count, 4)
    
class TestFiles(TestCase):
    """
    Test cases for Benchmark.Files class.
    """
    def setUp(self):
        self.path = "tests/ref"
        self.f = runscript.Benchmark.Files(self.path)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.f.path, self.path)
        self.assertSetEqual(self.f.files, set())
        self.assertSetEqual(self.f.encodings, set())
    
    def test_add_file(self):
        """
        Test add_file method.
        """
        file = "file.txt"
        self.f.add_file(file)
        self.assertSetEqual(self.f.files, {file})

    def test_add_encoding(self):
        """
        Test add_encoding method.
        """
        encoding = "encoding"
        self.f.add_encoding(encoding)
        self.assertSetEqual(self.f.encodings, {encoding})
    
    def test_init_m(self):
        """
        Test init method.
        """
        benchmark = runscript.Benchmark("bench")
        self.f.add_file("doesnt.exist")
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.add_instance") as add_inst:
            self.f.init(benchmark)
            self.assertEqual(add_inst.call_count, 0)
        
        self.f.add_file("test_bench/test_f1.lp")
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.add_instance") as add_inst:
            self.f.init(benchmark)
            self.assertEqual(add_inst.call_count, 1)

class TestBenchmark(TestCase):
    """
    Test cases for Benchmark class.
    """
    def setUp(self):
        self.name = "name"
        self.b = runscript.Benchmark(self.name)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.b.name, self.name)
        self.assertListEqual(self.b.elements, [])
        self.assertDictEqual(self.b.instances, {})
        self.assertFalse(self.b.initialized)
    
    def test_add_element(self):
        """
        Test add_element method.
        """
        self.assertListEqual(self.b.elements, [])
        f = runscript.Benchmark.Folder("path")
        self.b.add_element(f)
        self.assertListEqual(self.b.elements, [f])
    
    def test_add_instance(self):
        """
        Test add_instance method.
        """
        self.assertDictEqual(self.b.instances, {})
        root = "root"
        encodings = set()
        self.b.add_instance(root, "class1", "inst1", encodings)
        self.b.add_instance(root, "class1", "inst2", encodings)
        self.b.add_instance(root, "class2", "inst1", encodings)
        for key, val in self.b.instances.items():
            self.assertIsInstance(key, runscript.Benchmark.Class)
            self.assertIsInstance(val, set)
            for i in val:
                self.assertEqual(key, i.benchclass)
        
    def test_init_m(self):
        """"
        Test init method.
        """
        self.assertFalse(self.b.initialized)
        self.b.add_element(runscript.Benchmark.Folder("path"))
        class1 = runscript.Benchmark.Class("class1")
        class2 = runscript.Benchmark.Class("class2")
        inst1 = runscript.Benchmark.Instance("loc", class1, "inst1", set())
        inst2 = runscript.Benchmark.Instance("loc", class1, "inst2", set())
        inst3 = runscript.Benchmark.Instance("loc", class2, "inst3", set())
        self.b.instances = {class1: {inst1, inst2}, class2: {inst3}}
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.Folder.init") as folder_init:
            self.b.init()
            folder_init.assert_called_once()
        self.assertEqual(class1.id, 0)
        self.assertEqual(class2.id, 1)
        self.assertEqual(inst1.id, 0)
        self.assertEqual(inst2.id, 1)
        self.assertEqual(inst3.id, 0)
        self.assertTrue(self.b.initialized)

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        o = io.StringIO()
        bclass = runscript.Benchmark.Class("class")
        bclass.id = 0
        inst = runscript.Benchmark.Instance("loc", bclass, "inst", set())
        self.b.instances = {bclass: {inst}}
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.Instance.to_xml"):
            self.b.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<benchmark name="name">\n\t\t<class name="class" id="0">\n\t\t</class>\n\t</benchmark>\n',
        )

    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.b), hash(self.b.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        b2 = runscript.Benchmark("name2")
        self.assertEqual(self.b.__cmp__(self.b), 0)
        self.assertNotEqual(self.b.__cmp__(b2), 0)


class TestRunspec(TestCase):
    """
    Test cases for Runspec class.
    """
    def setUp(self):
        self.machine = mock.Mock(spec=runscript.Machine)
        self.machine.name = "machine"
        self.setting = mock.Mock(spec=runscript.Setting)
        self.setting.name = "setting"
        self.setting.system = mock.Mock(spec=runscript.System)
        self.setting.system.name = "sys"
        self.setting.system.version = "version"
        self.benchmark = mock.Mock(spec=runscript.Benchmark)
        self.benchmark.name = "bench"
        self.rs = runscript.Runspec(self.machine, self.setting, self.benchmark)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.rs.machine, self.machine)
        self.assertEqual(self.rs.setting, self.setting)
        self.assertEqual(self.rs.benchmark, self.benchmark)
        self.assertIsNone(self.rs.project)
    
    def test_path(self):
        """
        Test path method.
        """
        self.rs.project = mock.Mock(spec=runscript.Project)
        self.rs.project.path = mock.Mock(return_value="project_path")
        self.assertTrue(self.rs.path() in ["project_path/machine/results/bench/sys-version-setting", "project_path\\machine\\results\\bench\\sys-version-setting"])
    
    def test_gen_script(self):
        """
        Test gen_script method.
        """
        bclass = runscript.Benchmark.Class("class")
        inst = runscript.Benchmark.Instance("loc", bclass, "inst", set())
        self.rs.benchmark.instances = {bclass: {inst}}
        self.rs.benchmark.init = mock.Mock()
        script_gen = mock.Mock(spec=runscript.ScriptGen)
        script_gen.add_to_script = mock.Mock()
        self.rs.gen_scripts(script_gen)
        self.rs.benchmark.init.assert_called_once()
        script_gen.add_to_script.assert_called_once_with(self.rs, inst)
    
    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        self.rs.machine = runscript.Machine("machine", "", "")
        self.rs.setting = runscript.Setting("setting", "", set(), 0, None, None, "", {})
        self.rs.setting.system = runscript.System("sys", "version", "", 0)
        self.rs.benchmark = runscript.Benchmark("bench")
        rs2 = runscript.Runspec(self.rs.machine,  self.rs.setting, runscript.Benchmark("bench2"))
        self.assertEqual(self.rs.__cmp__(self.rs), 0)
        self.assertNotEqual(self.rs.__cmp__(rs2), 0)
    
class TestProject(TestCase):
    """
    Test cases for Project class.
    """
    def setUp(self):
        self.name = "name"
        self.prj = runscript.Project(self.name)
    
    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.prj.name, self.name)
        self.assertDictEqual(self.prj.runspecs, {})
        self.assertIsNone(self.prj.runscript)
        self.assertIsNone(self.prj.job)
    
    def test_add_runtag(self):
        """
        Test add_runtag method.
        """
        setting = mock.Mock(spec=runscript.Setting)
        setting.name = "setting"
        setting.tag = {"tag"}
        sys = mock.Mock(spec=runscript.System)
        sys.name = "sys"
        sys.version = "ver"
        sys.settings = {"setting": setting}
        rs = mock.Mock(spec=runscript.Runscript)
        rs.systems = {("sys", "ver"): sys}
        self.prj.runscript = rs
        m_name = "machine"
        b_name = "bench"

        with mock.patch("benchmarktool.runscript.runscript.Project.add_runspec") as add_runspec:
            self.prj.add_runtag(m_name, b_name, "tag2")
            add_runspec.assert_not_called()
            self.prj.add_runtag(m_name, b_name, "tag")
            add_runspec.assert_called_once_with(m_name, sys.name, sys.version, setting.name, b_name)
    
    def test_add_runspec(self):
        """
        Test add_runspec method.
        """
        machine = mock.Mock(spec=runscript.Machine)
        setting = mock.Mock(spec=runscript.Setting)
        sys = mock.Mock(spec=runscript.System)
        sys.settings = {"setting": setting}
        setting.system = sys
        bench = mock.Mock(spec=runscript.Benchmark)
        rs = mock.Mock(spec=runscript.Runscript)
        rs.machines = {"machine": machine}
        rs.systems = {("sys", "ver"): sys}
        rs.benchmarks = {"bench": bench}
        self.prj.runscript = rs
        m_name = "machine"

        self.assertDictEqual(self.prj.runspecs, {})
        self.prj.add_runspec(m_name, "sys", "ver", "setting", "bench")
        self.assertTrue(m_name in self.prj.runspecs)
        self.assertTrue(len(self.prj.runspecs[m_name]), 1)
        self.assertIsInstance(self.prj.runspecs[m_name][0], runscript.Runspec)
        self.assertEqual(self.prj.runspecs[m_name][0].machine, machine)
        self.assertEqual(self.prj.runspecs[m_name][0].setting, setting)
        self.assertEqual(self.prj.runspecs[m_name][0].benchmark, bench)
        self.assertEqual(self.prj.runspecs[m_name][0].project, self.prj)
    
    def test_path(self):
        """
        Test path method.
        """
        rs = mock.Mock(spec=runscript.Runscript)
        rs.path = mock.Mock(return_value="rs_path")
        self.prj.runscript = rs
        self.assertTrue(self.prj.path() in ["rs_path/name", "rs_path\\name"])
    
    def test_gen_script(self):
        """
        Test gen_script method.
        """
        # SeqJob
        j = runscript.SeqJob("job", 1 , 1, 1, {})
        self.prj.job = j
        rs = mock.Mock(spec=runscript.Runspec)
        rs.gen_scripts = mock.Mock()
        self.prj.runspecs = {"machine": [rs]}
        self.prj.path = mock.Mock(return_value="prj_path")
        with (mock.patch("benchmarktool.runscript.runscript.SeqJob.script_gen", wraps=j.script_gen) as s_gen,
              mock.patch("benchmarktool.runscript.runscript.SeqScriptGen.set_skip") as skip,
              mock.patch("benchmarktool.runscript.runscript.SeqScriptGen.gen_start_script") as gen_start,
        ):
            self.prj.gen_scripts(False)
            s_gen.assert_called_once()
            skip.assert_called_once_with(False)
            rs.gen_scripts.assert_called_once()
            gen_start.assert_called_once_with(os.path.join(self.prj.path(), "machine"))
        
        # PbsJob
        j = runscript.PbsJob("job", 1, 1, "", 1, 1, "", {})
        self.prj.job = j
        rs = mock.Mock(spec=runscript.Runspec)
        rs.gen_scripts = mock.Mock()
        self.prj.runspecs = {"machine": [rs]}
        self.prj.path = mock.Mock(return_value="prj_path")
        with (mock.patch("benchmarktool.runscript.runscript.PbsJob.script_gen", wraps=j.script_gen) as s_gen,
              mock.patch("benchmarktool.runscript.runscript.PbsScriptGen.set_skip") as skip,
              mock.patch("benchmarktool.runscript.runscript.PbsScriptGen.gen_start_script") as gen_start,
        ):
            self.prj.gen_scripts(False)
            s_gen.assert_called_once()
            skip.assert_called_once_with(False)
            rs.gen_scripts.assert_called_once()
            gen_start.assert_called_once_with(os.path.join(self.prj.path(), "machine"))
    
    def test_hash(self):
        """
        Test __hash__ method.
        """
        self.assertEqual(hash(self.prj), hash(self.prj.name))

    def test_cmp(self):
        """
        Test __cmp__ method.
        """
        prj2 = runscript.Project("name2")
        self.assertEqual(self.prj.__cmp__(self.prj), 0)
        self.assertNotEqual(self.prj.__cmp__(prj2), 0)


