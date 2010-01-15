'''
Created on Jan 15, 2010

@author: Roland Kaminski
'''

import tools
import os

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
    def __init__(self, name, cmdline, tag):
        self.name    = name
        self.cmdline = cmdline
        self.tag     = tag
        
class Job:
    def __init__(self, name, timeout, runs):
        self.name    = name
        self.timeout = timeout
        self.runs    = runs

class SeqScriptGen:
    def __init__(self, seqJob):
        self.seqJob = seqJob
    
    def addToScript(self, runspec, instance):
        for run in range(1, self.seqJob.runs + 1):
            path = os.path.join(runspec.path(), instance.classname, instance.instance, "run%d" % run)
            tools.mkdir_p(path)
    
    def genStartScript(self, path):
        tools.mkdir_p(path)
        print "implement me: generate start script!"
        
    
class SeqJob(Job):
    def __init__(self, name, timeout, runs, parallel):
        Job.__init__(self, name, timeout, runs)
        self.parallel = parallel
    
    def scriptGen(self):
        return SeqScriptGen(self) 

           
class PbsJob(Job):
    def __init__(self, name, timeout, runs, ppn, procs, script_mode, walltime):
        Job.__init__(self, name, timeout, runs)
        self.ppn         = ppn
        self.procs       = procs
        self.script_mode = script_mode
        self.walltime    = walltime

class Config:
    def __init__(self, name, template):
        self.name     = name
        self.template = template

class Benchmark:
    class Instance:
        def __init__(self, location, classname, instance):
            self.location  = location
            self.classname = classname
            self.instance  = instance
            self.hash      = hash((location, classname, instance))
        
        def __hash__(self):
            return self.hash 
        
    class Folder:
        def __init__(self, path):
            self.path     = path
            self.prefixes = set()
            
        def addIgnore(self, prefix):
            self.prefixes.add(os.path.normpath(prefix))
        
        def skip(self, root, path):
            if path == ".svn": 
                return True
            path = os.path.normpath(os.path.join(root, path))
            return path in self.prefixes
            
        def init(self, benchmark):
            for root, dirs, files in os.walk(self.path):
                relroot = os.path.relpath(root, self.path)
                sub = []
                for dir in dirs:
                    if self.skip(relroot, dir): continue
                    sub.append(dir)
                dirs[:] = sub
                for filename in files:
                    if self.skip(relroot, filename): continue
                    benchmark.addInstance(self.path, relroot, filename) 

    class Files:
        def __init__(self, path):
            self.path  = path
            self.files = set()
            
        def addFile(self, path):
            self.files.add(os.path.normpath(path))
        
        def init(self, benchmark):
            for path in self.files:
                if os.path.exists(os.path.join(self.path, path)):
                    relroot, filename = os.path.split(path)
                    benchmark.addInstance(self.path, relroot, filename)
                
    def __init__(self, name):
        self.name        = name
        self.elements    = []
        self.instances   = set()
        self.initialized = False
        
    def addElement(self, element):
        self.elements.append(element)
    
    def addInstance(self, root, relroot, filename):
        self.instances.add(Benchmark.Instance(root, relroot, filename))
    
    def init(self):
        if not self.initialized:
            for element in self.elements:
                element.init(self)
            self.initialized = True

class Runspec:
    def __init__(self, machine, setting, benchmark):
        self.machine   = machine
        self.setting   = setting
        self.benchmark = benchmark
    
    def path(self):
        name = self.setting.system.name + "-" + self.setting.system.version + "-" + self.setting.name
        return os.path.join(self.project.path(), "results", self.benchmark.name, name)
    
    def genScripts(self, scriptGen):
        self.benchmark.init()
        for instance in self.benchmark.instances:
            scriptGen.addToScript(self, instance)

class Runscript:
    def __init__(self, name, output):
        self.name       = name
        self.output     = output
        self.jobs       = {}
        self.projects   = {}
        self.machines   = {}
        self.systems    = {}
        self.configs    = {} 
        self.benchmarks = {}
    
    def addMachine(self, machine):
        self.machines[machine.name] = machine
    
    def addSystem(self, system, config):
        system.config = self.configs[config]
        self.systems[(system.name, system.version)] = system
        
    def addConfig(self, config):
        self.configs[config.name] = config

    def addBenchmark(self, benchmark):
        self.benchmarks[benchmark.name] = benchmark
    
    def addJob(self, job):
        self.jobs[job.name] = job
    
    def addProject(self, project, job):
        project.runscript = self
        project.job       = self.jobs[job] 
        self.projects[project.name] = project

    def genScripts(self):
        for project in self.projects.values():
            project.genScripts()
    
    def path(self):
        return self.output

class Project:
    def __init__(self, name):
        self.name     = name
        self.runspecs = {}

    def addRuntag(self, machine, benchmark, tag):
        disj = TagDisj(tag)
        for system in self.runscript.systems.values():
            for setting in system.settings.values():
                if disj.match(setting.tag):
                    self.addRunspec(machine, system.name, system.version, setting.name, benchmark)
        
    def addRunspec(self, machine, system, version, setting, benchmark):
        runspec = Runspec(self.runscript.machines[machine],
                          self.runscript.systems[(system,version)].settings[setting], 
                          self.runscript.benchmarks[benchmark])
        runspec.project = self
        if not machine in self.runspecs: self.runspecs[machine] = []
        self.runspecs[machine].append(runspec)
    
    def path(self):
        return os.path.join(self.runscript.path(), self.name)
    
    def genScripts(self):
        for machine, runspecs in self.runspecs.items():
            scriptGen = self.job.scriptGen()
            for runspec in runspecs:
                runspec.genScripts(scriptGen)
            scriptGen.genStartScript(self.path())

class TagDisj:
    """Represents tags in form of a disjunctive normal form."""
    ALL = 1
    def __init__(self, tag):
        """
        Transforms a string into a disjunctive normal form of tags.
        Spaces between tags are interpreted as conjunctions and |
        is interpreted as disjunction. The special value "*all*"
        matches everything.
        
        Keyword arguments:
        tag -- a string representing a disjunctive normal form of tags   
        """        
        if tag == "*all*": 
            self.tag = self.ALL
        else:
            self.tag = []
            tagDisj = tag.split("|")
            for tagConj in tagDisj:
                tagList = tagConj.split(None)
                self.tag.append(frozenset(tagList))
                
    def match(self, tag):
        """
        Checks whether a given set of tags is subsumed.
        
        Keyword arguments:
        tag - a set of tags
        """  
        if self.tag == self.ALL:
            return True
        for conj in self.tag:
            if conj.issubset(tag):
                return True
        return False
    