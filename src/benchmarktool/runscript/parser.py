"""
This module contains an XML-parser for run script specifications. 
It reads and converts a given specification and returns its 
representation in form of python classes.
"""

__author__ = "Roland Kaminski"

from benchmarktool.runscript.runscript import Runscript, Project, Benchmark, Config, System, Setting, PbsJob, SeqJob, Machine
import benchmarktool.tools as tools

class Parser:
    """
    A parser to parse xml runscript specifications.
    """   
    def __init__(self):
        """
        Initializes the parser.
        """
        pass
    
    def parse(self, fileName):
        """
        Parse a given runscript and return its representation 
        in form of an instance of class Runscript.
        
        Keyword arguments:
        fileName -- a string holding a path to a xml file  
        """
        from lxml import etree
        from io import StringIO
        
        schemadoc = etree.parse(StringIO("""\
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
            <xs:element name="pbsjob" type="pbsjobType"/>
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
                    <xs:attribute name="name" type="nameType" use="required"/>
                    <xs:attribute name="tag">
                        <xs:simpleType>
                            <xs:list itemType="nameType"/>
                        </xs:simpleType>
                    </xs:attribute>
                    <xs:attribute name="ppn" type="xs:positiveInteger"/>
                    <xs:attribute name="procs">
                        <xs:simpleType>
                            <xs:list itemType="xs:integer"/>
                         </xs:simpleType>
                    </xs:attribute>
                    <xs:attribute name="pbstemplate" type="xs:string"/>
                    <xs:anyAttribute processContents="lax"/>
                </xs:complexType>
            </xs:element>
        </xs:choice>
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="version" type="versionType" use="required"/>
        <xs:attribute name="measures" type="nameType" use="required"/>
        <xs:attribute name="config" type="nameType" use="required"/>
    </xs:complexType>

    <!-- generic attributes for jobs-->
    <xs:attributeGroup name="jobAttr">
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="timeout" type="timeType" use="required"/>
        <xs:attribute name="runs" type="xs:positiveInteger" use="required"/>
        <xs:anyAttribute processContents="lax"/>
    </xs:attributeGroup>
    
    <!-- a seqjob -->
    <xs:complexType name="seqjobType">
        <xs:attributeGroup ref="jobAttr"/>
        <xs:attribute name="parallel" type="xs:positiveInteger" use="required"/>
    </xs:complexType>
    
    <!-- a pbsjob -->
    <xs:complexType name="pbsjobType">
        <xs:attributeGroup ref="jobAttr"/>
        <xs:attribute name="script_mode" use="required">
            <xs:simpleType>
                <xs:restriction base="xs:string">
                    <xs:enumeration value="single"/>
                    <xs:enumeration value="timeout"/>
                </xs:restriction>
             </xs:simpleType>
        </xs:attribute>
        <xs:attribute name="walltime" type="timeType" use="required"/>
    </xs:complexType>
    
    <!-- a config -->
    <xs:complexType name="configType">
        <xs:attribute name="name" type="nameType" use="required"/>
        <xs:attribute name="template" type="xs:string" use="required"/>
    </xs:complexType>
    
    <!-- a benchmark -->
    <xs:complexType name="benchmarkType">
        <xs:sequence minOccurs="0" maxOccurs="unbounded">
            <xs:choice>
                <xs:element name="files">
                    <xs:complexType>
                        <xs:choice minOccurs="0" maxOccurs="unbounded">
                            <xs:element name="add">
                                <xs:complexType>
                                    <xs:attribute name="file" type="xs:string" use="required"/>
                                </xs:complexType>
                            </xs:element>
                        </xs:choice>
                        <xs:attribute name="path" type="xs:string" use="required"/>
                    </xs:complexType>
                </xs:element>
                <xs:element name="folder">
                    <xs:complexType>
                        <xs:sequence minOccurs="0" maxOccurs="unbounded">
                            <xs:element name="ignore">
                                <xs:complexType>
                                    <xs:attribute name="prefix" type="xs:string" use="required"/>
                                </xs:complexType>
                            </xs:element>
                        </xs:sequence>
                        <xs:attribute name="path" type="xs:string" use="required"/>
                    </xs:complexType>
                </xs:element>
            </xs:choice>
        </xs:sequence>
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
            <xs:pattern value="[0-9]+(:[0-9]+(:[0-9]+)?)?"/>
        </xs:restriction>
    </xs:simpleType>
    
    <xs:simpleType name="tagrefType">
        <xs:restriction base="xs:string">
            <xs:pattern value="(\*all\*)|([A-Za-z_\-0-9]+([ ]*[A-Za-z_\-0-9]+)*)([ ]*\|[ ]*([A-Za-z_\-0-9]+([ ]*[A-Za-z_\-0-9]+)*))*"/>
        </xs:restriction>
    </xs:simpleType>
    
    <xs:simpleType name="nameType">
        <xs:restriction base="xs:string">
            <xs:pattern value="[A-Za-z_\-0-9]*"/>
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
            <xs:selector xpath="seqjob|pbsjob"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- project keys -->
        <xs:unique name="projectKey">
            <xs:selector xpath="project"/>
            <xs:field xpath="@name"/>
        </xs:unique>
    </xs:element>
</xs:schema>
"""))
        schema = etree.XMLSchema(schemadoc)

        doc = etree.parse(open(fileName))
        schema.assertValid(doc)
        
        root = doc.getroot()
        run  = Runscript(root.get("output"))

        for node in root.xpath("./pbsjob"):
            attr = self._filterAttr(node, ["name", "timeout", "runs", "ppn", "procs", "script_mode", "walltime"])
            job = PbsJob(node.get("name"), tools.xmlTime(node.get("timeout")), int(node.get("runs")), node.get("script_mode"), tools.xmlTime(node.get("walltime")), attr)
            run.addJob(job)

        for node in root.xpath("./seqjob"):
            attr = self._filterAttr(node, ["name", "timeout", "runs", "parallel"])
            job = SeqJob(node.get("name"), tools.xmlTime(node.get("timeout")), int(node.get("runs")), int(node.get("parallel")), attr)
            run.addJob(job)
        
        for node in root.xpath("./machine"):
            machine = Machine(node.get("name"), node.get("cpu"), node.get("memory"))
            run.addMachine(machine)

        for node in root.xpath("./config"):
            config = Config(node.get("name"), node.get("template"))
            run.addConfig(config)
        
        compoundSettings = {}
        sytemOrder = 0 
        for node in root.xpath("./system"):
            system = System(node.get("name"), node.get("version"), node.get("measures"), sytemOrder)
            settingOrder = 0
            for child in node.xpath("setting"):
                attr = self._filterAttr(child, ["name", "cmdline", "tag"])
                compoundSettings[child.get("name")] = []
                if "procs" in attr:
                    procs = [int(proc) for proc in attr["procs"].split(None)]
                    del attr["procs"]
                else: procs = [None]
                if "ppn" in attr: 
                    ppn = int(attr["ppn"])
                    del attr["ppn"]
                else: ppn = None
                if "pbstemplate" in attr:
                    pbstemplate = attr["pbstemplate"]
                    del attr["pbstemplate"]
                else: pbstemplate = None
                if child.get("tag") == None: tag = set()
                else: tag = set(child.get("tag").split(None))
                for num in procs:
                    name = child.get("name")
                    if num != None: 
                        name += "-n{0}".format(num)
                    compoundSettings[child.get("name")].append(name)
                    setting = Setting(name, child.get("cmdline"), tag, settingOrder, num, ppn, pbstemplate, attr)
                    system.addSetting(setting)
                    settingOrder += 1

            run.addSystem(system, node.get("config"))
            sytemOrder += 1
            
        for node in root.xpath("./benchmark"):
            benchmark = Benchmark(node.get("name"))
            for child in node.xpath("./folder"):
                element = Benchmark.Folder(child.get("path"))
                for grandchild in child.xpath("./ignore"):
                    element.addIgnore(grandchild.get("prefix"))
                benchmark.addElement(element)
            for child in node.xpath("./files"):
                element = Benchmark.Files(child.get("path"))
                for grandchild in child.xpath("./add"):
                    element.addFile(grandchild.get("file"))
                benchmark.addElement(element)
            run.addBenchmark(benchmark)
        
        for node in root.xpath("./project"):
            project = Project(node.get("name"))
            run.addProject(project, node.get("job"))
            for child in node.xpath("./runspec"):
                for setting in compoundSettings[child.get("setting")]: 
                    project.addRunspec(child.get("machine"),
                                       child.get("system"),
                                       child.get("version"),
                                       setting,
                                       child.get("benchmark"))
                
            for child in node.xpath("./runtag"):
                project.addRuntag(child.get("machine"), 
                                  child.get("benchmark"),
                                  child.get("tag"))
        
        return run
    
    def _filterAttr(self, node, skip):
        """
        Returns a dictionary containing all attributes of a given node.
        Attributes whose name occurs in the set skip are ignored.
        """
        attr = {}
        for key, val in node.items():
            if not key in skip:
                attr[key] = val  
        return attr
