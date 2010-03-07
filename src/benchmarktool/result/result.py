'''
Created on Jan 19, 2010

@author: Roland Kaminski
'''

from benchmarktool.result.soffice import Spreadsheet

class Result:
    def __init__(self):
        self.machines   = {}
        self.configs    = {}
        self.systems    = {}
        self.jobs       = {}
        self.benchmarks = {}
        self.projects   = {}
    
    def merge(self, projects):
        benchmarks = set()
        for project in projects:
            for runspec in project.runspecs:
                for classresult in runspec.classresults:
                    for instresult in classresult.instresults:
                        instresult.instance.maxRuns = max(instresult.instance.maxRuns, len(instresult.runs))
                benchmarks.add(runspec.benchmark)
        return BenchmarkMerge(benchmarks)
        
    def genOffice(self, out, selProjects, measures):
        projects = [] 
        for project in self.projects.values():
            if selProjects == "" or project.name in selProjects:
                projects.append(project)
        benchmarkMerge = self.merge(projects)
        
        sheet = Spreadsheet(benchmarkMerge, measures)
        for project in projects:
            for runspec in project.runspecs:
                sheet.addRunspec(runspec)
        sheet.finish()
        sheet.printSheet(out)

class BenchmarkMerge:
    def __init__(self, benchmarks):
        self.benchmarks = benchmarks
        instNum         = 0
        classNum        = 0
        for benchclass in self:
            benchclass.line      = classNum
            benchclass.instStart = instNum
            for instance in benchclass:  
                instance.line = instNum
                instNum      += max(instance.maxRuns, 1)
            benchclass.instEnd = instNum - 1
            classNum          += 1

    def __iter__(self):
        for benchmark in sorted(self.benchmarks):
            for benchclass in benchmark:
                yield benchclass

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
    def __init__(self, name, version, config, measures, order):
        self.name     = name
        self.version  = version
        self.config   = config
        self.measures = measures
        self.order    = order
        self.settings = {}

class Setting:
    def __init__(self, system, name, cmdline, tag, order, attr):
        self.system  = system
        self.name    = name
        self.cmdline = cmdline
        self.tag     = tag
        self.order   = order
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
        
    def __iter__(self):
        for benchclass in sorted(self.classes.values()):
            yield benchclass
    
    def __cmp__(self, other):
        return cmp(self.name, other.name)
    
    def __hash__(self):
        return hash(self.name)

class Class:
    def __init__(self, benchmark, name, uid):
        self.benchmark = benchmark
        self.name      = name
        self.id        = uid
        self.line      = None
        self.instances = {}
    
    def __cmp__(self, other):
        return cmp((self.benchmark, self.name), (other.benchmark, other.name)) 

    def __iter__(self):
        for benchinst in sorted(self.instances.values()):
            yield benchinst

class Instance:
    def __init__(self, benchclass, name, uid):
        self.benchclass = benchclass
        self.name       = name
        self.id         = uid
        self.line       = None
        self.maxRuns    = 0
    
    def __cmp__(self, other):
        return cmp((self.benchclass, self.name), (other.benchclass, other.name))

class Project:
    def __init__(self, name, job):
        self.name     = name
        self.job      = job
        self.runspecs = [] 
    
    def __iter__(self):
        for runspec in self.runspecs:
            yield runspec

class Runspec():
    def __init__(self, system, machine, benchmark, setting):
        self.system       = system
        self.machine      = machine
        self.benchmark    = benchmark
        self.setting      = setting
        self.classresults = []
    
    def __iter__(self):
        for classresult in self.classresults:
            yield classresult

class ClassResult:
    def __init__(self, benchclass):
        self.benchclass  = benchclass
        self.instresults = []
        
    def __iter__(self):
        for instresult in self.instresults:
            yield instresult

class InstanceResult:
    def __init__(self, instance):
        self.instance = instance
        self.runs     = []
    
    def __iter__(self):
        for run in self.runs:
            yield run

class Run:
    def __init__(self, instresult, number):
        self.instresult = instresult
        self.number     = number
        self.measures   = {}
    
    def iter(self, measures):
        if measures == "": 
            for name in sorted(self.measures.keys()):
                yield name, self.measures[name][0], self.measures[name][1]
        else:
            for name, _ in measures:
                if name in self.measures:
                    yield name, self.measures[name][0], self.measures[name][1]
