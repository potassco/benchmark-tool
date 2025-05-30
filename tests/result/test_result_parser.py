"""
Test cases for result.parser classes.
"""

from unittest import TestCase

from benchmarktool.result import parser, result


# pylint: disable=too-many-statements
class TestParser(TestCase):
    """
    Test cases for Parser class.
    """

    def test_parse(self):
        """
        Test parse method. Includes start and close methods.
        """

        p = parser.Parser()
        res = p.parse("tests/ref/test_eval.xml")
        self.assertIsInstance(res, result.Result)

        # machines
        self.assertEqual(len(res.machines), 1)
        machine = res.machines["test_machine"]
        self.assertIsInstance(machine, result.Machine)
        self.assertEqual(machine.name, "test_machine")
        self.assertEqual(machine.cpu, "test_cpu")
        self.assertEqual(machine.memory, "test_mem")

        # configs
        self.assertEqual(len(res.configs), 1)
        config = res.configs["test_config"]
        self.assertIsInstance(config, result.Config)
        self.assertEqual(config.name, "test_config")
        self.assertEqual(config.template, "templates/seq-test.sh")

        # systems
        self.assertEqual(len(res.systems), 1)
        system = res.systems[("test_sys", "1.0.0")]
        self.assertIsInstance(system, result.System)
        self.assertEqual(system.name, "test_sys")
        self.assertEqual(system.version, "1.0.0")
        self.assertEqual(system.config, "test_config")
        self.assertEqual(system.measures, "test")
        self.assertEqual(system.order, 0)

        # settings
        self.assertEqual(len(system.settings), 2)
        setting = system.settings["test_setting"]
        self.assertIsInstance(setting, result.Setting)
        self.assertEqual(setting.system.name, "test_sys")
        self.assertEqual(setting.name, "test_setting")
        self.assertEqual(setting.cmdline, "test_cmdline")
        self.assertEqual(setting.tag, "basic")
        self.assertEqual(setting.order, 0)
        self.assertDictEqual(setting.attr, {})
        setting = system.settings["test_setting2"]
        self.assertIsInstance(setting, result.Setting)
        self.assertEqual(setting.system.name, "test_sys")
        self.assertEqual(setting.name, "test_setting2")
        self.assertEqual(setting.cmdline, "test_cmdline")
        self.assertEqual(setting.tag, "basic")
        self.assertEqual(setting.order, 1)
        self.assertDictEqual(setting.attr, {})

        # jobs
        self.assertEqual(len(res.jobs), 2)
        seq_job = res.jobs["test_seq"]
        self.assertIsInstance(seq_job, result.SeqJob)
        self.assertEqual(seq_job.name, "test_seq")
        self.assertEqual(seq_job.timeout, 10)
        self.assertEqual(seq_job.runs, 2)
        self.assertEqual(seq_job.parallel, 1)
        self.assertDictEqual(seq_job.attr, {})
        pbs_job = res.jobs["test_pbs"]
        self.assertIsInstance(pbs_job, result.PbsJob)
        self.assertEqual(pbs_job.name, "test_pbs")
        self.assertEqual(pbs_job.timeout, 10)
        self.assertEqual(pbs_job.runs, 2)
        self.assertEqual(pbs_job.script_mode, "timeout")
        self.assertEqual(pbs_job.walltime, "23:59:59")
        self.assertDictEqual(pbs_job.attr, {})

        # benchmarks
        self.assertEqual(len(res.benchmarks), 1)
        bench = res.benchmarks["test_bench"]
        self.assertIsInstance(bench, result.Benchmark)
        self.assertEqual(bench.name, "test_bench")

        # benchmark classes
        self.assertEqual(len(bench.classes), 1)
        benchclass = bench.classes[0]
        self.assertIsInstance(benchclass, result.Class)
        self.assertEqual(benchclass.name, "test_class")
        self.assertEqual(benchclass.id, 0)
        self.assertDictEqual(benchclass.values, {"row": 0, "inst_start": 0, "inst_end": 0})

        # instances
        self.assertEqual(len(benchclass.instances), 1)
        inst = benchclass.instances[0]
        self.assertIsInstance(inst, result.Instance)
        self.assertEqual(inst.benchclass, benchclass)
        self.assertEqual(inst.name, "test_inst")
        self.assertEqual(inst.id, 0)
        self.assertDictEqual(inst.values, {"row": 0, "max_runs": 0})

        # projects
        self.assertEqual(len(res.projects), 1)
        project = res.projects["test_proj"]
        self.assertIsInstance(project, result.Project)
        self.assertEqual(project.name, "test_proj")
        self.assertEqual(project.job, "test_seq")

        # runspecs
        self.assertEqual(len(project.runspecs), 2)
        runspec = project.runspecs[0]
        self.assertIsInstance(runspec, result.Runspec)
        self.assertEqual(runspec.system.name, "test_sys")
        self.assertEqual(runspec.machine.name, "test_machine")
        self.assertEqual(runspec.benchmark.name, "test_bench")
        self.assertEqual(runspec.setting.name, "test_setting")

        # class results
        self.assertEqual(len(runspec.classresults), 1)
        classres = runspec.classresults[0]
        self.assertIsInstance(classres, result.ClassResult)
        self.assertEqual(classres.benchclass.name, "test_class")

        # instance results
        self.assertEqual(len(classres.instresults), 1)
        instres = classres.instresults[0]
        self.assertIsInstance(instres, result.InstanceResult)
        self.assertEqual(instres.instance.name, "test_inst")

        # runs
        self.assertEqual(len(instres.runs), 2)
        run = instres.runs[0]
        self.assertIsInstance(run, result.Run)
        self.assertEqual(run.instresult, instres)
        self.assertEqual(run.number, 1)

        # measures
        self.assertEqual(len(run.measures), 7)
        self.assertTupleEqual(run.measures["time"], ("float", "7"))
