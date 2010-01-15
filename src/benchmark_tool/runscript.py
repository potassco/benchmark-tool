'''
Created on Jan 15, 2010

@author: Roland Kaminski
'''

import os

def mkdir_p(path):
    if not os.path.exists(path): os.makedirs(path)


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
        
class Seqjob(Job):
    def __init__(self, name, timeout, runs, parallel):
        Job.__init__(self, name, timeout, runs)
        self.parallel = parallel
    def genName(self):
        return self.name

           
class Pbsjob(Job):
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
    class Folder:
        def __init__(self, path):
            self.path     = path
            self.prefixes = []
            
        def addIgnore(self, prefix):
            self.prefixes.append(prefix)
            
    class Files:
        def __init__(self, path):
            self.path  = path
            self.files = set()
            
        def addFile(self, file):
            self.files.add(os.path.normpath(file))
            
    def __init__(self, name):
        self.name     = name
        self.elements = []
    def addElement(self, element):
        self.elements.append(element)

class Runspec:
    def __init__(self, machine, setting, benchmark):
        self.machine   = machine
        self.setting   = setting
        self.benchmark = benchmark
    
    def genPath(self):
        name = self.benchmark.name + "-" + self.setting.system.name + "-" + self.setting.system.version + "-" + self.setting.name
        return os.path.join(self.runscript.output, self.runscript.name, self.machine.name, name)
    
    def genScripts(self):
        mkdir_p(os.path.join(self.genPath(), "results"))

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
        mkdir_p(self.output)
        print "implement me!"

            
class Project:
    def __init__(self, name):
        self.name     = name
        self.runspecs = []

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
        self.runspecs.append(runspec)

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