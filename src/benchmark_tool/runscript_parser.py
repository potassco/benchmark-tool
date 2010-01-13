'''
Created on Jan 13, 2010

@author: Roland Kaminski
'''

class Machine:
    def __init__(self, name, cpu, memory):
        self.name   = name
        self.cpu    = cpu
        self.memory = memory

class System:
    def __init__(self, name, version, measures):
        self.name     = name
        self.version  = version
        self.measures = measures
        self.settings = {}
    def addSetting(self, setting):
        setting.system = self
        self.settings[setting.name] = setting

class Setting:
    def __init__(self, name, cmdline):
        self.name    = name
        self.cmdline = cmdline
        
class Jobspec:
    def __init__(self, name, timeout, runs):
        self.name    = name
        self.timeout = timeout
        self.runs    = runs
        
class SeqJobspec(Jobspec):
    def __init__(self, name, timeout, runs, parallel):
        Jobspec.__init__(self, name, timeout, runs)
        self.parallel = parallel
           
class PbsJobspec(Jobspec):
    def __init__(self, name, timeout, runs, ppn, procs, script_mode, walltime):
        Jobspec.__init__(self, name, timeout, runs)
        self.ppn         = ppn
        self.procs       = procs
        self.script_mode = script_mode
        self.walltime    = walltime

class Config:
    def __init__(self, name, template, output):
        self.name     = name
        self.template = template
        self.output   = output 

class Benchmark:
    def __init__(self, name):
        self.name     = name
        self.elements = []
    def addElement(self, element):
        self.elements.append(element)

class File:
    def __init__(self, path):
        self.path = path

class Files:
    def __init__(self, path):
        self.path    = path
        self.ignores = set()
    def addIgnore(self, ignore):
        self.ignores.add(ignore)

class Runspec:
    def __init__(self, name, machine, setting, config, jobspec, benchmark):
        self.name    = name 
        self.machine = machine
        self.setting = setting
        self.config  = config
        self.jobspec = jobspec

class Runscript:
    def __init__(self):
        self.runspecs   = {}
        self.machines   = {}
        self.systems    = {}
        self.jobspecs   = {} 
        self.configs    = {} 
        self.benchmarks = {}
    
    
    def addRunspec(self, name, machine, system, version, setting, config, jobspec, benchmark):
        runspec = Runspec(name,
                          self.machines[machine],
                          self.systems[(system,version)].settings[setting], 
                          self.configs[config], 
                          self.jobspecs[jobspec], 
                          self.benchmarks[benchmark])
        self.runspecs[runspec.name] = runspec
    
    def addMachine(self, machine):
        self.machines[machine.name] = machine
    
    def addSystem(self, system):
        self.systems[(system.name, system.version)] = system
        
    def addJobspec(self, jobspec):
        self.jobspecs[jobspec.name] = jobspec
        
    def addConfig(self, config):
        self.configs[config.name] = config

    def addBenchmark(self, benchmark):
        self.benchmarks[benchmark.name] = benchmark

class RunscriptParser:
    def __init__(self):
        pass

    def parse(self, fileName):
        from lxml import etree
        from StringIO import StringIO
        
        schemadoc = etree.parse(StringIO("""
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <!-- the runscript -->
    <xs:complexType name="runscriptType">
        <xs:choice minOccurs="0" maxOccurs="unbounded">
            <xs:element name="machine" type="machineType"/>
            <xs:element name="system" type="systemType"/>
            <xs:element name="setting" type="settingType"/>
            <xs:element name="jobspec" type="jobspecType"/>
            <xs:element name="config" type="configType"/>
            <xs:element name="benchmark" type="benchmarkType"/>
            <xs:element name="runspec" type="runspecType"/>
        </xs:choice>
    </xs:complexType>

    <!-- a machine -->
    <xs:complexType name="machineType">
        <xs:attribute name="name" type="xs:Name" use="required"/>
        <xs:attribute name="cpu" type="xs:token" use="required"/>
        <xs:attribute name="memory" type="xs:token" use="required"/>
    </xs:complexType>

    <!-- a system -->
    <xs:complexType name="systemType">
        <xs:attribute name="name" type="xs:Name" use="required"/>
        <xs:attribute name="version" type="versionType" use="required"/>
        <xs:attribute name="measures" type="xs:Name" use="required"/>
    </xs:complexType>

    <!-- per system settings -->
    <xs:complexType name="settingType">
        <xs:attribute name="name" type="xs:Name" use="required"/>
        <xs:attribute name="system" type="xs:Name" use="required"/>
        <xs:attribute name="cmdline" type="xs:string" use="required"/>
    </xs:complexType>
    
    <!-- a jobspec -->
    <xs:complexType name="jobspecType">
        <xs:choice>
            <xs:element name="sequential">
                <xs:complexType>
                    <xs:attribute name="parallel" type="xs:positiveInteger" use="required"/>
                </xs:complexType>
            </xs:element>
            <xs:element name="pbs">
                <xs:complexType>
                    <xs:attribute name="ppn" type="xs:positiveInteger" use="required"/>
                    <xs:attribute name="procs" use="required">
                        <xs:simpleType>
                            <xs:list itemType="xs:integer"/>
                         </xs:simpleType>
                    </xs:attribute>
                    <xs:attribute name="script_mode" use="required">
                        <xs:simpleType>
                            <xs:restriction base="xs:string">
                                <xs:enumeration value="single"/>
                                <xs:enumeration value="multi"/>
                                <xs:enumeration value="timeout"/>
                            </xs:restriction>
                         </xs:simpleType>
                    </xs:attribute>
                    <xs:attribute name="walltime" type="timeType" use="required"/>
                </xs:complexType>
            </xs:element>
        </xs:choice>
        <xs:attribute name="name" type="xs:Name" use="required"/>
        <xs:attribute name="timeout" type="timeType" use="required"/>
        <xs:attribute name="runs" type="xs:positiveInteger" use="required"/>
    </xs:complexType>

    <!-- a config -->
    <xs:complexType name="configType">
        <xs:attribute name="name" type="xs:Name" use="required"/>
        <xs:attribute name="template" type="xs:string" use="required"/>
        <xs:attribute name="output" type="xs:string" use="required"/>
    </xs:complexType>
    
    <!-- a benchmark -->
    <xs:complexType name="benchmarkType">
        <xs:sequence minOccurs="0" maxOccurs="unbounded">
            <xs:choice>
                <xs:element name="file">
                    <xs:complexType>
                        <xs:attribute name="path" type="xs:string" use="required"/>
                    </xs:complexType>
                </xs:element>
                <xs:element name="files">
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
        <xs:attribute name="name" type="xs:Name" use="required"/>
    </xs:complexType>

    <!-- a runspec -->
    <xs:complexType name="runspecType">
        <xs:attribute name="name" type="xs:Name" use="required"/>
        <xs:attribute name="system" type="xs:Name" use="required"/>
        <xs:attribute name="version" type="versionType" use="required"/>
        <xs:attribute name="setting" type="xs:Name" use="required"/>
        <xs:attribute name="machine" type="xs:Name" use="required"/>
        <xs:attribute name="config" type="xs:Name" use="required"/>
        <xs:attribute name="benchmark" type="xs:Name" use="required"/>
        <xs:attribute name="jobspec" type="xs:Name" use="required"/>
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
    
    <!-- the root element -->
    <xs:element name="runscript" type="runscriptType">
        <!-- machine keys -->
        <xs:keyref name="machineRef" refer="machineKey">
            <xs:selector xpath="runspec"/>
            <xs:field xpath="@machine"/>
        </xs:keyref>
        <xs:key name="machineKey">
            <xs:selector xpath="machine"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- benchmark keys -->
        <xs:keyref name="benchmarkRef" refer="benchmarkKey">
            <xs:selector xpath="runspec"/>
            <xs:field xpath="@benchmark"/>
        </xs:keyref>
        <xs:key name="benchmarkKey">
            <xs:selector xpath="benchmark"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- system keys -->
        <xs:keyref name="systemRef" refer="systemKey">
            <xs:selector xpath="runspec"/>
            <xs:field xpath="@system"/>
            <xs:field xpath="@version"/>
        </xs:keyref>
        <xs:key name="systemKey">
            <xs:selector xpath="system"/>
            <xs:field xpath="@name"/>
            <xs:field xpath="@version"/>
        </xs:key>
        <!-- setting keys -->
        <xs:keyref name="settingRef" refer="settingKey">
            <xs:selector xpath="runspec"/>
            <xs:field xpath="@system"/>
            <xs:field xpath="@setting"/>
        </xs:keyref>
        <xs:key name="settingKey">
            <xs:selector xpath="setting"/>
            <xs:field xpath="@system"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- config keys -->
        <xs:keyref name="configRef" refer="configKey">
            <xs:selector xpath="runspec"/>
            <xs:field xpath="@config"/>
        </xs:keyref>
        <xs:key name="configKey">
            <xs:selector xpath="config"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- jobspec keys -->
        <xs:keyref name="jobspecRef" refer="jobspecKey">
            <xs:selector xpath="runspec"/>
            <xs:field xpath="@jobspec"/>
        </xs:keyref>
        <xs:key name="jobspecKey">
            <xs:selector xpath="jobspec"/>
            <xs:field xpath="@name"/>
        </xs:key>
        <!-- runspec names have to be unique -->
        <xs:unique name="runspecKey">
            <xs:selector xpath="runspec"/>
            <xs:field xpath="@name"/>
        </xs:unique>
    </xs:element>
</xs:schema>
"""))
        schema = etree.XMLSchema(schemadoc)

        doc = etree.parse(open(fileName))
        schema.assertValid(doc)
        
        run = Runscript()
        
        for node in doc.getroot().xpath("./machine"):
            machine = Machine(node.get("name"), node.get("cpu"), node.get("memory"))
            run.addMachine(machine)
    
        for node in doc.getroot().xpath("./system"):
            system = System(node.get("name"), node.get("version"), node.get("measures"))
            for child in doc.getroot().xpath("./setting[@system='" + system.name + "']"):
                setting = Setting(child.get("name"), child.get("cmdline"))
                system.addSetting(setting)
            run.addSystem(system)
            
        for node in doc.getroot().xpath("./jobspec"):
            name    = node.get("name")
            timeout = node.get("timeout")
            runs    = node.get("runs")
            pbs = node.xpath("./pbs")
            if len(pbs) > 0:
                child = pbs[0]
                jobspec = PbsJobspec(name, timeout, runs, child.get("ppn"), child.get("procs"), child.get("script_mode"), child.get("walltime"))
            else:
                child = node.xpath("./sequential")[0]
                jobspec = SeqJobspec(name, timeout, runs, child.get("parallel"))
            run.addJobspec(jobspec)
        
        for node in doc.getroot().xpath("./config"):
            config = Config(node.get("name"), node.get("template"), node.get("output"))
            run.addConfig(config)
        
        for node in doc.getroot().xpath("./benchmark"):
            benchmark = Benchmark(node.get("name"))
            for child in node.xpath("./files"):
                element = Files(child.get("path"))
                for grandchild in child.xpath("./ignore"):
                    element.addIgnore(grandchild.get("prefix"))
                benchmark.addElement(element)
            for child in node.xpath("./file"):
                element = File(child.get("path"))
                benchmark.addElement(element)
            run.addBenchmark(benchmark)
        
        for node in doc.getroot().xpath("./runspec"):
            run.addRunspec(node.get("name"), 
                           node.get("machine"), 
                           node.get("system"), 
                           node.get("version"), 
                           node.get("setting"), 
                           node.get("config"), 
                           node.get("jobspec"), 
                           node.get("benchmark"))
