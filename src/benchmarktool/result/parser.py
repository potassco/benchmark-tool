'''
Created on Jan 19, 2010

@author: Roland Kaminski
'''

from lxml import etree
from benchmarktool import tools

class Result:
    def __init__(self):
        self.machines   = {}
        self.configs    = {}
        self.systems    = {}
        self.jobs       = {}
        self.benchmarks = {}
        self.projects   = {}

class Machine:
    def __init__(self, name, cpu, memory):
        self.name   = name
        self.cpu    = cpu
        self.memory = memory 

class Config:
    def __init__(self, name, template):
        self.name     = name
        self.template = template

class System:
    def __init__(self, name, version, config, measures):
        self.name     = name
        self.version  = version
        self.config   = config
        self.measures = measures
        self.settings = {}

class Setting:
    def __init__(self, system, name, cmdline, tag, attr):
        self.name    = name
        self.cmdline = cmdline
        self.tag     = tag
        self.attr    = attr

class Job:
    def __init__(self, name, timeout, runs, attrib):
        self.name    = name
        self.timeout = timeout
        self.runs    = runs
        self.attrib  = attrib

class SeqJob(Job):
    def __init__(self, name, timeout, runs, parallel, attrib):
        Job.__init__(self, name, timeout, runs, attrib)
        self.parallel = parallel

class Benchmark:
    def __init__(self, name):
        self.name    = name
        self.classes = {}

class Class:
    def __init__(self, name, id):
        self.name      = name
        self.id        = id
        self.instances = {}

class Instance:
    def __init__(self, name, id):
        self.name      = name
        self.id        = id

class Project:
    def __init__(self, name, job):
        self.name     = name
        self.job      = job
        self.runspecs = [] 

class Runspec():
    def __init__(self, system, machine, benchmark):
        self.system       = system
        self.machine      = machine
        self.benchmark    = benchmark
        self.classresults = []

class ClassResult:
    def __init__(self, benchclass):
        self.benchclass  = benchclass
        self.instresults = []

class InstanceResult:
    def __init__(self, benchinst):
        self.benchclass  = benchinst
        self.runs        = []

class Run:
    def __init__(self, instresult, number):
        self.instresult = instresult
        self.number     = number
        self.measures   = {}

class Parser:
    def __init__(self):
        pass
    
    def parse(self, infile):
        # to reduce memory consumption especially for large result files
        # do not use the full blown etree representation 
        parser = etree.XMLParser(target=self)
        etree.parse(infile, parser)
        
    def start(self, tag, attrib):
        if tag == "result":
            self.result = Result()
        elif tag == "machine":
            machine =  Machine(attrib["name"], attrib["cpu"], attrib["memory"])
            self.result.machines[machine.name] = machine 
        elif tag == "config":
            config = Config(attrib["name"], attrib["template"])
            self.result.configs[config.name] = config 
        elif tag == "system":
            self.system = System(attrib["name"], attrib["version"], attrib["config"], attrib["measures"])
            self.result.systems[(self.system.name, self.system.version)] = self.system
        elif tag == "setting":
            tag     = attrib.pop("tag", None)
            name    = attrib.pop("name")
            cmdline = attrib.pop("cmdline")
            setting = Setting(self.system, name, cmdline, tag, attrib)
            self.system.settings[name] = setting
        elif tag == "seqjob":
            name     = attrib.pop("name")
            timeout  = tools.xmlTime(attrib.pop("timeout"))
            runs     = int(attrib.pop("runs"))
            parallel = int(attrib.pop("parallel"))
            job = SeqJob(name, timeout, runs, parallel, attrib)
            self.result.jobs[job.name] = job
        elif tag == "benchmark":
            self.benchscope = True 
            self.benchmark = Benchmark(attrib["name"])
            self.result.benchmarks[self.benchmark.name] = self.benchmark
        elif tag == "class" and self.benchscope:
            self.benchclass = Class(attrib["name"], int(attrib["id"]))
            self.benchmark.classes[self.benchclass.id] = self.benchclass
        elif tag == "instance" and self.benchscope:
            instance = Instance(attrib["name"], int(attrib["id"]))
            self.benchclass.instances[instance.id] = instance
        elif tag == "project":
            self.project = Project(attrib["name"], attrib["job"])
            self.result.projects[self.project.name] = self.project
        elif tag == "runspec":
            self.benchscope = False
            self.runspec = Runspec(self.result.systems[(attrib["system"], attrib["version"])], self.result.machines[attrib["machine"]], self.result.benchmarks[attrib["benchmark"]])
            self.project.runspecs.append(self.runspec)
        elif tag == "class" and not self.benchscope:
            benchclass = self.runspec.benchmark.classes[int(attrib["id"])]
            self.classresult = ClassResult(benchclass)
            self.runspec.classresults.append(self.classresult)
        elif tag == "instance" and not self.benchscope:
            benchinst = self.classresult.benchclass.instances[int(attrib["id"])]
            self.instresult = InstanceResult(benchinst)
        elif tag == "run" and not self.benchscope:
            self.run = Run(self.instresult, int(attrib["number"]))
            self.instresult.runs.append(self.run)
        elif tag == "measure":
            self.run.measures[attrib["name"]] = (attrib["type"], attrib["val"]) 
        else: print tag, attrib 
    
    def close(self):
        pass
