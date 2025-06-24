"""
Test cases for runscript classes.
"""

import io
import os
from unittest import TestCase, mock

from benchmarktool.runscript import runscript

# pylint: disable=too-many-lines, anomalous-backslash-in-string, protected-access


class TestMachine(TestCase):
    """
    Test cases for Machine class.
    """

    def setUp(self):
        self.name = "name"
        self.cpu = "cpu"
        self.memory = "memory"

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        m = runscript.Machine(self.name, self.cpu, self.memory)
        o = io.StringIO()
        m.to_xml(o, "\t")
        self.assertEqual(o.getvalue(), '\t<machine name="name" cpu="cpu" memory="memory"/>\n')


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

    def test_add_setting(self):
        """
        Test add_setting method.
        """
        s = runscript.System(self.name, self.version, self.measures, self.order, self.config)
        setting = mock.MagicMock(spec=runscript.Setting)
        setting.name = "setting_name"
        self.assertDictEqual(s.settings, {})
        s.add_setting(setting)
        self.assertDictEqual(s.settings, {"setting_name": setting})

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        with mock.patch("benchmarktool.runscript.runscript.Setting", spec=True) as setting_cls:
            settings = [mock.Mock(name="s1", order=0), mock.Mock(name="s2", order=1)]
            setting_cls.side_effect = settings
            s1 = setting_cls()
            s2 = setting_cls()

        o = io.StringIO()
        s = runscript.System(
            self.name, self.version, self.measures, self.order, self.config, {s1.name: s1, s2.name: s2}
        )
        s.to_xml(o, "\t", None)
        s1.to_xml.assert_called_once_with(o, "\t\t")
        s2.to_xml.assert_called_once_with(o, "\t\t")
        self.assertEqual(
            o.getvalue(),
            '\t<system name="name" version="version" measures="clasp" config="config_name">\n\t</system>\n',
        )

        s1.to_xml.reset_mock()
        s2.to_xml.reset_mock()
        s = runscript.System(self.name, self.version, self.measures, self.order, self.config, {s2.name, s2})
        s.to_xml(o, "\t", [s2])
        s1.to_xml.assert_not_called()
        s2.to_xml.assert_called_once_with(o, "\t\t")


# pylint: disable=too-many-instance-attributes
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

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        s = runscript.Setting(
            self.name, self.cmdline, self.tag, self.order, self.procs, self.ppn, self.template, self.attr
        )
        o = io.StringIO()
        s.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<setting name="name" cmdline="cmdline" tag="tag1 tag2" '
            'procs="1" ppn="2" disttemplate="template" key="val">\n'
            "\t</setting>\n",
        )

        s = runscript.Setting(
            self.name,
            self.cmdline,
            self.tag,
            self.order,
            None,
            None,
            self.template,
            {},
            {"_default_": {"def.lp"}, "test": {"test1.lp", "test2.lp"}},
        )
        o = io.StringIO()
        s.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<setting name="name" cmdline="cmdline" tag="tag1 tag2" disttemplate="template">\n'
            '\t\t<encoding file="def.lp"/>\n'
            '\t\t<encoding file="test1.lp" tag="test"/>\n'
            '\t\t<encoding file="test2.lp" tag="test"/>\n'
            "\t</setting>\n",
        )


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

    def test_to_xml(self):
        """
        Test _to_xml method.
        """
        self.j = runscript.Job(self.name, self.timeout, self.runs, self.attr)
        o = io.StringIO()
        tag = "tag"
        extra = " extra"
        self.j._to_xml(o, "\t", tag, extra)
        self.assertEqual(
            o.getvalue(),
            '\t<tag name="name" timeout="20" runs="2" extra key="val"/>\n',
        )

    def test_script_gen(self):
        """
        Test script_gen stub.
        """
        self.assertRaises(NotImplementedError, self.j.script_gen)


class TestSeqJob(TestJob):
    """
    Test cases for SeqJob class.
    """

    def setUp(self):
        self.name = "name"
        self.timeout = 20
        self.runs = 2
        self.parallel = 4
        self.attr = {"key": "val"}
        self.j = runscript.SeqJob(self.name, self.timeout, self.runs, self.attr, self.parallel)

    def test_to_xml(self):
        """
        Test _to_xml method.
        """
        o = io.StringIO()
        o2 = io.StringIO()
        self.j._to_xml(o, "\t", "seqjob", ' parallel="4"')
        self.j.to_xml(o2, "\t")
        self.assertEqual(o2.getvalue(), o.getvalue())

    def test_script_gen(self):
        """
        Test script_gen method.
        """
        ref = runscript.SeqScriptGen
        with mock.patch("benchmarktool.runscript.runscript.SeqScriptGen", spec=True):
            self.assertIsInstance(self.j.script_gen(), ref)


# pylint: disable=too-many-instance-attributes
class TestDistJob(TestJob):
    """
    Test cases for DistJob class.
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
        self.j = runscript.DistJob(
            self.name, self.timeout, self.runs, self.attr, self.scriptmode, self.walltime, self.cpt, self.partition
        )

    def test_to_xml(self):
        """
        Test _to_xml method.
        """
        o = io.StringIO()
        o2 = io.StringIO()
        self.j._to_xml(o, "\t", "distjob", ' script_mode="mode" walltime="100" cpt="2" partition="all"')
        self.j.to_xml(o2, "\t")
        self.assertEqual(o2.getvalue(), o.getvalue())

    def test_script_gen(self):
        """
        Test script_gen method.
        """
        ref = runscript.DistScriptGen
        with mock.patch("benchmarktool.runscript.runscript.DistScriptGen", spec=True):
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
        self.runspec.setting.encodings = {"_default_": {"def.lp"}, "test": {"test.lp"}}
        self.runspec.system = mock.Mock(spec=runscript.System)
        self.runspec.system.name = "sys_name"
        self.runspec.system.version = "sys_version"
        self.instance = mock.Mock(spec=runscript.Benchmark.Instance)
        self.instance.path.return_value = "inst_path"
        self.instance.encodings = {"encoding.lp"}
        self.instance.enctags = {"test", "none"}
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
        self.assertEqual(self.r.encodings, '"../def.lp" "../encoding.lp" "../test.lp"')
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

        self.runspec: runscript.Runspec
        self.instance: runscript.Benchmark.Instance

    def setup_obj(self):
        """
        Setup helper objects.
        """
        self.runspec = mock.Mock(spec=runscript.Runspec)
        self.runspec.setting = mock.Mock(spec=runscript.Setting)
        self.runspec.setting.cmdline = "cmdline"
        self.runspec.setting.encodings = {}
        self.runspec.path.return_value = "runspec_path"
        self.runspec.project = mock.Mock(spec=runscript.Project)
        self.runspec.project.job = self.job
        self.runspec.system = mock.Mock(spec=runscript.System)
        self.runspec.system.name = "sys_name"
        self.runspec.system.version = "sys_version"
        self.runspec.system.config = mock.Mock(spec=runscript.Config)
        self.runspec.system.config.template = "tests/ref/test_template.sh"
        self.runspec.system.measures = "clasp"

        self.sg.job.runs = 1
        self.sg.job.timeout = 10

        self.instance = mock.Mock(spec=runscript.Benchmark.Instance)
        self.instance.name = "inst_name"
        self.instance.encodings = {"encoding"}
        self.instance.enctags = {}
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
                '$CAT ../../inst_path ../.. 10 ../../programs/sys_name-sys_version cmdline "../../encoding"\n',
                '$CAT ..\..\inst_path ..\.. 10 ..\../programs/sys_name-sys_version cmdline "..\..\encoding"\n',
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
        with mock.patch("benchmarktool.resultparser.clasp.parse", return_value=[("time", "int", 5)], create=True):
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


class TestDistScript(TestCase):
    """
    Test cases for DistScriptGen.DistScript class.
    """

    def setUp(self):
        self.runspec = mock.Mock(spec=runscript.Runspec)
        self.path = "tests/ref"
        self.queue = []

    def test_init(self):
        """
        Test class initialization.
        """
        with mock.patch("benchmarktool.runscript.runscript.DistScriptGen.DistScript.next") as next_m:
            ps = runscript.DistScriptGen.DistScript(self.runspec, self.path, self.queue)
            next_m.assert_called_once()
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
        with mock.patch("benchmarktool.runscript.runscript.DistScriptGen.DistScript.next"):
            ps = runscript.DistScriptGen.DistScript(self.runspec, self.path, self.queue)
        ps.startscripts = "job.sh"
        ps.num = 1
        ps.runspec.setting = mock.Mock(spec=runscript.Setting)
        ps.runspec.setting.disttemplate = "tests/ref/test_disttemplate.dist"
        ps.runspec.setting.procs = 4
        ps.runspec.setting.ppn = 2

        ps.runspec.project = mock.Mock(spec=runscript.Project)
        ps.runspec.project.job = mock.Mock(spec=runscript.DistJob)
        ps.runspec.project.job.walltime = 100
        ps.runspec.project.job.cpt = 1
        ps.runspec.project.job.partition = "all"
        ps.write()

        self.assertTrue(ps.queue[0] in ["tests/ref/start0000.dist", "tests/ref\\start0000.dist"])
        self.assertTrue(os.path.isfile("./tests/ref/start0000.dist"))
        with open("./tests/ref/start0000.dist", "r", encoding="utf8") as f:
            x = f.read()
        self.assertEqual(
            x, '#SBATCH --time=00:01:40\n#SBATCH --cpus-per-task=1\n#SBATCH --partition=all\n\njobs="job.sh"\n'
        )
        os.remove("./tests/ref/start0000.dist")

    def test_next(self):
        """
        Test next method.
        """
        with mock.patch("benchmarktool.runscript.runscript.DistScriptGen.DistScript.next"):
            ps = runscript.DistScriptGen.DistScript(self.runspec, self.path, self.queue)
        ps.startscripts = "test"
        ps.num = 2
        ps.time = 10
        with mock.patch("benchmarktool.runscript.runscript.DistScriptGen.DistScript.write") as write:
            ps.next()
            write.assert_called_once()
        self.assertEqual(ps.startscripts, "")
        self.assertEqual(ps.num, 0)
        self.assertEqual(ps.time, 0)

    def test_append(self):
        """
        Test append method.
        """
        with mock.patch("benchmarktool.runscript.runscript.DistScriptGen.DistScript.next"):
            ps = runscript.DistScriptGen.DistScript(self.runspec, self.path, self.queue)
        self.assertEqual(ps.num, 0)
        self.assertEqual(ps.startscripts, "")
        ps.append("new")
        self.assertEqual(ps.num, 1)
        self.assertEqual(ps.startscripts, "new\n")


class TestDistScriptGen(TestScriptGen):
    """
    Test cases for DistScriptGen class.
    """

    def setUp(self):
        self.job = mock.Mock(spec=runscript.DistJob)
        self.sg = runscript.DistScriptGen(self.job)

    def test_gen_start_script(self):
        """
        Test gen_start_script method.
        """
        self.setup_obj()
        self.runspec.setting.ppn = 1
        self.runspec.setting.procs = 2
        self.runspec.setting.disttemplate = "tests/ref/test_disttemplate.dist"
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
        self.assertEqual(x, '#!/bin/bash\n\ncd "$(dirname $0)"\nsbatch "start0000.dist"\nsbatch "start0001.dist"')
        os.remove("./tests/ref/start.sh")
        self.assertTrue(os.path.isfile("./tests/ref/start0000.dist"))
        os.remove("./tests/ref/start0000.dist")
        self.assertTrue(os.path.isfile("./tests/ref/start0001.dist"))
        os.remove("./tests/ref/start0001.dist")

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
        self.assertEqual(x, '#!/bin/bash\n\ncd "$(dirname $0)"\nsbatch "start0000.dist"\nsbatch "start0001.dist"')
        os.remove("./tests/ref/start.sh")
        self.assertTrue(os.path.isfile("./tests/ref/start0000.dist"))
        os.remove("./tests/ref/start0000.dist")
        self.assertTrue(os.path.isfile("./tests/ref/start0001.dist"))
        os.remove("./tests/ref/start0001.dist")


class TestConfig(TestCase):
    """
    Test cases for Config class.
    """

    def setUp(self):
        self.name = "config"
        self.template = "template"

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        c = runscript.Config(self.name, self.template)
        o = io.StringIO()
        c.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<config name="config" template="template"/>\n',
        )


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
        self.enctags = set()
        self.ins = runscript.Benchmark.Instance(self.location, self.benchclass, self.name, self.encodings, self.enctags)

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        o = io.StringIO()
        ins = runscript.Benchmark.Instance(self.location, self.benchclass, self.name, self.encodings, self.enctags, 2)
        ins.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<instance name="inst_name" id="2"/>\n',
        )

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
        self.path = "tests/ref/test_bench"
        self.f = runscript.Benchmark.Folder(self.path)

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.f.path, self.path)
        self.assertSetEqual(self.f.prefixes, set())
        self.assertSetEqual(self.f.encodings, set())
        self.assertSetEqual(self.f.enctags, set())

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

    def test_add_enctags(self):
        """
        Test add_enctags method.
        """
        tags = {"tag1", "tag2"}
        self.f.add_enctags(tags)
        self.assertSetEqual(self.f.enctags, tags)

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
            self.assertEqual(add_inst.call_count, 3)

        self.f.add_ignore("test_folder")
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.add_instance") as add_inst:
            self.f.init(benchmark)
            self.assertEqual(add_inst.call_count, 2)

        self.f.add_ignore("test_f2.lp")
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.add_instance") as add_inst:
            self.f.init(benchmark)
            self.assertEqual(add_inst.call_count, 1)


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
        self.assertSetEqual(self.f.enctags, set())

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

    def test_add_enctags(self):
        """
        Test add_enctags method.
        """
        tags = {"tag1", "tag2"}
        self.f.add_enctags(tags)
        self.assertSetEqual(self.f.enctags, tags)

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
        enctags = set()
        self.b.add_instance(root, "class1", "inst1", encodings, enctags)
        self.b.add_instance(root, "class1", "inst2", encodings, enctags)
        self.b.add_instance(root, "class2", "inst1", encodings, enctags)
        for key, val in self.b.instances.items():
            self.assertIsInstance(key, runscript.Benchmark.Class)
            self.assertIsInstance(val, set)
            for i in val:
                self.assertEqual(key, i.benchclass)

    def test_init(self):
        """
        Test init method.
        """
        self.assertFalse(self.b.initialized)
        self.b.add_element(runscript.Benchmark.Folder("path"))
        class1 = runscript.Benchmark.Class("class1")
        class2 = runscript.Benchmark.Class("class2")
        inst1 = runscript.Benchmark.Instance("loc", class1, "inst1", set(), set())
        inst2 = runscript.Benchmark.Instance("loc", class1, "inst2", set(), set())
        inst3 = runscript.Benchmark.Instance("loc", class2, "inst3", set(), set())
        self.b.instances = {class1: {inst1, inst2}, class2: {inst3}}
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.Folder.init") as folder_init:
            self.b.init()
            folder_init.assert_called_once()
        self.assertEqual(len(self.b.instances), 2)
        for bcl, ins_set in self.b.instances.items():
            if bcl.name == "class1":
                self.assertEqual(bcl.id, 0)
                self.assertEqual(len(ins_set), 2)
                ins_list = sorted(ins_set)
                self.assertEqual(ins_list[0].id, 0)
                self.assertEqual(ins_list[1].id, 1)
            elif bcl.name == "class2":
                self.assertEqual(bcl.id, 1)
                self.assertEqual(len(ins_set), 1)
                ins_list = sorted(ins_set)
                self.assertEqual(ins_list[0].id, 0)
            else:
                self.fail("Error in init method.")  # nocoverage
        self.assertTrue(self.b.initialized)

    def test_to_xml(self):
        """
        Test to_xml method.
        """
        o = io.StringIO()
        bclass = runscript.Benchmark.Class("class", 0)
        inst = runscript.Benchmark.Instance("loc", bclass, "inst", set(), set())
        self.b = runscript.Benchmark(self.name, [], {bclass: {inst}})
        with mock.patch("benchmarktool.runscript.runscript.Benchmark.Instance.to_xml"):
            self.b.to_xml(o, "\t")
        self.assertEqual(
            o.getvalue(),
            '\t<benchmark name="name">\n\t\t<class name="class" id="0">\n\t\t</class>\n\t</benchmark>\n',
        )


class TestRunspec(TestCase):
    """
    Test cases for Runspec class.
    """

    def setUp(self):
        self.machine = mock.Mock(spec=runscript.Machine)
        self.machine.name = "machine"
        self.setting = mock.Mock(spec=runscript.Setting)
        self.setting.name = "setting"
        self.system = mock.Mock(spec=runscript.System)
        self.system.name = "sys"
        self.system.version = "version"
        self.benchmark = mock.Mock(spec=runscript.Benchmark)
        self.benchmark.name = "bench"
        self.project = mock.Mock(spec=runscript.Project)
        self.project.name = "project"
        self.rs = runscript.Runspec(self.machine, self.system, self.setting, self.benchmark, self.project)

    def test_path(self):
        """
        Test path method.
        """
        self.rs.project.path = mock.Mock(return_value="project_path")
        self.assertTrue(
            self.rs.path()
            in [
                "project_path/machine/results/bench/sys-version-setting",
                "project_path\\machine\\results\\bench\\sys-version-setting",
            ]
        )

    def test_gen_script(self):
        """
        Test gen_script method.
        """
        bclass = runscript.Benchmark.Class("class")
        inst = runscript.Benchmark.Instance("loc", bclass, "inst", set(), set())
        self.rs.benchmark.instances = {bclass: {inst}}
        self.rs.benchmark.init = mock.Mock()
        script_gen = mock.Mock(spec=runscript.ScriptGen)
        script_gen.add_to_script = mock.Mock()
        self.rs.gen_scripts(script_gen)
        self.rs.benchmark.init.assert_called_once()
        script_gen.add_to_script.assert_called_once_with(self.rs, inst)


class TestProject(TestCase):
    """
    Test cases for Project class.
    """

    def setUp(self):
        self.name = "name"
        self.setting = mock.Mock(spec=runscript.Setting)
        self.setting.name = "setting"
        self.setting.tag = {"tag"}
        self.sys = mock.Mock(spec=runscript.System)
        self.sys.name = "sys"
        self.sys.version = "ver"
        self.sys.settings = {"setting": self.setting}
        self.job = runscript.SeqJob("job", 1, 1, {}, 1)

    def test_add_runtag(self):
        """
        Test add_runtag method.
        """
        rs = mock.Mock(spec=runscript.Runscript)
        rs.systems = {("sys", "ver"): self.sys}
        prj = runscript.Project(self.name, rs, self.job)
        m_name = "machine"
        b_name = "bench"

        with mock.patch("benchmarktool.runscript.runscript.Project.add_runspec") as add_runspec:
            prj.add_runtag(m_name, b_name, "tag2")
            add_runspec.assert_not_called()
            prj.add_runtag(m_name, b_name, "tag")
            add_runspec.assert_called_once_with(m_name, self.sys.name, self.sys.version, self.setting.name, b_name)

    def test_add_runspec(self):
        """
        Test add_runspec method.
        """
        machine = mock.Mock(spec=runscript.Machine)
        bench = mock.Mock(spec=runscript.Benchmark)
        rs = mock.Mock(spec=runscript.Runscript)
        rs.machines = {"machine": machine}
        rs.systems = {("sys", "ver"): self.sys}
        rs.benchmarks = {"bench": bench}
        prj = runscript.Project(self.name, rs, self.job)
        m_name = "machine"

        self.assertDictEqual(prj.runspecs, {})
        prj.add_runspec(m_name, "sys", "ver", "setting", "bench")
        self.assertTrue(m_name in prj.runspecs)
        self.assertTrue(len(prj.runspecs[m_name]), 1)
        self.assertIsInstance(prj.runspecs[m_name][0], runscript.Runspec)
        self.assertEqual(prj.runspecs[m_name][0].machine, machine)
        self.assertEqual(prj.runspecs[m_name][0].setting, self.setting)
        self.assertEqual(prj.runspecs[m_name][0].benchmark, bench)
        self.assertEqual(prj.runspecs[m_name][0].project, prj)

    def test_path(self):
        """
        Test path method.
        """
        rs = mock.Mock(spec=runscript.Runscript)
        rs.path = mock.Mock(return_value="rs_path")
        prj = runscript.Project(self.name, rs, self.job)
        self.assertTrue(prj.path() in ["rs_path/name", "rs_path\\name"])

    def test_gen_script(self):
        """
        Test gen_script method.
        """
        # SeqJob
        j = runscript.SeqJob("job", 1, 1, {}, 1)
        rs = mock.Mock(spec=runscript.Runspec)
        rs.gen_scripts = mock.Mock()
        prj = runscript.Project(self.name, rs, j, {"machine": [rs]})
        with (
            mock.patch("benchmarktool.runscript.runscript.SeqJob.script_gen", wraps=j.script_gen) as s_gen,
            mock.patch("benchmarktool.runscript.runscript.SeqScriptGen.set_skip") as skip,
            mock.patch("benchmarktool.runscript.runscript.SeqScriptGen.gen_start_script") as gen_start,
            mock.patch("benchmarktool.runscript.runscript.Project.path", return_value="prj_path"),
        ):
            prj.gen_scripts(False)
            s_gen.assert_called_once()
            skip.assert_called_once_with(False)
            rs.gen_scripts.assert_called_once()
            gen_start.assert_called_once_with(os.path.join(prj.path(), "machine"))

        # DistJob
        j = runscript.DistJob("job", 1, 1, {}, "", 1, 1, "")
        rs = mock.Mock(spec=runscript.Runspec)
        rs.gen_scripts = mock.Mock()
        prj = runscript.Project(self.name, rs, j, {"machine": [rs]})
        with (
            mock.patch("benchmarktool.runscript.runscript.DistJob.script_gen", wraps=j.script_gen) as s_gen,
            mock.patch("benchmarktool.runscript.runscript.DistScriptGen.set_skip") as skip,
            mock.patch("benchmarktool.runscript.runscript.DistScriptGen.gen_start_script") as gen_start,
            mock.patch("benchmarktool.runscript.runscript.Project.path", return_value="prj_path"),
        ):
            prj.gen_scripts(False)
            s_gen.assert_called_once()
            skip.assert_called_once_with(False)
            rs.gen_scripts.assert_called_once()
            gen_start.assert_called_once_with(os.path.join(prj.path(), "machine"))


class TestRunscript(TestCase):
    """
    Test cases for Runscript class.
    """

    def setUp(self):
        self.o = io.StringIO()
        self.rs = runscript.Runscript(self.o)

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.rs.output, self.o)
        self.assertDictEqual(self.rs.jobs, {})
        self.assertDictEqual(self.rs.projects, {})
        self.assertDictEqual(self.rs.machines, {})
        self.assertDictEqual(self.rs.systems, {})
        self.assertDictEqual(self.rs.configs, {})
        self.assertDictEqual(self.rs.benchmarks, {})

    def test_add_machine(self):
        """
        Test add_machine method.
        """
        self.assertDictEqual(self.rs.machines, {})
        m = mock.Mock(spec=runscript.Machine)
        m.name = "machine"
        self.rs.add_machine(m)
        self.assertDictEqual(self.rs.machines, {"machine": m})

    def test_add_system(self):
        """
        Test add_system method.
        """
        self.assertDictEqual(self.rs.systems, {})
        s = mock.Mock(spec=runscript.System)
        s.name = "sys"
        s.version = "ver"
        self.rs.add_system(s)
        self.assertDictEqual(self.rs.systems, {("sys", "ver"): s})

    def test_add_config(self):
        """
        Test add_config method.
        """
        self.assertDictEqual(self.rs.configs, {})
        c = mock.Mock(spec=runscript.Config)
        c.name = "config"
        self.rs.add_config(c)
        self.assertDictEqual(self.rs.configs, {"config": c})

    def test_add_benchmark(self):
        """
        Test add_benchmark method.
        """
        self.assertDictEqual(self.rs.benchmarks, {})
        b = mock.Mock(spec=runscript.Benchmark)
        b.name = "bench"
        self.rs.add_benchmark(b)
        self.assertDictEqual(self.rs.benchmarks, {"bench": b})

    def test_add_job(self):
        """
        test add_job method.
        """
        self.assertDictEqual(self.rs.jobs, {})
        j = mock.Mock(spec=runscript.Job)
        j.name = "job"
        self.rs.add_job(j)
        self.assertDictEqual(self.rs.jobs, {"job": j})

    def test_add_project(self):
        """
        Test add_project method.
        """
        self.assertDictEqual(self.rs.projects, {})
        p = mock.Mock(spec=runscript.Project)
        p.name = "project"
        self.rs.add_project(p)
        self.assertDictEqual(self.rs.projects, {"project": p})

    def test_gen_script(self):
        """
        Test gen_script method.
        """
        p = mock.Mock(spec=runscript.Project)
        p.gen_scripts = mock.Mock()
        self.rs.projects["prj"] = p
        skip = True
        self.rs.gen_scripts(skip)
        p.gen_scripts.assert_called_once_with(skip)

    def test_path(self):
        """
        Test path method.
        """
        self.assertEqual(self.rs.path(), self.o)

    def test_eval_results(self):
        """
        Test eval_results method.
        """

        def temp_to_xml(s: str):
            return lambda o, i, sys=None: o.write(f"{i}{s}\n")

        job = mock.Mock(spec=runscript.SeqJob)
        job.name = "job"
        job.order = 0
        job.to_xml = mock.Mock(side_effect=temp_to_xml("job_xml"))
        job.script_gen = mock.Mock(return_value=runscript.SeqScriptGen(job))

        config = mock.Mock(spec=runscript.Config)
        config.order = 0
        config.to_xml = mock.Mock(side_effect=temp_to_xml("config_xml"))

        sys = mock.Mock(spec=runscript.System)
        sys.config = config
        sys.name = "sys"
        sys.version = "ver"
        sys.order = 0
        sys.to_xml = mock.Mock(side_effect=temp_to_xml("sys_xml"))

        machine = mock.Mock(spec=runscript.Machine)
        machine.name = "machine"
        machine.order = 0
        machine.to_xml = mock.Mock(side_effect=temp_to_xml("machine_xml"))

        setting = mock.Mock(spec=runscript.Setting)
        setting.name = "setting"

        bclass = mock.Mock(spec=runscript.Benchmark.Class)
        bclass.id = 0
        inst = mock.Mock(spec=runscript.Benchmark.Instance)
        inst.id = 0

        bench = mock.Mock(runscript.Benchmark)
        bench.name = "bench"
        bench.instances = {bclass: {inst}}
        bench.to_xml = mock.Mock(side_effect=temp_to_xml("bench_xml"))

        runspec = mock.Mock(spec=runscript.Runspec)
        runspec.system = sys
        runspec.machine = machine
        runspec.setting = setting
        runspec.benchmark = bench

        prj = mock.Mock(spec=runscript.Project)
        prj.job = job
        prj.runspecs = {"machine": [runspec]}
        prj.name = "prj"

        self.rs.projects["prj"] = prj

        with mock.patch("benchmarktool.runscript.runscript.SeqScriptGen.eval_results") as sg_eval:
            self.rs.eval_results(self.o)
            sg_eval.assert_called_once_with(self.o, "\t\t\t\t\t", runspec, inst)
        self.assertEqual(
            self.o.getvalue(),
            "<result>\n"
            "\tmachine_xml\n"
            "\tconfig_xml\n"
            "\tsys_xml\n"
            "\tjob_xml\n"
            "\tbench_xml\n"
            '\t<project name="prj" job="job">\n'
            '\t\t<runspec machine="machine" system="sys" version="ver" '
            'benchmark="bench" setting="setting">\n'
            '\t\t\t<class id="0">\n'
            '\t\t\t\t<instance id="0">\n'
            "\t\t\t\t</instance>\n"
            "\t\t\t</class>\n"
            "\t\t</runspec>\n"
            "\t</project>\n"
            "</result>\n",
        )


class TestTagDisj(TestCase):
    """
    Test cases for TagDisj class.
    """

    def setUp(self):
        self.tag = "tag1 tag2 | tag3"
        self.td = runscript.TagDisj(self.tag)

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertListEqual(self.td.tag, [frozenset(["tag1", "tag2"]), frozenset(["tag3"])])
        all_td = runscript.TagDisj("*all*")
        self.assertEqual(all_td.tag, 1)

    def test_match(self):
        """
        Test match method.
        """
        self.assertTrue(self.td.match({"tag3", "tag4"}))
        self.assertFalse(self.td.match({"tag1"}))
        all_td = runscript.TagDisj("*all*")
        self.assertTrue(all_td.match({"test123"}))
