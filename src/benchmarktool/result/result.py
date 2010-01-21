'''
Created on Jan 19, 2010

@author: Roland Kaminski
'''

import heapq
import itertools
from benchmarktool.result.soffice import Column, Spreadsheet

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
        columns    = set()
        for project in projects:
            for runspec in project.runspecs:
                columns.add(Column(runspec.setting, runspec.machine))
                for classresult in runspec.classresults:
                    for instresult in classresult.instresults:
                        instresult.instance.maxRuns = max(instresult.instance.maxRuns, len(instresult.runs))
                benchmarks.add(runspec.benchmark)
        
        return BenchmarkMerge(benchmarks), ColumnMerge(columns)
        
    def genOffice(self, out, selProjects, measures):
        projects = [] 
        for project in self.projects.values():
            if selProjects == "" or project.name in selProjects:
                projects.append(project)
        benchmarkMerge, columnMerge = self.merge(projects)
        
        sheet = Spreadsheet(benchmarkMerge, columnMerge, measures)
        for project in projects:
            for runspec in project.runspecs:
                sheet.addRunspec(runspec)
        sheet.finish()
        sheet.printSheet(out)

class ColumnMerge:
    def __init__(self, columns):
        self.machines = set()
        self.columns  = {}
        for column in columns:
            self.columns[column] = column
            self.machines.add(column.machine)

    def getColumn(self, runspec):
        return self.columns[Column(runspec.setting, runspec.machine)]
    
class BenchmarkMerge:
    def __init__(self, benchmarks):
        start = []
        for benchmark in benchmarks:
            start = heapq.merge(start, benchmark)
        self.list = []
        num = 0
        for _, instances in itertools.groupby(start, lambda instance: (instance.benchclass.id, instance.id)):
            maxRuns = 1
            line = {}
            for instance in instances:
                line[instance.benchclass.benchmark] = instance
                instance.line = num
                maxRuns = max(instance.maxRuns, maxRuns)
            self.list.append(line)
            num = num + maxRuns 

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
    class Iterator:
        def __init__(self, benchmark):
            self.posclass = iter(sorted(benchmark.classes.values()))
            self.posinst  = None
            
        def next(self):
            while True:
                if self.posinst == None:
                    nextclass    = self.posclass.next()
                    self.posinst = iter(sorted(nextclass.instances.values()))
                try:
                    return self.posinst.next()
                except StopIteration:
                    self.posinst = None

    def __init__(self, name):
        self.name    = name
        self.classes = {}
        
    def __iter__(self):
        return Benchmark.Iterator(self)
    
class Class:
    def __init__(self, benchmark, name, uid):
        self.benchmark = benchmark
        self.name      = name
        self.id        = uid
        self.instances = {}

class Instance:
    def __init__(self, benchclass, name, uid):
        self.benchclass = benchclass
        self.name       = name
        self.id         = uid
        self.line       = None
        self.maxRuns    = 0
    
    def __cmp__(self, other):
        return cmp((self.benchclass.name, self.name, self.benchclass.benchmark.name), (other.benchclass.name, other.name, other.benchclass.benchmark.name))  

class Project:
    def __init__(self, name, job):
        self.name     = name
        self.job      = job
        self.runspecs = [] 

class Runspec():
    def __init__(self, system, machine, benchmark, setting):
        self.system       = system
        self.machine      = machine
        self.benchmark    = benchmark
        self.setting      = setting
        self.classresults = []

class ClassResult:
    def __init__(self, benchclass):
        self.benchclass  = benchclass
        self.instresults = []

class InstanceResult:
    def __init__(self, instance):
        self.instance = instance
        self.runs     = []

class Run:
    def __init__(self, instresult, number):
        self.instresult = instresult
        self.number     = number
        self.measures   = {}
