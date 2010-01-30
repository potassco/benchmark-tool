"""
This module contains classes that describe a run script.
It can be used to create scripts to start a benchmark 
specified by the run script. 
"""

__author__ = "Roland Kaminski"

import benchmarktool.pyratemp as pyratemp
import benchmarktool.tools as tools
import os
import stat

# needed to embed measurements functions via exec 
# pylint: disable-msg=W0611
import benchmarktool.config #@UnusedImport
# pylint: enable-msg=W0611

class Machine:
    """
    Describes a machine.
    """
    def __init__(self, name, cpu, memory):
        """
        Initializes a machine.
        
        Keyword arguments:
        name   - A name uniquely identifying the machine
        cpu    - Some cpu description
        memory - Some memory description
        """
        self.name   = name
        self.cpu    = cpu
        self.memory = memory

    def toXml(self, out, indent):
        """
        Dump the (pretty-printed) XML-representation of the machine.
        
        Keyword arguments:
        out    - Output stream to write to
        indent - Amount of indentation 
        """
        out.write('{1}<machine name="{0.name}" cpu="{0.cpu}" memory="{0.memory}"/>\n'.format(self, indent))

    def __hash__(self):
        """
        Return a hash values using the name of the machine.
        """
        return hash(self.name)
        
    def __cmp__(self, machine):
        """
        Compare two machines.
        """
        return cmp(self.name, machine.name)
    
class System:
    """
    Describes a system. This includes a solver description 
    together with a set of settings.  
    """
    def __init__(self, name, version, measures, order):
        """
        Initializes a system. Name and version of the system 
        are used to uniquely identify a system.   
        
        Keyword arguments:
        name     - The name of the system
        version  - The version of the system
        measures - A string specifying the measurement function
                   This must be a function given in the config
        order    - An integer used to order different system.
                   This integer should denote the occurrence in 
                   the run specification.      
        """
        self.name     = name
        self.version  = version
        self.measures = measures
        self.order    = order
        self.settings = {}
        self.config   = None
         
    def addSetting(self, setting):
        """
        Adds a given setting to the system.
        """
        setting.system = self
        self.settings[setting.name] = setting
        
    def toXml(self, out, indent, settings = None):
        """
        Dump the (pretty-printed) XML-representation of the system.
        
        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        setting - If None all the settings of the system are printed,
                  otherwise the given settings are printed  
        """
        out.write('{1}<system name="{0.name}" version="{0.version}" measures="{0.measures}" config="{0.config.name}">\n'.format(self, indent))
        if settings == None: settings = self.settings
        for setting in sorted(settings, key=lambda s: s.order):
            setting.toXml(out, indent + "\t")
        out.write('{0}</system>\n'.format(indent))
        
    def __hash__(self):
        """
        Calculates a hash value for the system using its name and version. 
        """
        return hash((self.name, self.version))

    def __cmp__(self, system):
        """
        Compares two systems using name and version. 
        """
        return cmp((self.name, self.version), (system.name, system.version))

class Setting:
    """
    Describes a setting for a system. This are command line options
    that can be passed to the system. Additionally, settings can be tagged. 
    """
    def __init__(self, name, cmdline, tag, order, attr):
        """
        Initializes a system.
        
        name    - A name uniquely identifying a setting. 
                  (In the scope of a system)
        cmdline - A string of command line options
        tag     - A set of tags
        order   - An integer specifying the order of settings
                  (This should denote the occurrence in the job specification.
                  Again in the scope of a system.)
        attr    - A dictionary of additional optional attributes.  
        """
        self.name    = name
        self.cmdline = cmdline
        self.tag     = tag
        self.order   = order
        self.attr    = attr

    def toXml(self, out, indent):
        """
        Dump a (pretty-printed) XML-representation of the setting.
        
        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """
        tag = " ".join(sorted(self.tag))
        out.write('{1}<setting name="{0.name}" cmdline="{0.cmdline}" tag="{2}"'.format(self, indent, tag))
        for key, val in self.attr.items():
            out.write(' {0}="{1}"'.format(key, val))
        out.write('/>\n')

    def __hash__(self):
        """
        Calculates a hash value for the setting using its name. 
        """
        return hash(self.name)

    def __cmp__(self, setting):
        """
        Compares two settings using their names. 
        """
        return cmp(self.name, setting.name)

        
class Job:
    """
    Base class for all jobs. 
    """
    def __init__(self, name, timeout, runs, attr):
        """
        Initializes a job.
        
        Keyword arguments:
        name    - A unique name for a job
        timeout - A timeout in seconds for individual benchmark runs
        runs    - The number of runs per benchmark
        attr    - A dictionary of arbitrary attributes
        """
        self.name    = name
        self.timeout = timeout
        self.runs    = runs
        self.attr    = attr

    def _toXml(self, out, indent, xmltag, extra):
        """
        Helper function to dump a (pretty-printed) XML-representation of a job.
        
        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        xmltag  - Tag name for the job
        extra   - Additional arguments for the job 
        """
        out.write('{1}<{2} name="{0.name}" timeout="{0.timeout}" runs="{0.runs}"{3}'.format(self, indent, xmltag, extra))
        for key, val in self.attr.items():
            out.write(' {0}="{1}"'.format(key, val))
        out.write('/>\n')
        
    def __hash__(self):
        """
        Calculates a hash value for the job using its name. 
        """
        return hash(self.name)
    
    def __cmp__(self, job):
        """
        Compares two jobs using their names. 
        """
        return cmp(job.name, job.name)

class Run:
    """
    Base class for all runs. 
    """
    def __init__(self, path):
        """
        Initializes a run.
        
        Keyword arguments:
        path - A path that holds the location 
               where the individual start scripts for the job shall be generated 
        """
        self.path = path
    
    def root(self):
        """
        Returns the root directory relative to the location of the run's path. 
        """
        return os.path.relpath(".", self.path)
    
class SeqRun(Run):
    """
    Describes a sequential run.
    """
    def __init__(self, path, run, job, runspec, instance):
        """
        Initializes a sequential run.
        
        Keyword arguments:
        path     - A path that holds the location 
                   where the individual start scripts for the job shall be generated
        run      - The number of the run
        job      - A reference to the job description
        runspec  - A reference to the run description
        instance - A reference to the instance to benchmark
        """
        Run.__init__(self, path)
        self.run      = run
        self.job      = job
        self.runspec  = runspec
        self.instance = instance
    
    def file(self):
        """
        Returns a relative path to the instance. 
        """
        return os.path.relpath(self.instance.path(), self.path)
    
    def args(self):
        """
        Returns the command line arguments for this run.
        """
        return self.runspec.setting.cmdline
    
    def solver(self):
        """
        Returns the solver for this run.
        """
        return self.runspec.system.name + "-" + self.runspec.system.version
    
    def timeout(self):
        """
        Returns the timeout of this run. 
        """
        return self.job.timeout
    
class SeqScriptGen:
    """
    A class that generates and evaluates start scripts for sequential runs.
    """
    def __init__(self, seqJob):
        """
        Initializes the script generator.
        
        Keyword arguments:
        seqJob - A reference to the associated sequential job.
        """
        self.seqJob     = seqJob
        self.startfiles = []
    
    def _path(self, runspec, instance, run):
        """
        Returns the relative path to the start script location.
        
        Keyword arguments:
        runspec  - The run specification for the start script
        instance - The benchmark instance for the start script
        run      - The number of the run for the start script
        """
        return os.path.join(runspec.path(), instance.classname.name, instance.instance, "run%d" % run)
        
    def addToScript(self, runspec, instance):
        """
        Creates a new start script for the given instance.
        
        Keyword arguments:
        runspec  - The run specification for the start script
        instance - The benchmark instance for the start script
        """
        for run in range(1, self.seqJob.runs + 1):
            path = self._path(runspec, instance, run)
            tools.mkdir_p(path)
            startpath = os.path.join(path, "start.sh")
            template  = pyratemp.Template(filename=runspec.system.config.template)
            startfile = open(startpath, "w")
            startfile.write(template(run=SeqRun(path, run, self.seqJob, runspec, instance)))
            startfile.close()
            self.startfiles.append((path, "start.sh"))
            startstat = os.stat(startpath)
            os.chmod(startpath, startstat[0] | stat.S_IXUSR)
    
    def evalResults(self, out, indent, runspec, instance):
        """
        Parses the results of a given benchmark instance and outputs them as XML.
        
        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        runspec - The run specification of the benchmark
        runspec - The benchmark instance
        """
        # pylint: disable-msg=W0122
        exec("func = benchmarktool.config." + runspec.system.measures)
        for run in range(1, self.seqJob.runs + 1):
            out.write('{0}<run number="{1}">\n'.format(indent, run))
            # pylint: disable-msg=E0602
            result = func(self._path(runspec, instance, run), runspec) #@UndefinedVariable
            for key, valtype, val in sorted(result):
                out.write('{0}<measure name="{1}" type="{2}" val="{3}"/>\n'.format(indent + "\t", key, valtype, val))
            out.write('{0}</run>\n'.format(indent))
    
    def genStartScript(self, path):
        """
        Generates a start script that can be used to start all scripts 
        generated using addToScript().
        
        Keyword arguments:
        path - The target location for the script
        """
        tools.mkdir_p(path)
        startfile = open(os.path.join(path, "start.py"), 'w')
        queue = ""
        comma = False
        for (instpath, instname) in self.startfiles:
            relpath = os.path.relpath(instpath, path)
            if comma: queue += ","
            else: comma  = True
            queue+= repr(os.path.join(relpath, instname))
        startfile.write("""\
#!/usr/bin/python

import optparse
import threading
import subprocess
import os
import sys

queue = [{0}]

class Main:
    def __init__(self):
        self.sem     = threading.BoundedSemaphore({1})
        self.lock    = threading.Lock()
        self.running = set()
        self.started = 0
        self.total   = None
    
    def finish(self, thread):
        self.lock.acquire()
        self.running.remove(thread)
        self.lock.release()
        self.sem.release()
   
    def start(self, cmd):
        self.sem.acquire()
        self.lock.acquire()
        thread = Run(cmd, self)
        self.started += 1
        self.running.add(thread)
        print("({{0}}/{{1}}/{{2}}) {{3}}".format(len(self.running), self.started, self.total, cmd))
        thread.start()
        self.lock.release()
    
    def run(self, queue):
        self.total = len(queue)
        for cmd in queue:
            self.start(cmd)
    
    def exit(self):
        self.lock.acquire()
        for thread in self.running:
            print("==== WARNING: stopping {{0}} ====".format(thread.cmd))
        self.lock.release()

class Run(threading.Thread):
    def __init__(self, cmd, main):
        threading.Thread.__init__(self)
        self.cmd  = cmd
        self.main = main
    
    def run(self):
        path, script = os.path.split(self.cmd)
        subprocess.Popen(["bash", script], cwd=path).wait()
        self.main.finish(self)

def gui():
    import Tkinter
    class App:
        def __init__(self):
            root    = Tkinter.Tk()
            frame   = Tkinter.Frame(root)
            scrollx = Tkinter.Scrollbar(frame, orient=Tkinter.HORIZONTAL)
            scrolly = Tkinter.Scrollbar(frame)
            list    = Tkinter.Listbox(frame, selectmode=Tkinter.MULTIPLE)
            
            for script in queue:
                list.insert(Tkinter.END, script)
            
            scrolly.config(command=list.yview)
            scrollx.config(command=list.xview)
            list.config(yscrollcommand=scrolly.set)
            list.config(xscrollcommand=scrollx.set)
                
            scrolly.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
            scrollx.pack(side=Tkinter.BOTTOM, fill=Tkinter.X)
            list.pack(fill=Tkinter.BOTH, expand=1)
            
            button = Tkinter.Button(root, text='Run', command=self.pressed)
            
            frame.pack(fill=Tkinter.BOTH, expand=1)
            button.pack(side=Tkinter.BOTTOM, fill=Tkinter.X)

            self.root  = root
            self.list  = list
            self.run   = False
            self.queue = [] 
        
        def pressed(self):
            sel = self.list.curselection()
            for index in sel:
                global queue
                self.queue.append(queue[int(index)])
            self.root.destroy()

        def start(self):
            self.root.mainloop()
            return self.queue

    global queue
    queue.sort()
    queue = App().start()

if __name__ == '__main__':
    usage  = "usage: %prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-g", "--gui", action="store_true", dest="gui", default=False, help="start gui to selectively start benchmarks") 

    opts, args = parser.parse_args(sys.argv[1:])
    if len(args) > 0: parser.error("no arguments expected")
    
    os.chdir(os.path.dirname(sys.argv[0]))
    if opts.gui: gui()

    m = Main()
    try:
        m.run(queue)
    except:
        m.exit()
        sys.exit("interrupted")
""".format(queue, self.seqJob.parallel))
        startfile.close()
        startstat = os.stat(os.path.join(path, "start.py"))
        os.chmod(os.path.join(path, "start.py"), startstat[0] | stat.S_IXUSR)

class SeqJob(Job):
    """
    Describes a sequential job.
    """
    def __init__(self, name, timeout, runs, parallel, attr):
        """
        Initializes a sequential job description.  
        
        Keyword arguments:
        name     - A unique name for a job
        timeout  - A timeout in seconds for individual benchmark runs
        runs     - The number of runs per benchmark
        parallel - The number of runs that can be started in parallel
        attr     - A dictionary of arbitrary attributes
        """
        Job.__init__(self, name, timeout, runs, attr)
        self.parallel = parallel
    
    def scriptGen(self):
        """
        Returns a class that can generate start scripts and evaluate benchmark results.
        (see SeqScriptGen) 
        """
        return SeqScriptGen(self) 

    def toXml(self, out, indent):
        """
        Dump a (pretty-printed) XML-representation of the sequential job.
        
        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """
        extra = ' parallel="{0.parallel}"'.format(self)
        Job._toXml(self, out, indent, "seqjob", extra)

           
class PbsJob(Job):
    def __init__(self, name, timeout, runs, ppn, procs, script_mode, walltime, attr):
        """
        Initializes a parallel job description.  
        
        Keyword arguments:
        name        - A unique name for a job
        timeout     - A timeout in seconds for individual benchmark runs
        runs        - The number of runs per benchmark
        ppn         - The number of processors per node
        procs       - A list of processes to start in parallel
        script_mode - Specifies the script generation mode
        walltime    - The walltime for a job submitted via PBS 
        attr        - A dictionary of arbitrary attributes
        """
        Job.__init__(self, name, timeout, runs, attr)
        self.ppn         = ppn
        self.procs       = procs
        self.script_mode = script_mode
        self.walltime    = walltime

    def toXml(self, out, indent):
        """
        Dump a (pretty-printed) XML-representation of the parallel job.
        
        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """        
        procs    = " ".join(self.procs)
        extra = ' ppn="{0.ppn}" procs={1} script_mode="{0.script_mode}" walltime="{0.walltime}"'.format(self, procs)
        Job._toXml(self, out, indent, "pbsjob", extra)

class Config:
    """
    Describes a configuration. Currently, this only specifies a template 
    that is used for start script generation. 
    """
    def __init__(self, name, template):
        """
        Keyword arguments:
        name     - A name uniquely identifying the configuration
        template - A path to the template for start script generation
        """
        self.name     = name
        self.template = template

    def toXml(self, out, indent):
        """
        Dump a (pretty-printed) XML-representation of the configuration.
        
        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """
        out.write('{1}<config name="{0.name}" template="{0.template}"/>\n'.format(self, indent))

    def __hash__(self):
        """
        Calculates a hash value for the configuration using its name. 
        """
        return hash(self.name)
    
    def __cmp__(self, config):
        """
        Compares two configurations using their names.
        """
        return cmp(config.name, config.name)

class Benchmark:
    """
    Describes a benchmark. This includes a set of classes
    that describe where to find particular instances.
    """
    class Class:
        """
        Describes a benchmark class.
        """
        def __init__(self, name):
            """
            Initializes a benchmark class.
            
            Keyword arguments:
            name - A name uniquely identifying a benchmark class (per benchmark).
            """
            self.name = name
            self.id   = None 

        def __cmp__(self, other):
            """
            Compares two benchmark classes using their names.
            """
            return cmp(self.name, other.name) 

        def __hash__(self):
            """
            Calculates a hash value for the benchmark class using its name. 
            """
            return hash(self.name)
            
    class Instance:
        """
        Describes a benchmark instance.
        """
        def __init__(self, location, classname, instance):
            """
            Initializes a benchmark instance. The instance name uniquely identifies
            an instance (per benchmark class). 
            
            Keyword arguments:
            location  - The location of the benchmark instance.
            classname - The class name of the instance 
            instance  - The name of the instance
            """
            self.location  = location
            self.classname = classname
            self.instance  = instance
            self.id        = None

        def toXml(self, out, indent):
            """
            Dump a (pretty-printed) XML-representation of the configuration.
            
            Keyword arguments:
            out     - Output stream to write to
            indent  - Amount of indentation
            """
            out.write('{1}<instance name="{0.instance}" id="{0.id}"/>\n'.format(self, indent))

        def __cmp__(self, instance):
            """
            Compares tow instances using the instance name.
            """
            return cmp(self.instance, instance.instance) 

        def __hash__(self):
            """
            Calculates a hash using the instance name.
            """
            return hash(self.instance)

        def path(self):
            """
            Returns the location of the instance by concatenating 
            location, class name and instance name.
            """
            return os.path.join(self.location, self.classname.name, self.instance)
        
    class Folder:
        """
        Describes a folder that should recursively be scanned for benchmarks.
        """
        def __init__(self, path):
            """
            Initializes a benchmark folder.
            
            Keyword arguments:
            path - The location of the folder
            """
            self.path     = path
            self.prefixes = set()
            
        def addIgnore(self, prefix):
            """
            Can be used to ignore certain sub-folders or instances 
            by giving a path prefix that shall be ignored.
            
            Keyword arguments:
            prefix - The prefix to be ignored 
            """
            self.prefixes.add(os.path.normpath(prefix))
        
        def _skip(self, root, path):
            """
            Returns whether a given path should be ignored.
            
            Keyword arguments:
            root - The root path
            path - Some path relative to the root path
            """
            if path == ".svn": 
                return True
            path = os.path.normpath(os.path.join(root, path))
            return path in self.prefixes
            
        def init(self, benchmark):
            """
            Recursively scans the folder and adds all instances found to the given benchmark.
            
            Keyword arguments:
            benchmark - The benchmark to be populated.
            """
            for root, dirs, files in os.walk(self.path):
                relroot = os.path.relpath(root, self.path)
                sub = []
                for dirname in dirs:
                    if self._skip(relroot, dirname): continue
                    sub.append(dirname)
                dirs[:] = sub
                for filename in files:
                    if self._skip(relroot, filename): continue
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
        self.instances   = {}
        self.initialized = False
        
    def addElement(self, element):
        self.elements.append(element)
    
    def addInstance(self, root, relroot, filename):
        classname = Benchmark.Class(relroot)
        if not classname in self.instances: 
            self.instances[classname] = set()
        self.instances[classname].add(Benchmark.Instance(root, classname, filename))
    
    def init(self):
        if not self.initialized:
            for element in self.elements: element.init(self)
            classid = 0
            for classname in sorted(self.instances.keys()):
                classname.id = classid
                classid += 1
                instanceid = 0
                for instance in sorted(self.instances[classname]):
                    instance.id = instanceid
                    instanceid += 1
            self.initialized = True
            

    def toXml(self, out, indent):
        self.init()
        out.write('{1}<benchmark name="{0}">\n'.format(self.name, indent))
        for classname in sorted(self.instances.keys()):
            instances = self.instances[classname]
            out.write('{1}<class name="{0.name}" id="{0.id}">\n'.format(classname, indent + "\t"))
            for instance in sorted(instances):
                instance.toXml(out, indent + "\t\t")
            out.write('{0}</class>\n'.format(indent + "\t"))
        out.write('{0}</benchmark>\n'.format(indent))
        
    def __hash__(self):
        return hash(self.name)

    def __cmp__(self, benchmark):
        return cmp(benchmark.name, benchmark.name)

class Runspec:
    def __init__(self, machine, setting, benchmark):
        self.machine   = machine
        self.setting   = setting
        self.system    = setting.system
        self.benchmark = benchmark
        self.project   = None
    
    def path(self):
        name = self.setting.system.name + "-" + self.setting.system.version + "-" + self.setting.name
        return os.path.join(self.project.path(), self.machine.name, "results", self.benchmark.name, name)
    
    def genScripts(self, scriptGen):
        self.benchmark.init()
        for instances in self.benchmark.instances.values():
            for instance in instances:
                scriptGen.addToScript(self, instance)
    
    def __cmp__(self, runspec):
        return cmp((self.machine, self.system, self.setting, self.benchmark), (runspec.machine, runspec.system, runspec.setting, runspec.benchmark)) 


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
    
    def evalResults(self, out):
        machines   = set()
        jobs       = set()
        configs    = set()
        systems    = {}
        benchmarks = set() 
        
        for project in self.projects.values():
            jobs.add(project.job)
            for runspecs in project.runspecs.values():
                for runspec in runspecs:
                    machines.add(runspec.machine)
                    configs.add(runspec.system.config)
                    if not runspec.system in systems: systems[runspec.system] = []
                    systems[runspec.system].append(runspec.setting)
                    benchmarks.add(runspec.benchmark)
        
        out.write('<result>\n')
        
        for machine in sorted(machines):
            machine.toXml(out, "\t")
        for config in sorted(configs):
            config.toXml(out, "\t")
        for system in sorted(systems.keys(), cmp=lambda s: s.order):
            system.toXml(out, "\t", systems[system])
        for job in sorted(jobs):
            job.toXml(out, "\t")
        for benchmark in sorted(benchmarks):
            benchmark.toXml(out, "\t")
        
        for project in self.projects.values():
            out.write('\t<project name="{0.name}" job="{0.job.name}">\n'.format(project))
            jobGen = project.job.scriptGen()
            jobs.add(project.job)
            for runspecs in project.runspecs.values():
                for runspec in runspecs:
                    out.write('\t\t<runspec machine="{0.machine.name}" system="{0.system.name}" version="{0.system.version}" benchmark="{0.benchmark.name}" setting="{0.setting.name}">\n'.format(runspec))
                    for classname in sorted(runspec.benchmark.instances):
                        out.write('\t\t\t<class id="{0.id}">\n'.format(classname))
                        instances =  runspec.benchmark.instances[classname]
                        for instance in instances:
                            out.write('\t\t\t\t<instance id="{0.id}">\n'.format(instance))
                            jobGen.evalResults(out, "\t\t\t\t\t", runspec, instance)
                            out.write('\t\t\t\t</instance>\n')
                        out.write('\t\t\t</class>\n')
                    out.write('\t\t</runspec>\n')
            out.write('\t</project>\n')
        out.write('</result>\n')
         
class Project:
    def __init__(self, name):
        self.name      = name
        self.runspecs  = {}
        self.runscript = None
        self.job       = None

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
            scriptGen.genStartScript(os.path.join(self.path(), machine))
    
    def __hash__(self):
        return hash(self.name)

    def __cmp__(self, project):
        return cmp(project.name, project.name)


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
    
