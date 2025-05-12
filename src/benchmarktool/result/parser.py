'''
Created on Jan 19, 2010

@author: Roland Kaminski
'''

from lxml import etree
from benchmarktool import tools
from benchmarktool.result.result import Benchmark, Class, ClassResult, Config, Instance, InstanceResult, Machine, Project, Result, Run, Runspec, SeqJob, PbsJob, Setting, System

class Parser:
    """
    A parser to parse XML result files.
    """    
    def __init__(self):
        """
        Initializes the parser.
        """
        self.benchclass   = None
        self.systemOrder  = None
        self.result       = None
        self.system       = None
        self.settingOrder = None
        self.benchscope   = None
        self.benchmark    = None
        self.classresult  = None
        self.instresult   = None
        self.runspec      = None
        self.project      = None
        self.run          = None
    
    def parse(self, infile):
        """
        Parse a given result file and return its representation 
        in form of an instance of class Result.
        
        Keyword arguments:
        infile -- The file to parse  
        """
        # to reduce memory consumption especially for large result files
        # do not use the full blown etree representation 
        parser = etree.XMLParser(target=self)
        etree.parse(infile, parser)
        return self.result
        
    def start(self, tag, attrib):
        """
        This method is called for every opening XML tag.
        
        tag    - The name of the tag
        attrib - The attributes of the tag  
        """
        if tag == "result":
            self.systemOrder = 0
            self.result = Result()
        elif tag == "machine":
            machine =  Machine(attrib["name"], attrib["cpu"], attrib["memory"])
            self.result.machines[machine.name] = machine 
        elif tag == "config":
            config = Config(attrib["name"], attrib["template"])
            self.result.configs[config.name] = config 
        elif tag == "system":
            self.system = System(attrib["name"], attrib["version"], attrib["config"], attrib["measures"], self.systemOrder)
            self.result.systems[(self.system.name, self.system.version)] = self.system
            self.systemOrder += 1
            self.settingOrder = 0
        elif tag == "setting":
            tag     = attrib.pop("tag", None)
            name    = attrib.pop("name")
            cmdline = attrib.pop("cmdline")
            setting = Setting(self.system, name, cmdline, tag, self.settingOrder, attrib)
            self.system.settings[name] = setting
            self.settingOrder += 1
        elif tag == "seqjob":
            name     = attrib.pop("name")
            timeout  = tools.xml_time(attrib.pop("timeout"))
            runs     = int(attrib.pop("runs"))
            parallel = int(attrib.pop("parallel"))
            job = SeqJob(name, timeout, runs, parallel, attrib)
            self.result.jobs[job.name] = job
        elif tag == "pbsjob":
            name        = attrib.pop("name")
            timeout     = tools.xml_time(attrib.pop("timeout"))
            runs        = int(attrib.pop("runs"))
            script_mode = attrib.pop("script_mode")
            walltime    = attrib.pop("walltime")
            job = PbsJob(name, timeout, runs, script_mode, walltime, attrib)
            self.result.jobs[job.name] = job
            pass
        elif tag == "benchmark":
            self.benchscope = True 
            self.benchmark = Benchmark(attrib["name"])
            self.result.benchmarks[self.benchmark.name] = self.benchmark
        elif tag == "class" and self.benchscope:
            self.benchclass = Class(self.benchmark, attrib["name"], int(attrib["id"]))
            self.benchmark.classes[self.benchclass.id] = self.benchclass
        elif tag == "instance" and self.benchscope:
            instance = Instance(self.benchclass, attrib["name"], int(attrib["id"]))
            self.benchclass.instances[instance.id] = instance
        elif tag == "project":
            self.project = Project(attrib["name"], attrib["job"])
            self.result.projects[self.project.name] = self.project
        elif tag == "runspec":
            self.benchscope = False
            self.runspec = Runspec(self.result.systems[(attrib["system"], attrib["version"])], self.result.machines[attrib["machine"]], self.result.benchmarks[attrib["benchmark"]], self.result.systems[(attrib["system"], attrib["version"])].settings[attrib["setting"]])
            self.project.runspecs.append(self.runspec)
        elif tag == "class" and not self.benchscope:
            benchclass = self.runspec.benchmark.classes[int(attrib["id"])]
            self.classresult = ClassResult(benchclass)
            self.runspec.classresults.append(self.classresult)
        elif tag == "instance" and not self.benchscope:
            benchinst = self.classresult.benchclass.instances[int(attrib["id"])]
            self.instresult = InstanceResult(benchinst)
            self.classresult.instresults.append(self.instresult)
        elif tag == "run" and not self.benchscope:
            self.run = Run(self.instresult, int(attrib["number"]))
            self.instresult.runs.append(self.run)
        elif tag == "measure":
            self.run.measures[attrib["name"]] = (attrib["type"], attrib["val"]) 

    def close(self):
        """
        This method is called for every closing XML tag.
        """
        pass
