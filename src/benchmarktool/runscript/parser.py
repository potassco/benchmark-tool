"""
This module contains an XML-parser for run script specifications.
It reads and converts a given specification and returns its
representation in form of python classes.
"""

__author__ = "Roland Kaminski"
import os
import sys
from typing import Any

from lxml import etree  # type: ignore[import-untyped]

from benchmarktool import tools
from benchmarktool.runscript.runscript import (
    Benchmark,
    Config,
    DistJob,
    Machine,
    Project,
    Runscript,
    SeqJob,
    Setting,
    System,
    TagDisj,
)


# pylint: disable=anomalous-backslash-in-string, line-too-long, too-many-locals
class Parser:
    """
    A parser to parse xml runscript specifications.
    """

    def __init__(self) -> None:
        """
        Initializes the parser.
        """

    # pylint: disable=too-many-branches, too-many-statements, too-many-nested-blocks
    def parse(self, file_name: str) -> Runscript:
        """
        Parse a given runscript and return its representation
        in form of an instance of class Runscript.

        Attributes:
            fileName (str): a string holding a path to a xml file.
        """

        schemas_dir = os.path.join(os.path.dirname(__file__), "schemas")
        if not os.path.isdir(schemas_dir):
            sys.stderr.write(
                f"*** ERROR: Resources missing: '{schemas_dir}' does not exist.\nTry reinstalling the package.\n"
            )
            sys.exit(1)

        doc = self.parse_file(file_name, schemas_dir, "runscript.xml")

        root = doc.getroot()
        run = Runscript(root.get("output"))

        for node in root.xpath("./distjob"):
            run.add_job(self._parse_job(node, "distjob"))

        for node in root.xpath("./seqjob"):
            run.add_job(self._parse_job(node, "seqjob"))

        for node in root.xpath("./machine"):
            machine = Machine(node.get("name"), node.get("cpu"), node.get("memory"))
            run.add_machine(machine)

        for node in root.xpath("./config"):
            config = Config(node.get("name"), node.get("template"))
            run.add_config(config)

        compound_settings: dict[str, list[str]] = {}
        system_order = 0
        for node in root.xpath("./system"):
            config = run.configs[node.get("config")]
            system = System(node.get("name"), node.get("version"), node.get("measures"), system_order, config)
            setting_order = 0
            sys_cmdline = node.get("cmdline")
            sys_cmdline_post = node.get("cmdline_post")
            for child in node.xpath("setting"):
                attr = self._filter_attr(
                    child, ["name", "cmdline", "cmdline_post", "tag", "dist_options", "dist_template"]
                )
                compound_settings[child.get("name")] = []
                dist_template = child.get("dist_template")
                if dist_template is None:
                    dist_template = "templates/single.dist"
                if child.get("tag") is None:
                    tag = set()
                else:
                    tag = set(child.get("tag").split(None))
                dist_options = child.get("dist_options")
                if dist_options is None:
                    dist_options = ""
                encodings: dict[str, set[str]] = {"_default_": set()}
                for grandchild in child.xpath("./encoding"):
                    if grandchild.get("enctag") is None:
                        encodings["_default_"].add(os.path.normpath(grandchild.get("file")))
                    else:
                        enctags = set(grandchild.get("enctag").split(None))
                        for t in enctags:
                            if t not in encodings:
                                encodings[t] = set()
                            encodings[t].add(os.path.normpath(grandchild.get("file")))

                cmdline = " ".join(
                    filter(None, [sys_cmdline, child.get("cmdline"), sys_cmdline_post, child.get("cmdline_post")])
                )
                name = child.get("name")
                compound_settings[child.get("name")].append(name)
                keys = list(attr.keys())
                if keys:
                    sys.stderr.write(
                        f"""*** INFO: Attribute{'s' if len(keys) > 1 else ''} {', '.join(f"'{k}'" for k in keys)} in setting '{name}' {'are' if len(keys) > 1 else 'is'} currently unused.\n"""
                    )
                setting = Setting(
                    name=name,
                    cmdline=cmdline,
                    tag=tag,
                    order=setting_order,
                    dist_template=dist_template,
                    attr=attr,
                    dist_options=dist_options,
                    encodings=encodings,
                )
                system.add_setting(setting)
                setting_order += 1

            run.systems[(system.name, system.version)] = system
            system_order += 1

        element: Any
        for node in root.xpath("./benchmark"):
            benchmark = Benchmark(node.get("name"))
            for child in node.xpath("./spec"):
                # discover spec files
                for dirpath, dirnames, filenames in os.walk(child.get("path")):
                    tag = child.get("instance_tag")
                    if "spec.xml" in filenames:
                        # stop recursion if spec.xml found
                        dirnames.clear()
                        spec_file = os.path.join(dirpath, "spec.xml")
                        spec = self.parse_file(spec_file, schemas_dir, "benchmark_spec.xml").getroot()
                        for class_elem in spec.xpath("./class"):
                            class_name = class_elem.get("name")
                            if class_elem.get("encoding_tag") is None:
                                enctag = set()
                            else:
                                enctag = set(class_elem.get("encoding_tag").split(None))

                            elements: list[Any] = []
                            instances = class_elem.xpath("./instance")
                            if instances:
                                files = Benchmark.Files(dirpath, class_name)
                                for instance in instances:
                                    if (
                                        tag is None
                                        or instance.get("instance_tag") is None
                                        or TagDisj(tag).match(set(instance.get("instance_tag").split(None)))
                                    ):
                                        files.add_file(instance.get("file"), instance.get("group"))
                                files.add_enctags(enctag)
                                elements.append(files)

                            # folder elements are still in development
                            for folder_elem in class_elem.xpath("./folder"):
                                if (
                                    tag is None
                                    or folder_elem.get("instance_tag") is None
                                    or TagDisj(tag).match(set(folder_elem.get("instance_tag").split(None)))
                                ):
                                    if folder_elem.get("group") is not None:
                                        group = folder_elem.get("group").lower() == "true"
                                    else:
                                        group = False
                                    folder = Benchmark.Folder(
                                        os.path.join(dirpath, folder_elem.get("path")), group, class_name
                                    )
                                    folder.add_enctags(enctag)
                                    elements.append(folder)

                            for element in elements:
                                for encoding in class_elem.xpath("./encoding"):
                                    element.add_encoding(encoding.get("file"))
                                benchmark.add_element(element)

            for child in node.xpath("./folder"):
                if child.get("group") is not None:
                    group = child.get("group").lower() == "true"
                else:
                    group = False
                element = Benchmark.Folder(child.get("path"), group)
                if child.get("enctag") is None:
                    tag = set()
                else:
                    tag = set(child.get("enctag").split(None))
                element.add_enctags(tag)
                for grandchild in child.xpath("./encoding"):
                    element.add_encoding(grandchild.get("file"))
                for grandchild in child.xpath("./ignore"):
                    element.add_ignore(grandchild.get("prefix"))
                benchmark.add_element(element)
            for child in node.xpath("./files"):
                element = Benchmark.Files(child.get("path"))
                if child.get("enctag") is None:
                    tag = set()
                else:
                    tag = set(child.get("enctag").split(None))
                element.add_enctags(tag)
                for grandchild in child.xpath("./encoding"):
                    element.add_encoding(grandchild.get("file"))
                for grandchild in child.xpath("./add"):
                    element.add_file(grandchild.get("file"), grandchild.get("group"))
                benchmark.add_element(element)
            run.add_benchmark(benchmark)

        for node in root.xpath("./project"):
            project = Project(node.get("name"), run, run.jobs[node.get("job")])
            run.add_project(project)
            for child in node.xpath("./runspec"):
                for setting_name in compound_settings[child.get("setting")]:
                    project.add_runspec(
                        machine_name=child.get("machine"),
                        system_name=child.get("system"),
                        system_version=child.get("version"),
                        setting_name=setting_name,
                        benchmark_name=child.get("benchmark"),
                    )

            for child in node.xpath("./runtag"):
                project.add_runtag(child.get("machine"), child.get("benchmark"), child.get("tag"))

        self.validate_components(run)
        return run

    def parse_file(self, file_name: str, schema_dir: str, schema_file: str) -> etree._ElementTree:
        """
        Parse a given XML file and validate it against a given schema.

        Attributes:
            file_name (str): a string holding a path to a xml file.
            schema_dir (str): a string holding a path to the schema directory.
            schema_file (str): a string holding the name of the schema file.
        """

        try:
            schema = etree.XMLSchema(file=os.path.join(schema_dir, schema_file))
        except etree.XMLSchemaParseError as e:
            sys.stderr.write(f"*** ERROR: Failed to load schema file {schema_file}: {e}\n")
            sys.exit(1)

        try:
            doc = etree.parse(file_name)
        except (etree.XMLSyntaxError, OSError) as e:
            if isinstance(e, OSError):
                sys.stderr.write(f"*** ERROR: File '{file_name}' not found.\n")
                sys.exit(1)
            sys.stderr.write(f"*** ERROR: XML Syntax Error in file '{file_name}': {e}\n")
            sys.exit(1)

        try:
            schema.assertValid(doc)
        except etree.DocumentInvalid as e:
            sys.stderr.write(f"*** ERROR: '{file_name}' is invalid: {e}\n")
            sys.exit(1)

        return doc

    def validate_components(self, run: Runscript) -> None:
        """
        Check runscript for the existence of all required components.
        """
        # machine
        if not run.machines:
            sys.stderr.write("*** WARNING: No machine defined in runscript.\n")

        # config
        if not run.configs:
            sys.stderr.write("*** WARNING: No config defined in runscript.\n")

        # system
        if not run.systems:
            sys.stderr.write("*** WARNING: No system defined in runscript.\n")

        # setting
        for system in run.systems.values():
            if not system.settings:
                sys.stderr.write(f"*** WARNING: No setting defined for system '{system.name}-{system.version}'.\n")

        # job
        if not run.jobs:
            sys.stderr.write("*** WARNING: No job defined in runscript.\n")

        # benchmark
        if not run.benchmarks:
            sys.stderr.write("*** WARNING: No benchmark defined in runscript.\n")

        # instances
        for benchmark in run.benchmarks.values():
            if not benchmark.elements:
                sys.stderr.write(
                    f"*** WARNING: No spec or instance folders/files defined for benchmark '{benchmark.name}'.\n"
                )

        # project
        if not run.projects:
            sys.stderr.write("*** WARNING: No project defined in runscript.\n")

    def _filter_attr(self, node: etree._Element, skip: list[str]) -> dict[str, Any]:
        """
        Returns a dictionary containing all attributes of a given node.
        Attributes whose name occurs in the skip list are ignored.
        """
        attr = {}
        for key, val in node.items():
            if not key in skip:
                attr[key] = val
        return attr

    def _parse_job(self, node: etree._Element, job_type: str) -> DistJob | SeqJob:
        """
        Parses a job node and returns the corresponding job instance.
        """
        attr_filter = ["name", "timeout", "memout", "runs", "template_options"]
        kwargs = {
            "name": node.get("name"),
            "timeout": tools.xml_to_seconds_time(node.get("timeout")),
            "runs": int(node.get("runs")),
        }
        memout = node.get("memout")
        if memout is not None:
            kwargs["memout"] = int(memout)
        template_options = node.get("template_options")
        if template_options is None:
            template_options = ""
        kwargs["template_options"] = template_options

        if job_type == "distjob":
            attr = self._filter_attr(node, attr_filter + ["script_mode", "walltime", "cpt", "partition"])
            keys = list(attr.keys())
            if keys:
                sys.stderr.write(
                    f"""*** INFO: Attribute{'s' if len(keys) > 1 else ''} {', '.join(f"'{k}'" for k in keys)} in distjob '{node.get('name')}' {'are' if len(keys) > 1 else 'is'} currently unused.\n"""
                )
            kwargs.update(
                {
                    "attr": attr,
                    "script_mode": node.get("script_mode"),
                    "walltime": tools.xml_to_seconds_time(node.get("walltime")),
                    "cpt": int(node.get("cpt")),
                }
            )
            partition = node.get("partition")
            if partition is not None:
                kwargs["partition"] = partition
            return DistJob(**kwargs)  # pylint: disable=missing-kwoa
        if job_type == "seqjob":
            attr = self._filter_attr(node, attr_filter + ["parallel"])
            keys = list(attr.keys())
            if keys:
                sys.stderr.write(
                    f"""*** INFO: Attribute{'s' if len(keys) > 1 else ''} {', '.join(f"'{k}'" for k in keys)} in seqjob '{node.get('name')}' {'are' if len(keys) > 1 else 'is'} currently unused.\n"""
                )
            kwargs.update(
                {
                    "attr": attr,
                    "parallel": int(node.get("parallel")),
                }
            )
            return SeqJob(**kwargs)  # pylint: disable=missing-kwoa
        # Should never happen, checked by xml schema
        raise ValueError(f"Unknown job type: {job_type}")  # nocoverage
