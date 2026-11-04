"""
Test cases for result classes.
"""

from dataclasses import FrozenInstanceError
from unittest import TestCase, mock

from benchmarktool.result import result
from benchmarktool.result.xlsx_gen import xlsx_gen
from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet


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
            bm.assert_called_once_with({bench}, None)
            bm.reset_mock()
            self.assertEqual(self.res.merge([p], class_group_depth=2), "bench_merge")
            bm.assert_called_once_with({bench}, 2)
        self.assertEqual(ins.values["max_runs"], 2)

    def test_gen_spreadsheet(self):
        """
        Test gen_spreadsheet method.
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

        xlsx_doc = mock.create_autospec(xlsx_gen.XLSXDoc, instance=True)
        xlsx_doc.inst_sheet = mock.create_autospec(InstanceSheet, instance=True)

        with (
            mock.patch("benchmarktool.result.result.Result.merge", return_value="bench_merge") as bm,
            mock.patch("benchmarktool.result.result.XLSXDoc", return_value=xlsx_doc) as xlsx_init,
        ):
            ex_file = self.res.gen_spreadsheet("out", "p1", [("time", "to")])
            self.assertIsNone(ex_file)
            bm.assert_called_once_with([p1], None)
            xlsx_init.assert_called_once_with("bench_merge", [("time", "to")], 300, True)
            xlsx_doc.add_runspec.assert_called_once_with(run)
            xlsx_doc.finalize.assert_called_once()
            xlsx_doc.make_xlsx.assert_called_once_with("out.xlsx")
            xlsx_doc.inst_sheet.export_values.assert_not_called()

            ex_file = self.res.gen_spreadsheet("out.xlsx", "p1", [("time", "to")], True)
            self.assertIn("out.parquet", ex_file)
            xlsx_doc.inst_sheet.export_values.assert_called_once()
            self.assertIn({"_to_test_system-1.0/test_setting": [10]}, xlsx_doc.inst_sheet.export_values.call_args.args)

    def test_gen_spreadsheet_class_group_depth(self):
        """
        Test forwarding the depth and using the grouped reporting view.
        """
        run = mock.Mock(spec=result.Runspec)
        project = result.Project("p", "job", [run])
        self.res.projects["p"] = project
        benchmark = mock.Mock(spec=result.BenchmarkMerge)
        with (
            mock.patch.object(self.res, "merge", return_value=benchmark) as merge,
            mock.patch("benchmarktool.result.result.XLSXDoc") as doc,
        ):
            self.res.gen_spreadsheet("out", {"p"}, {"time": "t"}, class_group_depth=2)
        merge.assert_called_once_with([project], 2)
        benchmark.group_runspec.assert_called_once_with(run)
        doc.return_value.add_runspec.assert_called_once_with(benchmark.group_runspec.return_value)


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
        self.assertIsNone(bm.class_group_depth)
        self.assertEqual(ins.values["merged_row"], 0)
        self.assertEqual(ins2.values["merged_row"], 1)
        runspec = mock.Mock(spec=result.Runspec)
        self.assertIs(bm.group_runspec(runspec), runspec)

    def test_invalid_class_group_depth(self):
        """
        Test that nonpositive grouping depths are rejected.
        """
        for depth in (0, -1):
            with self.subTest(depth=depth):
                with self.assertRaisesRegex(ValueError, "Class group depth must be a positive integer"):
                    result.BenchmarkMerge(set(), class_group_depth=depth)

    def test_init_with_class_group_depth(self):
        """
        Test that prefixes, benchmark boundaries, identities, and row ranges are preserved.
        """
        benchmarks = [result.Benchmark("a"), result.Benchmark("b")]
        names = [".", "flat", "planning/small/random", "planning/small/structured", r"scheduling\small\random"]
        originals = []
        for benchmark in benchmarks:
            for index, name in enumerate(names):
                benchclass = result.Class(benchmark, name, index)
                benchmark.classes[index] = benchclass
                instance = result.Instance(benchclass, "case01", 0)
                instance.values["max_runs"] = index
                benchclass.instances[0] = instance
                originals.append(instance)

        for depth, expected in (
            (1, [".", "flat", "planning", "scheduling"]),
            (2, [".", "flat", "planning/small", "scheduling/small"]),
            (5, [".", "flat", "planning/small/random", "planning/small/structured", "scheduling/small/random"]),
        ):
            with self.subTest(depth=depth):
                merged = result.BenchmarkMerge(set(benchmarks), class_group_depth=depth)
                self.assertEqual(merged.class_group_depth, depth)
                self.assertEqual([group.name for group in merged], expected * 2)
                row = 0
                merged_row = 0
                for class_row, group in enumerate(merged):
                    self.assertEqual(group.values["row"], class_row)
                    self.assertEqual(group.values["inst_start"], row)
                    for instance in group:
                        self.assertIs(instance, originals[merged_row])
                        self.assertIs(instance.benchclass.instances[instance.id], instance)
                        self.assertEqual(instance.values["row"], row)
                        self.assertEqual(instance.values["merged_row"], merged_row)
                        row += max(instance.values["max_runs"], 1)
                        merged_row += 1
                    self.assertEqual(group.values["inst_end"], row - 1)
                self.assertEqual(merged_row, len(originals))
        self.assertEqual([instance.benchclass.name for instance in originals], names * 2)

    def test_group_runspec(self):
        """
        Test regrouping of results without copying instances, runs, or source containers.
        """
        benchmark = result.Benchmark("bench")
        classes = []
        for index, name in enumerate(("planning/small/a", "planning/small/b", "planning/large/a")):
            benchclass = result.Class(benchmark, name, index)
            benchmark.classes[index] = benchclass
            instance = result.Instance(benchclass, "case01", 0)
            benchclass.instances[0] = instance
            instresult = result.InstanceResult(instance)
            instresult.runs.append(result.Run(instresult, 1, {"time": ("float", "1")}))
            classes.append(result.ClassResult(benchclass, [instresult]))
        runspec = result.Runspec(mock.Mock(), mock.Mock(), benchmark, mock.Mock(), classes)
        merged = result.BenchmarkMerge({benchmark}, class_group_depth=2)
        grouped = merged.group_runspec(runspec)
        self.assertIsNot(grouped, runspec)
        self.assertIs(grouped.system, runspec.system)
        self.assertIs(grouped.machine, runspec.machine)
        self.assertIs(grouped.setting, runspec.setting)
        self.assertIs(grouped.benchmark, benchmark)
        self.assertEqual([group.benchclass.name for group in grouped], ["planning/large", "planning/small"])
        self.assertIs(grouped.classresults[0].instresults[0], classes[2].instresults[0])
        for index in (0, 1):
            self.assertIs(grouped.classresults[1].instresults[index], classes[index].instresults[0])
        self.assertIs(runspec.classresults, classes)
        self.assertEqual(len(classes), 3)
        self.assertTrue(all(len(group.instresults) == 1 for group in classes))


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
        conf = result.Config("conf", "temp")
        measure = "measure"
        order = 0
        cmdline = {"pre": "cmdline", "post": "cmdline_post"}
        s = result.System(name, ver, measure, order, conf, cmdline)
        self.assertEqual(s.name, name)
        self.assertEqual(s.version, ver)
        self.assertEqual(s.config, conf)
        self.assertEqual(s.measures, measure)
        self.assertEqual(s.order, order)
        self.assertDictEqual(s.cmdline, cmdline)
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
        cmd = {"pre": "cmdline", "post": "cmdline_post"}
        tag = "tag"
        order = 0
        dist_template = "dist_temp"
        dist_options = "dist_opt"
        attr = {"a": "b"}
        s = result.Setting(
            system=sys,
            name=name,
            cmdline=cmd,
            tag=tag,
            order=order,
            dist_template=dist_template,
            dist_options=dist_options,
            attr=attr,
        )
        self.assertEqual(s.system, sys)
        self.assertEqual(s.name, name)
        self.assertDictEqual(s.cmdline, cmd)
        self.assertEqual(s.tag, tag)
        self.assertEqual(s.order, order)
        self.assertEqual(s.dist_template, dist_template)
        self.assertEqual(s.dist_options, dist_options)
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
        self.memout = 5000
        self.runs = 2
        self.attr = {"a": "b"}
        self.template_options = "test_op"
        self.j = result.Job(
            name=self.name,
            timeout=self.timeout,
            memout=self.memout,
            runs=self.runs,
            attr=self.attr,
            template_options=self.template_options,
        )

    def test_init(self):
        """
        Test class initialization.
        """
        self.assertEqual(self.j.name, self.name)
        self.assertEqual(self.j.timeout, self.timeout)
        self.assertEqual(self.j.memout, self.memout)
        self.assertEqual(self.j.runs, self.runs)
        self.assertDictEqual(self.j.attr, self.attr)
        self.assertEqual(self.j.template_options, self.template_options)

        with self.assertRaises(FrozenInstanceError):
            self.j.name = "new"


class TestSeqJob(TestJob):
    """
    Test cases for SeqJob class.
    """

    def setUp(self):
        super().setUp()
        self.para = 2
        self.j = result.SeqJob(
            name=self.name,
            timeout=self.timeout,
            memout=self.memout,
            runs=self.runs,
            attr=self.attr,
            template_options=self.template_options,
            parallel=self.para,
        )

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
        self.cpt = 2
        self.pt = "pt"
        self.j = result.DistJob(
            name=self.name,
            timeout=self.timeout,
            memout=self.memout,
            runs=self.runs,
            attr=self.attr,
            template_options=self.template_options,
            script_mode=self.sm,
            walltime=self.wt,
            cpt=self.cpt,
            partition=self.pt,
        )

    def test_init(self):
        """
        Test class initialization.
        """
        super().test_init()
        self.assertEqual(self.j.script_mode, self.sm)
        self.assertEqual(self.j.walltime, self.wt)
        self.assertEqual(self.j.cpt, self.cpt)
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
        inst_id = 0
        cmdline = {"pre": "cmdline", "post": "cmdline_post"}
        i = result.Instance(bcls, name, inst_id, cmdline)
        self.assertEqual(i.benchclass, bcls)
        self.assertEqual(i.name, name)
        self.assertEqual(i.id, inst_id)
        self.assertDictEqual(i.cmdline, cmdline)
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
        res = r.iter({})
        self.assertListEqual(list(res), [("a", "string", "b"), ("c", "int", "5")])
        res = r.iter({"c": "to"})
        self.assertListEqual(list(res), [("c", "int", "5")])
        res = r.iter({"d": "t"})
        self.assertListEqual(list(res), [("d", "None", "NaN")])
