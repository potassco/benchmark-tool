'''
Created on Jan 19, 2010

@author: Roland Kaminski
'''

from benchmarktool.result.soffice import Spreadsheet

class Result:
    """
    Stores the benchmark description and its results.  
    """
    def __init__(self):
        """
        Initializes an empty result.
        """
        self.machines   = {}
        self.configs    = {}
        self.systems    = {}
        self.jobs       = {}
        self.benchmarks = {}
        self.projects   = {}
    
    def merge(self, projects):
        """
        Concatenates the benchmarks in the given projects into one benchmark set.
        
        Keyword arguments:
        projects - The project to merge with 
        """
        benchmarks = set()
        for project in projects:
            for runspec in project.runspecs:
                for classresult in runspec.classresults:
                    for instresult in classresult.instresults:
                        instresult.instance.maxRuns = max(instresult.instance.maxRuns, len(instresult.runs))
                benchmarks.add(runspec.benchmark)
        return BenchmarkMerge(benchmarks)
        
    def genOffice(self, out, selProjects, measures):
        """
        Prints the current result in open office spreadsheet format.
        
        Keyword arguments:
        out         - The output stream to write to
        selProjects - The selected projects ("" for all) 
        measures    - The measures to extract 
        """
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
    """
    Represents an (ordered) set of benchmark sets. 
    """
    def __init__(self, benchmarks):
        """
        Initializes using the given set of benchmarks. 
        """
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

    """
    Creates an interator over all benchmark classes in all benchmarks.
    """
    def __iter__(self):
        for benchmark in sorted(self.benchmarks):
            for benchclass in benchmark:
                yield benchclass

class Machine:
    """
    Represents a machine.
    """
    def __init__(self, name, cpu, memory):
        """
        Initializes a machine.
    
        Keyword arguments:
        name   - The name of the machine 
        cpu    - String describing the CPU
        memory - String describing the Memory
        """
        self.name   = name
        self.cpu    = cpu
        self.memory = memory 

class Config:
    """
    Represents a config.
    """
    def __init__(self, name, template):
        """
        Initializes a machine.
    
        Keyword arguments:
        name     - The name of the config
        template - A path to the template file
        """
        self.name     = name
        self.template = template

class System:
    """
    Represents a system.
    """
    def __init__(self, name, version, config, measures, order):
        """
        Initializes a system.
    
        Keyword arguments:
        name     - The name of the system
        version  - The version
        config   - The config (a string)
        measures - The measurement function (a string) 
        order    - An integer denoting the occurrence in the XML file 
        """
        self.name     = name
        self.version  = version
        self.config   = config
        self.measures = measures
        self.order    = order
        self.settings = {}

class Setting:
    """
    Represents a setting.
    """
    def __init__(self, system, name, cmdline, tag, order, attr):
        """
        Initializes a setting.
    
        Keyword arguments:
        system   - The system associated with the setting
        name     - The name of the setting
        cmdline  - Command line parameters
        tag      - Tags of the setting
        order    - An integer denoting the occurrence in the XML file
        attr     - Arbitrary extra arguments 
        """
        self.system  = system
        self.name    = name
        self.cmdline = cmdline
        self.tag     = tag
        self.order   = order
        self.attr    = attr

class Job:
    """
    Represents a job.
    """
    def __init__(self, name, timeout, runs, attrib):
        """
        Initializes a job.
    
        Keyword arguments:
        name     - The name of the job
        timeout  - Timeout of the job
        runs     - Number of repetitions per instance 
        attr     - Arbitrary extra arguments 
        """
        self.name    = name
        self.timeout = timeout
        self.runs    = runs
        self.attrib  = attrib

class SeqJob(Job):
    """
    Represents a sequential job.
    """
    def __init__(self, name, timeout, runs, parallel, attrib):
        """
        Initializes a job.
    
        Keyword arguments:
        name     - The name of the job
        timeout  - Timeout of the job
        runs     - Number of repetitions per instance
        parallel - Number of processes to start in parallel 
        attr     - Arbitrary extra arguments 
        """
        Job.__init__(self, name, timeout, runs, attrib)
        self.parallel = parallel

class Benchmark:
    """
    Represents a benchmark, i.e., a set of instances.
    """
    def __init__(self, name):
        """
        Initializes a job.
    
        Keyword arguments:
        name - The name of the benchmark
        """
        self.name    = name
        self.classes = {}
        
    def __iter__(self):
        """
        Creates an iterator over all benchmark classes.
        """
        for benchclass in sorted(self.classes.values()):
            yield benchclass
    
    def __cmp__(self, other):
        """
        Compares two benchmarks.
        """
        return cmp(self.name, other.name)
    
    def __hash__(self):
        """
        Calculates a hash value using the name of the benchmark.
        """
        return hash(self.name)

class Class:
    """
    Represents a benchmark class.
    """
    def __init__(self, benchmark, name, uid):
        """
        Initializes a benchmark class.
    
        Keyword arguments:
        benchmark - The benchmark associaed with this class 
        name      - The name of the benchmark
        uid       - A unique id (in the scope of the benchmark)  
        """
        self.benchmark = benchmark
        self.name      = name
        self.id        = uid
        self.line      = None
        self.instances = {}
    
    def __cmp__(self, other):
        """
        Compares two benchmark classes. 
        """
        return cmp((self.benchmark, self.name), (other.benchmark, other.name)) 

    def __iter__(self):
        """
        Creates an iterator over all instances in the benchmark class.
        """
        for benchinst in sorted(self.instances.values()):
            yield benchinst

class Instance:
    """
    Represents a benchmark instance.
    """
    def __init__(self, benchclass, name, uid):
        """
        Initializes a benchmark instance.
        
        benchclass - The class of the instance
        name       - The name of the instance
        uid        - A unique id (in the scope of the class)
        """
        self.benchclass = benchclass
        self.name       = name
        self.id         = uid
        self.line       = None
        self.maxRuns    = 0
    
    def __cmp__(self, other):
        """
        Compares two benchmark instances. 
        """
        return cmp((self.benchclass, self.name), (other.benchclass, other.name))

class Project:
    """
    Describes a project, i.e, a collection of run specifications.
    """
    def __init__(self, name, job):
        """
        Initializes a benchmark instance.
        
        name - The name of the project
        job  - Job associated with the project (a string)
        """
        self.name     = name
        self.job      = job
        self.runspecs = []
    
    def __iter__(self):
        """
        Creates an iterator over all run specification in the project. 
        """
        for runspec in self.runspecs:
            yield runspec

class Runspec():
    """
    Describes a run specification, i.e, how to run individual systems
    on a set of instances.
    """
    def __init__(self, system, machine, benchmark, setting):
        """
        Initializes a run specification.
        
        Keyword arguments:
        system    - The system to evaluate
        machine   - The machine to run on
        benchmark - The benchmark set to evaluate
        settings  - The settings to run with
        """
        self.system       = system
        self.machine      = machine
        self.benchmark    = benchmark
        self.setting      = setting
        self.classresults = []
    
    def __iter__(self):
        """
        Creates an iterator over all results (grouped by benchmark class.)  
        """
        for classresult in self.classresults:
            yield classresult

class ClassResult:
    """
    Represents the results of all instances of a benchmark class.
    """
    def __init__(self, benchclass):
        """
        Initializes an empty class result.
        
        Keyword arguments:
        benchclass - The benchmark class for the results
        """
        self.benchclass  = benchclass
        self.instresults = []
        
    def __iter__(self):
        """
        Creates an iterator over all the individual results per instance.
        """
        for instresult in self.instresults:
            yield instresult

class InstanceResult:
    """
    Represents the result of an individual instance (with possibly multiple runs). 
    """
    def __init__(self, instance):
        """
        Initializes an empty instance result (0 runs).
        """
        self.instance = instance
        self.runs     = []
    
    def __iter__(self):
        """
        Creates an iterator over the result of all runs.
        """
        for run in self.runs:
            yield run

class Run:
    """
    Represents the result of an individual run of a benchmark instance. 
    """
    def __init__(self, instresult, number):
        """
        Initializes a benchmark result.
        
        Keyword arguments:
        instresult - The associated instance result
        number     - The number of the run
        """
        self.instresult = instresult
        self.number     = number
        self.measures   = {}
    
    def iter(self, measures):
        """
        Creates an iterator over all measures captured during the run.
        Measures can be filter by giving a string set of measure names.
        If this sttring set is "" instead all measures sorted by their keys 
        will be returned. 
        """
        if measures == "": 
            for name in sorted(self.measures.keys()):
                yield name, self.measures[name][0], self.measures[name][1]
        else:
            for name, _ in measures:
                if name in self.measures:
                    yield name, self.measures[name][0], self.measures[name][1]
