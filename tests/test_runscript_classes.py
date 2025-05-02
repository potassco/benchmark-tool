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
        self.runspec.system = mock.Mock(spec=runscript.System)
        self.runspec.system.name = "sys_name"
        self.runspec.system.version = "sys_version"
        self.runspec.system.config = mock.Mock(spec=runscript.Config)
        self.runspec.system.config.template = "tests/ref/test_template.sh"
        self.runspec.system.measures = "result_parser"

        self.sg.job.runs = 1
        self.sg.job.timeout = 10

        self.instance = mock.Mock(spec=runscript.Benchmark.Instance)
        self.instance.instance = "inst_name"
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
            os.path.join(self.runspec.path(), self.instance.benchclass.name, self.instance.instance, "run%d" % 1),
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
    Test cases for PbsScript class.
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
