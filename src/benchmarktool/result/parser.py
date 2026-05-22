"""
Created on Jan 19, 2010

@author: Roland Kaminski
"""

from typing import Any, Optional, TypeVar

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
        self.setting: Optional[Setting] = None
        self.benchmark: Optional[Benchmark] = None
        self.benchclass: Optional[Class] = None
        self.classresult: Optional[ClassResult] = None
        self.instresult: Optional[InstanceResult] = None
        self.runspec: Optional[Runspec] = None
        self.project: Optional[Project] = None
        self.run: Optional[Run] = None

    @staticmethod
    def _pop_required(attrib: dict[str, Any], key: str, tag: str) -> Any:
        """
        Pop required XML attribute and raise a contextual ValueError when missing.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to pop from.
            key (str):              The key of the required attribute.
            tag (str):              The name of the XML tag for error context.
        """
        if (value := attrib.pop(key, None)) is None:
            raise ValueError(f"Missing required attribute '{key}' in {tag}")  # nocoverage
        return value

    @staticmethod
    def _get_required(attrib: dict[str, Any], key: str, tag: str) -> Any:
        """
        Read required XML attribute and raise a contextual ValueError when missing.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            key (str):              The key of the required attribute.
            tag (str):              The name of the XML tag for error context.
        """
        if (value := attrib.get(key)) is None:
            raise ValueError(f"Missing required attribute '{key}' in {tag}")  # nocoverage
        return value

    @staticmethod
    def _pop_required_int(attrib: dict[str, Any], key: str, tag: str) -> int:
        """
        Parse a required integer XML attribute.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to pop from.
            key (str):              The key of the required attribute.
            tag (str):              The name of the XML tag for error context.
        """
        value = Parser._pop_required(attrib, key, tag)
        try:
            return int(value)
        except (TypeError, ValueError) as e:  # nocoverage
            raise ValueError(f"Invalid integer value for attribute '{key}' in {tag}: {value}") from e

    @staticmethod
    def _get_required_int(attrib: dict[str, Any], key: str, tag: str) -> int:
        """
        Parse a required integer XML attribute without removing it.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            key (str):              The key of the required attribute.
            tag (str):              The name of the XML tag for error context.
        """
        value = Parser._get_required(attrib, key, tag)
        try:
            return int(value)
        except (TypeError, ValueError) as e:  # nocoverage
            raise ValueError(f"Invalid integer value for attribute '{key}' in {tag}: {value}") from e

    @staticmethod
    def _pop_required_time(attrib: dict[str, Any], key: str, tag: str) -> int:
        """
        Parse a required XML time attribute.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to pop from.
            key (str):              The key of the required attribute.
            tag (str):              The name of the XML tag for error context.
        """
        value = Parser._pop_required(attrib, key, tag)
        try:
            return tools.xml_to_seconds_time(value)
        except (TypeError, ValueError) as e:  # nocoverage
            raise ValueError(f"Invalid time value for attribute '{key}' in {tag}: {value}") from e

    T = TypeVar("T")

    @staticmethod
    def _lookup(mapping: dict[Any, T], key: Any, obj: str, tag: str) -> T:
        """
        Lookup an object in a mapping and fail with contextual ValueError.

        Attributes:
            mapping (dict[Any, T]): The mapping to lookup from.
            key (Any):              The key to lookup.
            obj (str):              The description of the object being looked up.
            tag (str):              The name of the XML tag for error context.
        """
        if (value := mapping.get(key)) is None:
            raise ValueError(f"Unknown {obj} '{key}' referenced in {tag}")  # nocoverage
        return value

    def _parse_machine(self, attrib: dict[str, Any], tag: str) -> Machine:
        """
        Parse Machine object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        return Machine(
            self._get_required(attrib, "name", tag),
            self._get_required(attrib, "cpu", tag),
            self._get_required(attrib, "memory", tag),
        )

    def _parse_config(self, attrib: dict[str, Any], tag: str) -> Config:
        """
        Parse Config object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        return Config(
            self._get_required(attrib, "name", tag),
            self._get_required(attrib, "template", tag),
        )

    def _parse_system(self, attrib: dict[str, Any], tag: str) -> System:
        """
        Parse System object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        name = self._pop_required(attrib, "name", tag)
        version = self._pop_required(attrib, "version", tag)
        measures = self._pop_required(attrib, "measures", tag)
        config_key = self._pop_required(attrib, "config", tag)
        config = self._lookup(self.result.configs, config_key, "config", tag)
        cmdline = {"pre": attrib.pop("cmdline", ""), "post": attrib.pop("cmdline_post", "")}
        return System(name, version, measures, self.system_order, config, cmdline)

    def _parse_setting(self, attrib: dict[str, Any], tag: str) -> Setting:
        """
        Parse Setting object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        setting_tag = self._pop_required(attrib, "tag", tag)
        name = self._pop_required(attrib, "name", tag)
        cmdline = {"pre": attrib.pop("cmdline", ""), "post": attrib.pop("cmdline_post", "")}
        dist_template = attrib.pop("dist_template", "")
        dist_options = attrib.pop("dist_options", "")
        if self.system is None:
            raise ValueError(f"Setting '{name}' defined outside of a system")  # nocoverage
        return Setting(
            system=self.system,
            name=name,
            cmdline=cmdline,
            tag=setting_tag,
            order=self.setting_order,
            dist_template=dist_template,
            dist_options=dist_options,
            attr=attrib,
            encodings=dict(),
        )

    def _parse_encoding(self, attrib: dict[str, Any], tag: str) -> None:
        """
        Parse Encoding object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        file = self._get_required(attrib, "file", tag)
        if self.benchscope:
            # instance encodings currently unused
            return
        else:
            encoding_tag = attrib.pop("encoding_tag", "_default_")
            if self.setting is None:
                raise ValueError(f"Encoding '{file}' defined outside of a setting")  # nocoverage
            self.setting.encodings.setdefault(encoding_tag, set()).add(file)

    def _parse_seqjob(self, attrib: dict[str, Any], tag: str) -> SeqJob:
        """
        Parse SeqJob object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        name = self._pop_required(attrib, "name", tag)
        timeout = self._pop_required_time(attrib, "timeout", tag)
        memout = self._pop_required_int(attrib, "memout", tag)
        runs = self._pop_required_int(attrib, "runs", tag)
        template_options = attrib.pop("template_options", "")
        parallel = self._pop_required_int(attrib, "parallel", tag)
        return SeqJob(
            name=name,
            timeout=timeout,
            runs=runs,
            attr=attrib,
            memout=memout,
            template_options=template_options,
            parallel=parallel,
        )

    def _parse_distjob(self, attrib: dict[str, Any], tag: str) -> DistJob:
        """
        Parse DistJob object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        name = self._pop_required(attrib, "name", tag)
        timeout = self._pop_required_time(attrib, "timeout", tag)
        memout = self._pop_required_int(attrib, "memout", tag)
        runs = self._pop_required_int(attrib, "runs", tag)
        template_options = attrib.pop("template_options", "")
        script_mode = self._pop_required(attrib, "script_mode", tag)
        walltime = self._pop_required(attrib, "walltime", tag)
        cpt = self._pop_required_int(attrib, "cpt", tag)
        partition = self._pop_required(attrib, "partition", tag)
        return DistJob(
            name=name,
            timeout=timeout,
            runs=runs,
            attr=attrib,
            memout=memout,
            template_options=template_options,
            script_mode=script_mode,
            walltime=walltime,
            cpt=cpt,
            partition=partition,
        )

    def _parse_benchmark(self, attrib: dict[str, Any], tag: str) -> Benchmark:
        """
        Parse Benchmark object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        return Benchmark(self._get_required(attrib, "name", tag))

    def _parse_project(self, attrib: dict[str, Any], tag: str) -> Project:
        """
        Parse Project object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        return Project(self._get_required(attrib, "name", tag), self._get_required(attrib, "job", tag))

    def _parse_runspec(self, attrib: dict[str, Any], tag: str) -> Runspec:
        """
        Parse Runspec object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        system_name = self._get_required(attrib, "system", tag)
        system_version = self._get_required(attrib, "version", tag)
        machine_name = self._get_required(attrib, "machine", tag)
        benchmark_name = self._get_required(attrib, "benchmark", tag)
        setting_name = self._get_required(attrib, "setting", tag)
        system = self._lookup(self.result.systems, (system_name, system_version), "system", tag)
        machine = self._lookup(self.result.machines, machine_name, "machine", tag)
        benchmark = self._lookup(self.result.benchmarks, benchmark_name, "benchmark", tag)
        setting = self._lookup(system.settings, setting_name, "setting", tag)
        if self.project is None:
            raise ValueError(f"Runspec defined outside of a project")  # nocoverage
        runspec = Runspec(system, machine, benchmark, setting)
        self.project.runspecs.append(runspec)
        return runspec

    def _parse_class(self, attrib: dict[str, Any], tag: str) -> None:
        """
        Parse Class object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        if self.benchscope:
            if self.benchmark is None:
                raise ValueError(f"Class defined outside of a benchmark")  # nocoverage
            self.benchclass = Class(
                self.benchmark,
                self._get_required(attrib, "name", tag),
                self._get_required_int(attrib, "id", tag),
            )
            self.benchmark.classes[self.benchclass.id] = self.benchclass
        else:
            if self.runspec is None:
                raise ValueError(f"Class defined outside of a runspec")  # nocoverage
            benchclass = self._lookup(
                self.runspec.benchmark.classes,
                self._get_required_int(attrib, "id", tag),
                "class",
                tag,
            )
            self.classresult = ClassResult(benchclass)
            self.runspec.classresults.append(self.classresult)

    def _parse_instance(self, attrib: dict[str, Any], tag: str) -> None:
        """
        Parse Instance object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        if self.benchscope:
            if self.benchclass is None:
                raise ValueError(f"Instance defined outside of a class")  # nocoverage
            cmdline = {"pre": attrib.pop("cmdline", ""), "post": attrib.pop("cmdline_post", "")}
            # instance and encoding files and encoding_tag currently unused
            instance = Instance(
                self.benchclass,
                self._get_required(attrib, "name", tag),
                self._get_required_int(attrib, "id", tag),
                cmdline,
            )
            self.benchclass.instances[instance.id] = instance
        else:
            if self.classresult is None:
                raise ValueError(f"Instance defined outside of a class result")  # nocoverage
            benchinst = self._lookup(
                self.classresult.benchclass.instances,
                self._get_required_int(attrib, "id", tag),
                "instance",
                tag,
            )
            self.instresult = InstanceResult(benchinst)
            self.classresult.instresults.append(self.instresult)

    def _parse_run(self, attrib: dict[str, Any], tag: str) -> None:
        """
        Parse Run object.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        if not self.benchscope:
            if self.instresult is None:
                raise ValueError(f"Run defined outside of an instance result")  # nocoverage
            self.run = Run(self.instresult, self._get_required_int(attrib, "number", tag))
            self.instresult.runs.append(self.run)

    def _parse_measure(self, attrib: dict[str, Any], tag: str) -> None:
        """
        Parse measurement.

        Attributes:
            attrib (dict[str, Any]): The attribute dictionary to read from.
            tag (str):               The name of the XML tag for error context.
        """
        if self.run is None:
            raise ValueError(f"Measure defined outside of a run")  # nocoverage
        name = self._get_required(attrib, "name", tag)
        measure_type = self._get_required(attrib, "type", tag)
        value = self._get_required(attrib, "val", tag)
        self.run.measures[name] = (measure_type, value)

    def start(self, tag: str, attrib: dict[str, Any]) -> None:
        """
        This method is called for every opening XML tag.

        Attributes:
            tag (str):               The name of the tag.
            attrib (dict[str, Any]): The attributes of the tag.
        """
        match tag:
            case "machine":
                machine = self._parse_machine(attrib, tag)
                self.result.machines[machine.name] = machine
            case "config":
                config = self._parse_config(attrib, tag)
                self.result.configs[config.name] = config
            case "system":
                self.system = self._parse_system(attrib, tag)
                self.result.systems[(self.system.name, self.system.version)] = self.system
                self.system_order += 1
                self.setting_order = 0
            case "setting":
                self.setting = self._parse_setting(attrib, tag)
                self.system.settings[self.setting.name] = self.setting
                self.setting_order += 1
            case "encoding":
                self._parse_encoding(attrib, tag)
            case "seqjob":
                seq_job = self._parse_seqjob(attrib, tag)
                self.result.jobs[seq_job.name] = seq_job
            case "distjob":
                dist_job = self._parse_distjob(attrib, tag)
                self.result.jobs[dist_job.name] = dist_job
            case "benchmark":
                self.benchscope = True
                self.benchmark = self._parse_benchmark(attrib, tag)
                self.result.benchmarks[self.benchmark.name] = self.benchmark
            case "project":
                self.project = self._parse_project(attrib, tag)
                self.result.projects[self.project.name] = self.project
            case "runspec":
                self.benchscope = False
                self.runspec = self._parse_runspec(attrib, tag)
            case "class":
                self._parse_class(attrib, tag)
            case "instance":
                self._parse_instance(attrib, tag)
            case "run":
                self._parse_run(attrib, tag)
            case "measure":
                self._parse_measure(attrib, tag)

    def close(self) -> None:
        """
        This method is called for every closing XML tag.
        """

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
