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
)

try:
    from StringIO import StringIO  # type: ignore[import-not-found]
except ModuleNotFoundError:
    from io import StringIO


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

        schemadoc = etree.parse(
            StringIO(
                """\
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <!-- the runscript -->
    <xs:complexType name="runscriptType">
        <xs:choice minOccurs="0" maxOccurs="unbounded">
            <xs:element name="machine" type="machineType"/>
            <xs:element name="system" type="systemType">
                <!-- setting keys have to be unique per system/version-->
                <!-- unfortunately i have found no way to create a link between settings and systems -->
                <!-- schematron should be able to do this but the lxml implementation seems to be incomplete-->
                <xs:unique name="settingKey">
                    <xs:selector xpath="setting"/>
                    <xs:field xpath="@name"/>
                </xs:unique>
            </xs:element>
            <xs:element name="config" type="configType"/>
            <xs:element name="benchmark" type="benchmarkType"/>
            <xs:element name="distjob" type="distjobType"/>
            <xs:element name="seqjob" type="seqjobType"/>
            <xs:element name="project" type="projectType"/>
        </xs:choice>
        <xs:attribute name="output" type="xs:string" use="required"/>
    </xs:complexType>

    <!-- a project -->
    <xs:complexType name="projectType">
        <xs:choice minOccurs="0" maxOccurs="unbounded">
            <xs:element name="runspec" type="runspecType"/>
            <xs:element name="runtag" type="runtagType"/>
        </xs:choice>
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="job" type="nameType" use="required"/>
    </xs:complexType>

    <!-- a machine -->
    <xs:complexType name="machineType">
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="cpu" type="xs:token" use="required"/>
        <xs:attribute name="memory" type="xs:token" use="required"/>
    </xs:complexType>

    <!-- a system -->
    <xs:complexType name="systemType">
        <xs:choice minOccurs="1" maxOccurs="unbounded">
            <xs:element name="setting">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="encoding" minOccurs="0" maxOccurs="unbounded">
                            <xs:complexType>
                                <xs:attribute name="file" type="xs:string" use="required"/>
                                <xs:attribute name="enctag">
                                    <xs:simpleType>
                                        <xs:list itemType="nameType"/>
                                    </xs:simpleType>
                                </xs:attribute>
                            </xs:complexType>
                        </xs:element>
                    </xs:sequence>
                    <xs:attribute name="name" type="nameType" use="required"/>
                    <xs:attribute name="cmdline" type="xs:string"/>
                    <xs:attribute name="cmdline_post" type="xs:string"/>
                    <xs:attribute name="tag">
                        <xs:simpleType>
                            <xs:list itemType="nameType"/>
                        </xs:simpleType>
                    </xs:attribute>
                    <xs:attribute name="dist_template" type="xs:string"/>
                    <xs:attribute name="dist_options" type="xs:string"/>
                    <xs:anyAttribute processContents="lax"/>
                </xs:complexType>
            </xs:element>
        </xs:choice>
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="version" type="versionType" use="required"/>
        <xs:attribute name="measures" type="nameType" use="required"/>
        <xs:attribute name="config" type="nameType" use="required"/>
        <xs:attribute name="cmdline" type="xs:string"/>
        <xs:attribute name="cmdline_post" type="xs:string"/>
    </xs:complexType>

    <!-- generic attributes for jobs-->
    <xs:attributeGroup name="jobAttr">
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="timeout" type="timeType" use="required"/>
        <xs:attribute name="runs" type="xs:positiveInteger" use="required"/>
        <xs:attribute name="memout" type="xs:positiveInteger"/>
        <xs:attribute name="template_options" type="xs:string"/>
        <xs:anyAttribute processContents="lax"/>
    </xs:attributeGroup>

    <!-- a seqjob -->
    <xs:complexType name="seqjobType">
        <xs:attributeGroup ref="jobAttr"/>
        <xs:attribute name="parallel" type="xs:positiveInteger" use="required"/>
    </xs:complexType>

    <!-- a distjob -->
    <xs:complexType name="distjobType">
        <xs:attributeGroup ref="jobAttr"/>
        <xs:attribute name="script_mode" use="required">
            <xs:simpleType>
                <xs:restriction base="xs:string">
                    <xs:enumeration value="multi"/>
                    <xs:enumeration value="timeout"/>
                </xs:restriction>
             </xs:simpleType>
        </xs:attribute>
        <xs:attribute name="walltime" type="timeType" use="required"/>
        <xs:attribute name="cpt" type="xs:positiveInteger" use="required"/>
        <xs:attribute name="partition" type="xs:string"/>
    </xs:complexType>

    <!-- a config -->
    <xs:complexType name="configType">
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="template" type="xs:string" use="required"/>
    </xs:complexType>

    <!-- a benchmark -->
    <xs:complexType name="benchmarkType">
        <xs:choice minOccurs="0" maxOccurs="unbounded">
            <xs:element name="files">
                <xs:complexType>
                    <xs:choice minOccurs="0" maxOccurs="unbounded">
                        <xs:element name="add">
                            <xs:complexType>
                                <xs:attribute name="file" type="xs:string" use="required"/>
                                <xs:attribute name="group" type="xs:string"/>
                            </xs:complexType>
                        </xs:element>
                        <xs:element name="encoding">
                            <xs:complexType>
                                <xs:attribute name="file" type="xs:string" use="required"/>
                            </xs:complexType>
                        </xs:element>
                    </xs:choice>
                    <xs:attribute name="path" type="xs:string" use="required"/>
                    <xs:attribute name="enctag">
                        <xs:simpleType>
                            <xs:list itemType="nameType"/>
                        </xs:simpleType>
                    </xs:attribute>
                </xs:complexType>
            </xs:element>
            <xs:element name="folder">
                <xs:complexType>
                    <xs:choice minOccurs="0" maxOccurs="unbounded">
                        <xs:element name="ignore">
                            <xs:complexType>
                                <xs:attribute name="prefix" type="xs:string" use="required"/>
                            </xs:complexType>
                        </xs:element>
                        <xs:element name="encoding">
                            <xs:complexType>
                                <xs:attribute name="file" type="xs:string" use="required"/>
                            </xs:complexType>
                        </xs:element>
                    </xs:choice>
                    <xs:attribute name="path" type="xs:string" use="required"/>
                    <xs:attribute name="group" type="xs:boolean"/>
                    <xs:attribute name="enctag">
                        <xs:simpleType>
                            <xs:list itemType="nameType"/>
                        </xs:simpleType>
                    </xs:attribute>
                </xs:complexType>
            </xs:element>
        </xs:choice>
        <xs:attribute name="name" type="nameType" use="required"/>
    </xs:complexType>

    <!-- common attributes for runspec/runtag -->
    <xs:attributeGroup name="runAttr">
        <xs:attribute name="machine" type="nameType" use="required"/>
        <xs:attribute name="benchmark" type="nameType" use="required"/>
    </xs:attributeGroup>

    <!-- a runspec -->
    <xs:complexType name="runspecType">
        <xs:attribute name="system" type="nameType" use="required"/>
        <xs:attribute name="version" type="versionType" use="required"/>
        <xs:attribute name="setting" type="nameType" use="required"/>
        <xs:attributeGroup ref="runAttr"/>
    </xs:complexType>

    <!-- a runtag -->
    <xs:complexType name="runtagType">
        <xs:attributeGroup ref="runAttr"/>
        <xs:attribute name="tag" type="tagrefType" use="required"/>
    </xs:complexType>

    <!-- simple types used througout the above definitions -->
    <xs:simpleType name="versionType">
        <xs:restriction base="xs:string">
            <xs:pattern value="[0-9a-zA-Z._-]+"/>
        </xs:restriction>
    </xs:simpleType>

    <xs:simpleType name="timeType">
        <xs:restriction base="xs:string">
            <xs:pattern value="([0-9]+)|([0-9]+d)?[ ]*([0-9]+h)?[ ]*([0-9]+m)?[ ]*([0-9]+s)?"/>
        </xs:restriction>
    </xs:simpleType>

    <xs:simpleType name="tagrefType">
        <xs:restriction base="xs:string">
            <xs:pattern value="(\\*all\\*)|([A-Za-z_\\-0-9]+([ ]*[A-Za-z_\\-0-9]+)*)([ ]*\\|[ ]*([A-Za-z_\\-0-9]+([ ]*[A-Za-z_\\-0-9]+)*))*"/>
        </xs:restriction>
    </xs:simpleType>

    <xs:simpleType name="nameType">
        <xs:restriction base="xs:string">
            <xs:pattern value="[A-Za-z_\\-0-9]*"/>
        </xs:restriction>
    </xs:simpleType>

    <!-- the root element -->
    <xs:element name="runscript" type="runscriptType">
        <!-- machine keys -->
        <xs:keyref name="machineRef" refer="machineKey">
            <xs:selector xpath="project/runspec|project/runall"/>
            <xs:field xpath="@machine"/>
        </xs:keyref>
        <xs:key name="machineKey">
            <xs:selector xpath="machine"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- benchmark keys -->
        <xs:keyref name="benchmarkRef" refer="benchmarkKey">
            <xs:selector xpath="project/runspec|project/runall"/>
            <xs:field xpath="@benchmark"/>
        </xs:keyref>
        <xs:key name="benchmarkKey">
            <xs:selector xpath="benchmark"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- system keys -->
        <xs:keyref name="systemRef" refer="systemKey">
            <xs:selector xpath="project/runspec"/>
            <xs:field xpath="@system"/>
            <xs:field xpath="@version"/>
        </xs:keyref>
        <xs:key name="systemKey">
            <xs:selector xpath="system"/>
            <xs:field xpath="@name"/>
            <xs:field xpath="@version"/>
        </xs:key>
        <!-- config keys -->
        <xs:keyref name="configRef" refer="configKey">
            <xs:selector xpath="system"/>
            <xs:field xpath="@config"/>
        </xs:keyref>
        <xs:key name="configKey">
            <xs:selector xpath="config"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- config keys -->
        <xs:keyref name="jobRef" refer="jobKey">
            <xs:selector xpath="project"/>
            <xs:field xpath="@job"/>
        </xs:keyref>
        <xs:key name="jobKey">
            <xs:selector xpath="seqjob|distjob"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- project keys -->
        <xs:unique name="projectKey">
            <xs:selector xpath="project"/>
            <xs:field xpath="@name"/>
        </xs:unique>
    </xs:element>
</xs:schema>
"""
            )
        )
        schema = etree.XMLSchema(schemadoc)

        try:
            doc = etree.parse(file_name)
        except (etree.XMLSyntaxError, OSError) as e:
            if isinstance(e, OSError):
                sys.stderr.write(f"*** ERROR: Runscript file '{file_name}' not found.\n")
                sys.exit(1)
            sys.stderr.write(f"*** ERROR: XML Syntax Error in runscript: {e}\n")
            sys.exit(1)

        try:
            schema.assertValid(doc)
        except etree.DocumentInvalid as e:
            sys.stderr.write(f"*** ERROR: Invalid runscript file: {e}\n")
            sys.exit(1)

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
                sys.stderr.write(f"*** WARNING: No instance folder/files defined for benchmark '{benchmark.name}'.\n")

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
