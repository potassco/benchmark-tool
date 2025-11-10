"""
Test cases for result classes.
"""

from dataclasses import FrozenInstanceError
from unittest import TestCase, mock

from benchmarktool.result import ods_gen, result


class TestResult(TestCase):
    """
    Test cases for Result class
    """

    def setUp(self):
        self.res = result.Result()

    def test_merge(self):
        """
        Test merge method.
        """
        ins = mock.Mock(spec=result.Instance)
        ins.values = {"max_runs": 1}
        ires = mock.Mock(spec=result.InstanceResult)
        ires.runs = [mock.Mock(spec=result.Run), mock.Mock(spec=result.Run)]
        ires.instance = ins
        cres = mock.Mock(spec=result.ClassResult)
        cres.instresults = [ires]
        bench = result.Benchmark("test_bench")
        run = result.Runspec(mock.Mock(), mock.Mock(), bench, mock.Mock(), [cres])
        p = result.Project("test_proj", "job", [run])

        with mock.patch("benchmarktool.result.result.BenchmarkMerge", return_value="bench_merge") as bm:
            self.assertEqual(self.res.merge([p]), "bench_merge")
            bm.assert_called_once_with({bench})
        self.assertEqual(ins.values["max_runs"], 2)

    def test_gen_office(self):
        """
        Test gen_office method.
        """
        run = mock.Mock(spec=result.Runspec)
        run.setting = mock.Mock(spec=result.Setting)
        run.setting.name = "test_setting"
        run.setting.system = mock.Mock(spec=result.System)
        run.setting.system.name = "test_system"
        run.setting.system.version = "1.0"
        p1 = result.Project("p1", "job", [run])
        p2 = result.Project("p2", "job")
        self.res.projects = {"p1": p1, "p2": p2}
        job = mock.Mock(spec=result.Job)
        job.timeout = 10
        self.res.jobs = {"job": job}

        ods_doc = mock.create_autospec(ods_gen.ODSDoc, instance=True)
        ods_doc.inst_sheet = mock.create_autospec(ods_gen.Sheet, instance=True)

        with (
            mock.patch("benchmarktool.result.result.Result.merge", return_value="bench_merge") as bm,
            mock.patch("benchmarktool.result.result.ODSDoc", return_value=ods_doc) as ods_init,
        ):
            ex_file = self.res.gen_office("out", "p1", [("time", "to")])
            self.assertIsNone(ex_file)
            bm.assert_called_once_with([p1])
            ods_init.assert_called_once_with("bench_merge", [("time", "to")])
            ods_doc.add_runspec.assert_called_once_with(run)
            ods_doc.finish.assert_called_once()
            ods_doc.make_ods.assert_called_once_with("out")
            ods_doc.inst_sheet.export_values.assert_not_called()

            ex_file = self.res.gen_office("out.ods", "p1", [("time", "to")], True)
            self.assertIn("out.parquet", ex_file)
            ods_doc.inst_sheet.export_values.assert_called_once()
            self.assertIn({"_to_test_system-1.0/test_setting": [10]}, ods_doc.inst_sheet.export_values.call_args.args)


class TestBenchmarkMerge(TestCase):
    """
    Test cases for BenchmarkMerge class.
    """

    def test_init(self):
        """
        Test class initialization and indirectly __iter__.
        """
        bench = result.Benchmark("bench")
        bcls = result.Class(bench, "bcls", 0)
        bench.classes[0] = bcls
        ins = result.Instance(bcls, "ins", 0)
        ins2 = result.Instance(bcls, "ins2", 1)
        bcls.instances[0] = ins
        bcls.instances[1] = ins2

        bm = result.BenchmarkMerge({bench})
        self.assertEqual(list(bm.benchmarks)[0].classes[0].instances[1].values["row"], 1)
        self.assertEqual(list(bm.benchmarks)[0].classes[0].values["inst_end"], 1)


class TestMachine(TestCase):
    """
    Test cases for Machine class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        name = "name"
        cpu = "cpu"
        mem = "mem"
        m = result.Machine(name, cpu, mem)
        self.assertEqual(m.name, name)
        self.assertEqual(m.cpu, cpu)
        self.assertEqual(m.memory, mem)

        with self.assertRaises(FrozenInstanceError):
            m.name = "new"


class TestConfig(TestCase):
    """
    Test cases for Config class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        name = "name"
        temp = "temp"
        c = result.Config(name, temp)
        self.assertEqual(c.name, name)
        self.assertEqual(c.template, temp)

        with self.assertRaises(FrozenInstanceError):
            c.name = "new"


class TestSystem(TestCase):
    """
    Test cases for System class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        name = "name"
        ver = "ver"
        conf = "conf"
        measure = "measure"
        order = 0
        s = result.System(name, ver, conf, measure, order)
        self.assertEqual(s.name, name)
        self.assertEqual(s.version, ver)
        self.assertEqual(s.config, conf)
        self.assertEqual(s.measures, measure)
        self.assertDictEqual(s.settings, {})

        with self.assertRaises(FrozenInstanceError):
            s.name = "new"


class TestSetting(TestCase):
    """
    Test cases for Setting class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        sys = mock.Mock(spec=result.System)
        name = "name"
        cmd = "cmd"
        tag = "tag"
        order = 0
        attr = {"a": "b"}
        s = result.Setting(sys, name, cmd, tag, order, attr)
        self.assertEqual(s.system, sys)
        self.assertEqual(s.name, name)
        self.assertEqual(s.cmdline, cmd)
        self.assertEqual(s.tag, tag)
        self.assertEqual(s.order, order)
        self.assertDictEqual(s.attr, attr)

        with self.assertRaises(FrozenInstanceError):
            s.name = "new"


class TestJob(TestCase):
    """
    Test cases for Job class.
    """

    def setUp(self):
        self.name = "name"
        self.timeout = 10
        self.runs = 2
        self.attr = {"a": "b"}
        self.j = result.Job(self.name, self.timeout, self.runs, self.attr)

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.j.name, self.name)
        self.assertEqual(self.j.timeout, self.timeout)
        self.assertEqual(self.j.runs, self.runs)
        self.assertDictEqual(self.j.attr, self.attr)

        with self.assertRaises(FrozenInstanceError):
            self.j.name = "new"


class TestSeqJob(TestJob):
    """
    Test cases for SeqJob class.
    """

    def setUp(self):
        super().setUp()
        self.para = 2
        self.j = result.SeqJob(self.name, self.timeout, self.runs, self.attr, self.para)

    def test_init(self):
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.j.parallel, self.para)


class TestDistJob(TestJob):
    """
    Test cases for DistJob class.
    """

    def setUp(self):
        super().setUp()
        self.sm = "sm"
        self.wt = "wt"
        self.pt = "pt"
        self.j = result.DistJob(self.name, self.timeout, self.runs, self.attr, self.sm, self.wt, self.pt)

    def test_init(self):
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.j.script_mode, self.sm)
        self.assertEqual(self.j.walltime, self.wt)
        self.assertEqual(self.j.partition, self.pt)


class TestBenchmark(TestCase):
    """
    Test cases for Benchmark class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        name = "name"
        b = result.Benchmark(name)
        self.assertEqual(b.name, name)
        self.assertDictEqual(b.classes, {})

        with self.assertRaises(FrozenInstanceError):
            b.name = "new"

        # __iter__
        b.classes[0] = mock.Mock(spec=result.Class)
        self.assertListEqual(list(iter(b)), sorted(b.classes.values()))


class TestClass(TestCase):
    """
    Test cases for Class class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        b = mock.Mock(spec=result.Benchmark)
        name = "name"
        ident = 0
        c = result.Class(b, name, ident)
        self.assertEqual(c.benchmark, b)
        self.assertEqual(c.name, name)
        self.assertEqual(c.id, ident)
        self.assertDictEqual(c.instances, {})
        self.assertDictEqual(c.values, {"row": 0, "inst_start": 0, "inst_end": 0})

        with self.assertRaises(FrozenInstanceError):
            c.name = "new"

        # __iter__
        c.instances[0] = mock.Mock(spec=result.Instance)
        self.assertListEqual(list(iter(c)), sorted(c.instances.values()))


class TestInstance(TestCase):
    """
    Test cases for Instance class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        bcls = mock.Mock(spec=result.Class)
        name = "name"
        ident = 0
        i = result.Instance(bcls, name, ident)
        self.assertEqual(i.benchclass, bcls)
        self.assertEqual(i.name, name)
        self.assertEqual(i.id, ident)
        self.assertDictEqual(i.values, {"row": 0, "max_runs": 0})

        with self.assertRaises(FrozenInstanceError):
            i.name = "new"


class TestProject(TestCase):
    """
    Test cases for Project class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        name = "name"
        job = "job"
        p = result.Project(name, job)
        self.assertEqual(p.name, name)
        self.assertEqual(p.job, job)
        self.assertListEqual(p.runspecs, [])

        with self.assertRaises(FrozenInstanceError):
            p.name = "new"

        # __iter__
        p.runspecs.append(mock.Mock(spec=result.Runspec))
        self.assertListEqual(list(iter(p)), p.runspecs)


class TestRunspec(TestCase):
    """
    Test cases for Runspec class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        sys = mock.Mock(spec=result.System)
        m = mock.Mock(spec=result.Machine)
        b = mock.Mock(spec=result.Benchmark)
        s = mock.Mock(spec=result.Setting)
        r = result.Runspec(sys, m, b, s)
        self.assertEqual(r.system, sys)
        self.assertEqual(r.machine, m)
        self.assertEqual(r.benchmark, b)
        self.assertEqual(r.setting, s)
        self.assertListEqual(r.classresults, [])

        with self.assertRaises(FrozenInstanceError):
            r.system = mock.Mock(spec=result.System)

        # __iter__
        r.classresults.append(mock.Mock(spec=result.ClassResult))
        self.assertListEqual(list(iter(r)), r.classresults)


class TestClassResult(TestCase):
    """
    Test cases for ClassResult class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        bcls = mock.Mock(spec=result.Class)
        cres = result.ClassResult(bcls)
        self.assertEqual(cres.benchclass, bcls)
        self.assertListEqual(cres.instresults, [])

        with self.assertRaises(FrozenInstanceError):
            cres.benchclass = mock.Mock(spec=result.Class)

        # __iter__
        cres.instresults.append(mock.Mock(spec=result.InstanceResult))
        self.assertListEqual(list(iter(cres)), cres.instresults)


class TestInstanceResult(TestCase):
    """
    Test cases for InstanceResult class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        ins = mock.Mock(spec=result.Instance)
        ires = result.InstanceResult(ins)
        self.assertEqual(ires.instance, ins)
        self.assertListEqual(ires.runs, [])

        with self.assertRaises(FrozenInstanceError):
            ires.instance = mock.Mock(spec=result.Instance)

        # __iter__
        ires.runs.append(mock.Mock(spec=result.Run))
        self.assertListEqual(list(iter(ires)), ires.runs)


class TestRun(TestCase):
    """
    Test cases for Run class.
    """

    def test_init(self):
        """
        Test class initialization.
        """
        ires = mock.Mock(spec=result.InstanceResult)
        number = 1
        r = result.Run(ires, number)
        self.assertEqual(r.instresult, ires)
        self.assertEqual(r.number, number)
        self.assertDictEqual(r.measures, {})

        with self.assertRaises(FrozenInstanceError):
            r.number = 5

    def test_iter(self):
        """
        Test iter method.
        """
        ires = mock.Mock(spec=result.InstanceResult)
        number = 1
        r = result.Run(ires, number, {"a": ("string", "b"), "c": ("int", "5")})
        res = r.iter([])
        self.assertListEqual(list(res), [("a", "string", "b"), ("c", "int", "5")])
        res = r.iter([("c", "to")])
        self.assertListEqual(list(res), [("c", "int", "5")])
        res = r.iter([("d", "t")])
        self.assertListEqual(list(res), [("d", "None", "NaN")])
