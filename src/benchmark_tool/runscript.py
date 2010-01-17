'''
Created on Jan 15, 2010

@author: Roland Kaminski
'''
import benchmark_tool

import tools
import os
import stat

class Machine:
    def __init__(self, name, cpu, memory):
        self.name   = name
        self.cpu    = cpu
        self.memory = memory

    def toXml(self, out, indent):
        out.write('{1}<machine name="{0.name}" cpu="{0.cpu}" memory="{0.memory}"/>\n'.format(self, indent))

    def __hash__(self):
        return hash(self.name)
        
    def __cmp__(self, machine):
        return self.name < machine.name
    
class System:
    def __init__(self, name, version, measures):
        self.name     = name
        self.version  = version
        self.measures = measures
        self.settings = {}
        self.config   = None
         
    def addSetting(self, setting):
        setting.system = self
        self.settings[setting.name] = setting
        
    def toXml(self, out, indent, settings = None):
        out.write('{1}<system name="{0.name}" version="{0.version}" measures="{0.measures}" config="{0.config.name}">\n'.format(self, indent))
        if settings == None: settings = self.settings
        for setting in settings:
            setting.toXml(out, indent + "\t")
        out.write('{0}<system/>\n'.format(indent))
        
    def __hash__(self):
        return hash(self.name)

    def __cmp__(self, system):
        return self.name < system.name

class Setting:
    def __init__(self, name, cmdline, tag, attr):
        self.name    = name
        self.cmdline = cmdline
        self.tag     = tag
        self.attr    = attr

    def toXml(self, out, indent):
        tag = " ".join(sorted(self.tag))
        out.write('{1}<setting name="{0.name}" cmdline="{0.cmdline}" tag="{2}"'.format(self, indent, tag))
        for key, val in self.attr.items():
            out.write(' {0}="{1}"'.format(key, val))
        out.write('/>\n')

    def __hash__(self):
        return hash(self.name)

    def __cmp__(self, setting):
        return self.name < setting.name

        
class Job:
    def __init__(self, name, timeout, runs, attr):
        self.name    = name
        self.timeout = timeout
        self.runs    = runs
        self.attr    = attr

    def _toXml(self, out, indent, xmltag, extra):
        out.write('{1}<{2} name="{0.name}" timeout="{0.timeout}" runs="{0.runs}"{3}'.format(self, indent, xmltag, extra))
        for key, val in self.attr.items():
            out.write(' {0}="{1}"'.format(key, val))
        out.write('/>\n')
        
    def __hash__(self):
        return hash(self.name)
    
    def __cmp__(self, job):
        return job.name < job.name

class Run:
    def __init__(self, path):
        self.path = path
    
    def root(self):
        return os.path.relpath(".", self.path)
    
class SeqRun(Run):
            
    def __init__(self, path, run, job, runspec, instance):
        Run.__init__(self, path)
        self.run      = run
        self.job      = job
        self.runspec  = runspec
        self.instance = instance
    
    def file(self):
        return os.path.relpath(self.instance.path(), self.path)
    
    def args(self):
        return self.runspec.setting.cmdline
    
    def solver(self):
        return self.runspec.system.name + "-" + self.runspec.system.version
    
    def timeout(self):
        return self.job.timeout
    
class SeqScriptGen:
    def __init__(self, seqJob):
        self.seqJob     = seqJob
        self.startfiles = []
    
    def path(self, runspec, instance, run):
        return os.path.join(runspec.path(), instance.classname.name, instance.instance, "run%d" % run)
        
    def addToScript(self, runspec, instance):
        import pyratemp
        for run in range(1, self.seqJob.runs + 1):
            path = self.path(runspec, instance, run)
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
        import benchmark_tool.config #@UnusedImport
        exec("func = benchmark_tool.config." + runspec.system.measures)
        for run in range(1, self.seqJob.runs + 1):
            out.write('{0}<run number="{1}">\n'.format(indent, run))
            result = func(self.path(runspec, instance, run)) #@UndefinedVariable
            for key, type, val in sorted(result):
                out.write('{0}<measure name="{1}" type="{2}" val="{3}"/>\n'.format(indent + "\t", key, type, val))
            out.write('{0}</run>\n'.format(indent))
    
    def genStartScript(self, path):
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
import multiprocessing
import subprocess
import os
import sys

queue = [%s]

def run(cmd):
    print(cmd)
    path, script = os.path.split(cmd)
    subprocess.Popen(["bash", script], cwd=path).wait()

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
    usage  = "usage: %%prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-g", "--gui", action="store_true", dest="gui", default=False, help="start gui to selectively start benchmarks") 

    opts, args = parser.parse_args(sys.argv[1:])
    if len(args) > 0: parser.error("no arguments expected")
    
    os.chdir(os.path.dirname(sys.argv[0]))
    if opts.gui: gui()
    pool = multiprocessing.Pool(processes=%d)
    pool.map(run, queue)
""" % (queue, self.seqJob.parallel))
        startfile.close()
        startstat = os.stat(os.path.join(path, "start.py"))
        os.chmod(os.path.join(path, "start.py"), startstat[0] | stat.S_IXUSR)
    
class SeqJob(Job):
    def __init__(self, name, timeout, runs, parallel, attr):
        Job.__init__(self, name, timeout, runs, attr)
        self.parallel = parallel
    
    def scriptGen(self):
        return SeqScriptGen(self) 

    def toXml(self, out, indent):
        extra = ' parallel="{0.parallel}"'.format(self)
        Job._toXml(self, out, indent, "seqjob", extra)

           
class PbsJob(Job):
    def __init__(self, name, timeout, runs, ppn, procs, script_mode, walltime, attr):
        Job.__init__(self, name, timeout, runs, attr)
        self.ppn         = ppn
        self.procs       = procs
        self.script_mode = script_mode
        self.walltime    = walltime

    def toXml(self, out, indent):
        procs    = " ".join(self.procs)
        extra = ' ppn="{0.ppn}" procs={1} script_mode="{0.script_mode}" walltime="{0.walltime}"'.format(self, procs)
        Job._toXml(self, out, indent, "pbsjob", extra)

class Config:
    def __init__(self, name, template):
        self.name     = name
        self.template = template

    def toXml(self, out, indent):
        out.write('{1}<config name="{0.name}" template="{0.template}"/>\n'.format(self, indent))

    def __hash__(self):
        return hash(self.name)
    
    def __cmp__(self, config):
        return config.name < config.name

class Benchmark:
    class Class:
        def __init__(self, name):
            self.name = name
            self.id   = None 

        def __cmp__(self, other):
            return self.name < other.name 

        def __hash__(self):
            return hash(self.name)
            
    class Instance:
        def __init__(self, location, classname, instance):
            self.location  = location
            self.classname = classname
            self.instance  = instance
            self.hash      = hash((classname, instance))
            self.id        = None

        def toXml(self, out, indent):
            out.write('{1}<instance name="{0.instance}" id="{0.id}"/>\n'.format(self, indent))

        def __cmp__(self, instance):
            return self.instance < instance.instance 

        def __hash__(self):
            return hash(self.instance)

        def path(self):
            return os.path.join(self.location, self.classname.name, self.instance)
        
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
                for dirname in dirs:
                    if self.skip(relroot, dirname): continue
                    sub.append(dirname)
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
        return benchmark.name < benchmark.name

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
        return (self.machine, self.system, self.setting, self.benchmark) < (runspec.machine, runspec.system, runspec.setting, runspec.benchmark) 


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
        for system in sorted(systems.keys()):
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
                    out.write('\t\t<runspec machine="{0.machine.name}" system="{0.system.name}" version="{0.system.version}" benchmark="{0.benchmark.name}">\n'.format(runspec))
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
        return project.name < project.name


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
    
