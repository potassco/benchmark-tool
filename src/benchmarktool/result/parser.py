"""
Created on Jan 19, 2010

@author: Roland Kaminski
"""

from typing import Any, Optional

from lxml import etree  # type: ignore[import-untyped]

from benchmarktool import tools
from benchmarktool.result.result import (
    Benchmark,
    Class,
    ClassResult,
    Config,
    DistJob,
    Instance,
    InstanceResult,
    Machine,
    Project,
    Result,
    Run,
    Runspec,
    SeqJob,
    Setting,
    System,
)


# pylint: disable=too-many-instance-attributes
class Parser:
    """
    A parser to parse XML result files.
    """

    def __init__(self) -> None:
        """
        Initializes the parser.
        """

        self.system_order = 0
        self.result = Result()
        self.setting_order = 0
        self.benchscope = False

        self.system: Optional[System] = None
        self.benchmark: Optional[Benchmark] = None
        self.benchclass: Optional[Class] = None
        self.classresult: Optional[ClassResult] = None
        self.instresult: Optional[InstanceResult] = None
        self.runspec: Optional[Runspec] = None
        self.project: Optional[Project] = None
        self.run: Optional[Run] = None

    def parse(self, infile: Any) -> Result:
        """
        Parse a given result file and return its representation
        in form of an instance of class Result.

        Attributes:
            infile (Any): The file to parse.
        """
        # to reduce memory consumption especially for large result files
        # do not use the full blown etree representation
        parser = etree.XMLParser(target=self)
        etree.parse(infile, parser)
        assert isinstance(self.result, Result)
        return self.result

    # pylint: disable=too-many-statements,too-many-branches
    def start(self, tag: str, attrib: dict[str, Any]) -> None:
        """
        This method is called for every opening XML tag.

        Attributes:
            tag (str):               The name of the tag.
            attrib (dict[str, Any]): The attributes of the tag.
        """
        match tag:
            case "machine":
                machine = Machine(attrib["name"], attrib["cpu"], attrib["memory"])
                self.result.machines[machine.name] = machine
            case "config":
                config = Config(attrib["name"], attrib["template"])
                self.result.configs[config.name] = config
            case "system":
                self.system = System(
                    attrib["name"], attrib["version"], attrib["config"], attrib["measures"], self.system_order
                )
                self.result.systems[(self.system.name, self.system.version)] = self.system
                self.system_order += 1
                self.setting_order = 0
            case "setting":
                tag = attrib.pop("tag", None)
                name = attrib.pop("name")
                cmdline = attrib.pop("cmdline")
                assert self.system is not None
                setting = Setting(self.system, name, cmdline, tag, self.setting_order, attrib)
                self.system.settings[name] = setting
                self.setting_order += 1
            case "seqjob":
                name = attrib.pop("name")
                timeout = tools.xml_to_seconds_time(attrib.pop("timeout"))
                runs = int(attrib.pop("runs"))
                parallel = int(attrib.pop("parallel"))
                seq_job = SeqJob(name, timeout, runs, attrib, parallel)
                self.result.jobs[seq_job.name] = seq_job
            case "distjob":
                name = attrib.pop("name")
                timeout = tools.xml_to_seconds_time(attrib.pop("timeout"))
                runs = int(attrib.pop("runs"))
                script_mode = attrib.pop("script_mode")
                walltime = attrib.pop("walltime")
                partition = attrib.pop("partition")
                dist_job = DistJob(name, timeout, runs, attrib, script_mode, walltime, partition)
                self.result.jobs[dist_job.name] = dist_job
            case "benchmark":
                self.benchscope = True
                self.benchmark = Benchmark(attrib["name"])
                self.result.benchmarks[self.benchmark.name] = self.benchmark
            case "project":
                self.project = Project(attrib["name"], attrib["job"])
                self.result.projects[self.project.name] = self.project
            case "runspec":
                self.benchscope = False
                self.runspec = Runspec(
                    self.result.systems[(attrib["system"], attrib["version"])],
                    self.result.machines[attrib["machine"]],
                    self.result.benchmarks[attrib["benchmark"]],
                    self.result.systems[(attrib["system"], attrib["version"])].settings[attrib["setting"]],
                )
                assert self.project is not None
                self.project.runspecs.append(self.runspec)
            case "class":
                if self.benchscope:
                    assert self.benchmark is not None
                    self.benchclass = Class(self.benchmark, attrib["name"], int(attrib["id"]))
                    self.benchmark.classes[self.benchclass.id] = self.benchclass
                else:
                    assert self.runspec is not None
                    benchclass = self.runspec.benchmark.classes[int(attrib["id"])]
                    self.classresult = ClassResult(benchclass)
                    self.runspec.classresults.append(self.classresult)
            case "instance":
                if self.benchscope:
                    assert self.benchclass is not None
                    instance = Instance(self.benchclass, attrib["name"], int(attrib["id"]))
                    self.benchclass.instances[instance.id] = instance
                else:
                    assert self.classresult is not None
                    benchinst = self.classresult.benchclass.instances[int(attrib["id"])]
                    self.instresult = InstanceResult(benchinst)
                    self.classresult.instresults.append(self.instresult)
            case "run":
                if not self.benchscope:
                    assert self.instresult is not None
                    self.run = Run(self.instresult, int(attrib["number"]))
                    self.instresult.runs.append(self.run)
            case "measure":
                assert self.run is not None
                self.run.measures[attrib["name"]] = (attrib["type"], attrib["val"])

    def close(self) -> None:
        """
        This method is called for every closing XML tag.
        """
