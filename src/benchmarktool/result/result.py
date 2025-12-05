"""
Created on Jan 19, 2010

@author: Roland Kaminski
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

from benchmarktool.result.xlsx_gen import XLSXDoc


class Result:
    """
    Stores the benchmark description and its results.
    """

    def __init__(self) -> None:
        """
        Initializes an empty result.
        """
        self.machines: dict[str, Machine] = {}
        self.configs: dict[str, Config] = {}
        self.systems: dict[tuple[str, str], System] = {}
        self.jobs: dict[str, SeqJob | DistJob] = {}
        self.benchmarks: dict[str, Benchmark] = {}
        self.projects: dict[str, Project] = {}

    def merge(self, projects: list["Project"]) -> "BenchmarkMerge":
        """
        Concatenates the benchmarks in the given projects into one benchmark set.

        Attributes:
            projects (list[Project]): The projects to merge with.
        """
        benchmarks: set[Benchmark] = set()
        for project in projects:
            for runspec in project:
                for classresult in runspec:
                    for instresult in classresult.instresults:
                        instresult.instance.values["max_runs"] = max(
                            instresult.instance.values["max_runs"], len(instresult.runs)
                        )
                benchmarks.add(runspec.benchmark)
        return BenchmarkMerge(benchmarks)

    # pylint: disable=too-many-positional-arguments
    def gen_spreadsheet(
        self,
        out: str,
        sel_projects: set[str],
        measures: list[tuple[str, Any]],
        export: bool = False,
        max_col_width: int = 300,
    ) -> Optional[str]:
        """
        Prints the current result in an Excel spreadsheet format.
        Returns the name of the export file if values are exported.

        Attributes:
            out (str):                        The output file to write to.
            sel_projects (set[str]):          The selected projects ("" for all).
            measures (list[tuple[str, Any]]): The measures to extract.
            export (bool):                    Whether to export the raw values as parquet file.
            max_col_width (int):              The maximum column width for spreadsheet.
        """
        projects: list[Project] = []
        for project in self.projects.values():
            if len(sel_projects) == 0 or project.name in sel_projects:
                projects.append(project)
        benchmark_merge = self.merge(projects)

        doc = XLSXDoc(benchmark_merge, measures, max_col_width)
        for project in projects:
            for runspec in project:
                doc.add_runspec(runspec)
        doc.finish()
        doc.make_xlsx(out)

        if export:
            # as_posix() for windows compatibility
            ex_file = Path(out).absolute().as_posix().replace(".xlsx", ".parquet")
            timeout_meta = {}
            for project in projects:
                for runspec in project.runspecs:
                    timeout_meta[
                        "_to_"
                        + runspec.setting.system.name
                        + "-"
                        + runspec.setting.system.version
                        + "/"
                        + runspec.setting.name
                    ] = [self.jobs[project.job].timeout]
            doc.inst_sheet.export_values(ex_file, timeout_meta)
            return ex_file
        return None


class BenchmarkMerge:
    """
    Represents an (ordered) set of benchmark sets.
    """

    def __init__(self, benchmarks: set["Benchmark"]):
        """
        Initializes using the given set of benchmarks.

        Attributes:
            benchmarks (set[Benchmark]): Benchmarks to merge.
        """
        self.benchmarks = benchmarks
        inst_num = 0
        class_num = 0
        for benchclass in self:
            benchclass.values["row"] = class_num
            benchclass.values["inst_start"] = inst_num
            for instance in benchclass:
                instance.values["row"] = inst_num
                inst_num += max(instance.values["max_runs"], 1)
            benchclass.values["inst_end"] = inst_num - 1
            class_num += 1

    def __iter__(self) -> Iterator["Class"]:
        """
        Creates an interator over all benchmark classes in all benchmarks.
        """
        for benchmark in sorted(self.benchmarks):
            yield from benchmark


@dataclass(order=True, frozen=True)
class Machine:
    """
    Represents a machine.

    Attributes:
        name (str):   The name of the machine.
        cpu (str):    String describing the CPU.
        memory (str): String describing the Memory.
    """

    name: str
    cpu: str = field(compare=False)
    memory: str = field(compare=False)


@dataclass(order=True, frozen=True)
class Config:
    """
    Represents a config.

    Attributes:
        name (str):     The name of the config.
        template (str): A path to the template file.
    """

    name: str
    template: str = field(compare=False)


@dataclass(order=True, frozen=True)
class System:
    """
    Represents a system.

    Attributes:
        name (str):                    The name of the system.
        version (str):                 The version.
        config (str):                  The config (a string).
        measures (str):                The measurement function (a string).
        order (int):                   An integer denoting the occurrence in the XML file.
        settings (dict[str, Setting]): Dictionary of all system settings.
    """

    name: str
    version: str
    config: str = field(compare=False)
    measures: str = field(compare=False)
    order: int
    settings: dict[str, "Setting"] = field(default_factory=dict, compare=False)


@dataclass(order=True, frozen=True)
class Setting:
    """
    Represents a setting.

    Attributes:
        system (System):       The system associated with the setting.
        name (str):            The name of the setting.
        cmdline (str):         Command line parameters.
        tag (str):             Tags of the setting.
        order (int):           An integer denoting the occurrence in the XML file.
        attr (dict[str, Any]): Arbitrary extra arguments.
    """

    system: "System"
    name: str
    cmdline: str = field(compare=False)
    tag: str = field(compare=False)
    order: int
    attr: dict[str, Any] = field(compare=False)


@dataclass(order=True, frozen=True)
class Job:
    """
    Represents a job.

    Attributes:
        name (str):            The name of the job.
        timeout (int):         Timeout of the job.
        runs (int):            Number of repetitions per instance.
        attr (dict[str, Any]): Arbitrary extra arguments.
    """

    name: str
    timeout: int = field(compare=False)
    runs: int = field(compare=False)
    attr: dict[str, Any] = field(compare=False)


@dataclass(order=True, frozen=True)
class SeqJob(Job):
    """
    Represents a sequential job.

    Attributes:
        name (str):              The name of the job.
        timeout (int):           Timeout of the job.
        runs (int):              Number of repetitions per instance.
        attrib (dict[str, Any]): Arbitrary extra arguments.
        parallel (int):          Number of processes to start in parallel.
    """

    parallel: int = field(compare=False)


@dataclass(order=True, frozen=True)
class DistJob(Job):
    """
    Represents a dist job.

    Attributes:
        name (str):              The name of the job.
        timeout (int):           Timeout of the job.
        runs (int):              Number of repetitions per instance.
        attrib (dict[str, Any]): Arbitrary extra arguments.
        script_mode (str):       Specifies the script generation mode.
        walltime (str):          The walltime for a distributed job.
    """

    script_mode: str = field(compare=False)
    walltime: str = field(compare=False)
    partition: str = field(compare=False)


@dataclass(order=True, frozen=True)
class Benchmark:
    """
    Represents a benchmark, i.e., a set of instances.

    Attributes:
        name (str):                 The name of the benchmark.
        classes (dict[int, Class]): Benchmark classes in this benchmark.
    """

    name: str
    classes: dict[int, "Class"] = field(default_factory=dict, compare=False)

    def __iter__(self) -> Iterator["Class"]:
        """
        Creates an iterator over all benchmark classes.
        """
        yield from sorted(self.classes.values())


@dataclass(order=True, frozen=True)
class Class:
    """
    Represents a benchmark class.

    Attributes:
        benchmark (Benchmark):           The benchmark associaed with this class.
        name (str):                      The name of the benchmark.
        id (int):                        A unique id (in the scope of the benchmark).
        instances (dict[int, Instance]): Instances belonging to this benchmark class.
        values (dict[str, Any]):         Mutable dict with helper values.
    """

    benchmark: Benchmark
    name: str
    id: int = field(compare=False)
    instances: dict[int, "Instance"] = field(default_factory=dict, compare=False)
    values: dict[str, int] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        """
        Initialize mutable helper variables.
        """
        self.values["row"] = 0
        self.values["inst_start"] = 0
        self.values["inst_end"] = 0

    def __iter__(self) -> Iterator["Instance"]:
        """
        Creates an iterator over all instances in the benchmark class.
        """
        yield from sorted(self.instances.values())


@dataclass(order=True, frozen=True)
class Instance:
    """
    Represents a benchmark instance.

    Attributes:
        benchclass (Class):      The class of the instance.
        name (str):              The name of the benchmark.
        id (int):                A unique id (in the scope of the benchmark).
        max_runs (int):          Max number of runs.
        values (dict[str, Any]): Mutable dict with helper values.
    """

    benchclass: Class
    name: str
    id: int = field(compare=False)
    values: dict[str, int] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        """
        Initialize mutable helper variables.
        """
        self.values["max_runs"] = 0
        self.values["row"] = 0


@dataclass(order=True, frozen=True)
class Project:
    """
    Describes a project, i.e, a collection of run specifications.

    Attributes:
        name (str):                 The name of the project.
        job (str):                  The name of the associated job.
        runspecs (list['Runspec']): Run specifications of the project.
    """

    name: str
    job: str = field(compare=False)
    runspecs: list["Runspec"] = field(default_factory=list, compare=False)

    def __iter__(self) -> Iterator["Runspec"]:
        """
        Creates an iterator over all run specification in the project.
        """
        yield from self.runspecs


@dataclass(order=True, frozen=True)
class Runspec:
    """
    Describes a run specification, i.e, how to run individual systems
    on a set of instances.

    Attributes:
        system (System):                  The system to evaluate.
        machine (Machine):                The machine to run on.
        benchmark (Benchmark):            The benchmark set to evaluate.
        setting (Setting):                The setting to run with.
        classresults (list[ClassResult]): The benchmark results.
    """

    system: "System"
    machine: "Machine"
    benchmark: "Benchmark"
    setting: "Setting"
    classresults: list["ClassResult"] = field(default_factory=list, compare=False)

    def __iter__(self) -> Iterator["ClassResult"]:
        """
        Creates an iterator over all results (grouped by benchmark class.)
        """
        yield from self.classresults


@dataclass(order=True, frozen=True)
class ClassResult:
    """
    Represents the results of all instances of a benchmark class.

    Attributes:
        benchclass (Class):                 The benchmark class for the results.
        instresults (list[InstanceResult]): Results of instances belonging to the benchmark class.
    """

    benchclass: "Class"
    instresults: list["InstanceResult"] = field(default_factory=list, compare=False)

    def __iter__(self) -> Iterator["InstanceResult"]:
        """
        Creates an iterator over all the individual results per instance.
        """
        yield from self.instresults


@dataclass(order=True, frozen=True)
class InstanceResult:
    """
    Represents the result of an individual instance (with possibly multiple runs).

    Attributes:
        instance (Instance): The instance for the results.
        runs (list[Run]):    Results of runs belonging to the instance.
    """

    instance: "Instance"
    runs: list["Run"] = field(default_factory=list, compare=False)

    def __iter__(self) -> Iterator["Run"]:
        """
        Creates an iterator over the result of all runs.
        """
        yield from self.runs


@dataclass(order=True, frozen=True)
class Run:
    """
    Represents the result of an individual run of a benchmark instance.

    Attributes:
        instresult (InstanceResult):           The associated instance result.
        number (int):                          The number of the run.
        measures (dict[str, tuple[str, str]]): Concrete measurements.
    """

    instresult: "InstanceResult"
    number: int
    measures: dict[str, tuple[str, str]] = field(default_factory=dict, compare=False)

    def iter(self, measures: list[tuple[str, Any]]) -> Iterator[tuple[str, str, str]]:
        """
        Creates an iterator over all measures captured during the run.
        Measures can be filter by giving a string set of measure names.
        If this string set is empty, instead all measures sorted by their keys
        will be returned.

        Attributes:
            measures (list[tuple[str, Any]]): Selected measures.
        """
        if len(measures) == 0:
            for name in sorted(self.measures.keys()):
                yield name, self.measures[name][0], self.measures[name][1]
        else:
            for name, _ in measures:
                if name in self.measures:
                    yield name, self.measures[name][0], self.measures[name][1]
                else:
                    yield name, "None", "NaN"
