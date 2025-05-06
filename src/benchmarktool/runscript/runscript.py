"""
This module contains classes that describe a run script.
It can be used to create scripts to start a benchmark
specified by the run script.
"""

__author__ = "Roland Kaminski"

import os
from typing import Any, Optional

# needed to embed measurements functions via exec
# pylint: disable-msg=W0611
import benchmarktool.config  # @UnusedImport
from benchmarktool import tools
from benchmarktool.tools import Sortable, cmp

# pylint: enable-msg=W0611
# pylint: disable=too-many-lines


class Machine(Sortable):
    """
    Describes a machine.
    """

    def __init__(self, name: str, cpu: str, memory: str):
        """
        Initializes a machine.

        Keyword arguments:
        name   - A name uniquely identifying the machine
        cpu    - Some cpu description
        memory - Some memory description
        """
        self.name = name
        self.cpu = cpu
        self.memory = memory

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump the (pretty-printed) XML-representation of the machine.

        Keyword arguments:
        out    - Output stream to write to
        indent - Amount of indentation
        """
        out.write('{1}<machine name="{0.name}" cpu="{0.cpu}" memory="{0.memory}"/>\n'.format(self, indent))

    def __hash__(self) -> int:
        """
        Return a hash values using the name of the machine.
        """
        return hash(self.name)

    def __cmp__(self, machine: "Machine") -> int:
        """
        Compare two machines.
        """
        return cmp(self.name, machine.name)


class System(Sortable):
    """
    Describes a system. This includes a solver description
    together with a set of settings.
    """

    def __init__(self, name: str, version: str, measures: str, order: int):
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
        self.name = name
        self.version = version
        self.measures = measures
        self.order = order
        self.settings: dict[str, Setting] = {}
        self.config: Optional[Config] = None

    def add_setting(self, setting: "Setting") -> None:
        """
        Adds a given setting to the system.
        """
        setting.system = self
        self.settings[setting.name] = setting

    def to_xml(self, out: Any, indent: str, settings: Optional[list["Setting"]] = None) -> None:
        """
        Dump the (pretty-printed) XML-representation of the system.

        Keyword arguments:
        out      - Output stream to write to
        indent   - Amount of indentation
        settings - If None all the settings of the system are printed,
                   otherwise the given settings are printed
        """
        assert isinstance(self.config, Config)
        out.write(
            (
                f'{indent}<system name="{self.name}" version="{self.version}" '
                f'measures="{self.measures}" config="{self.config.name}">\n'
            )
        )
        if settings is None:
            settings = list(self.settings.values())
        for setting in sorted(settings, key=lambda s: s.order):
            setting.to_xml(out, indent + "\t")
        out.write("{0}</system>\n".format(indent))

    def __hash__(self) -> int:
        """
        Calculates a hash value for the system using its name and version.
        """
        return hash((self.name, self.version))

    def __cmp__(self, system: "System") -> int:
        """
        Compares two systems using name and version.
        """
        return cmp((self.name, self.version), (system.name, system.version))


# pylint: disable=too-many-instance-attributes, too-many-positional-arguments
class Setting(Sortable):
    """
    Describes a setting for a system. This are command line options
    that can be passed to the system. Additionally, settings can be tagged.
    """

    def __init__(
        self,
        name: str,
        cmdline: str,
        tag: set[str],
        order: int,
        procs: Optional[int],
        ppn: Optional[int],
        pbstemplate: str,
        attr: dict[str, Any],
    ):
        """
        Initializes a system.

        name        - A name uniquely identifying a setting.
                      (In the scope of a system)
        cmdline     - A string of command line options
        tag         - A set of tags
        order       - An integer specifying the order of settings
                      (This should denote the occurrence in the job specification.
                      Again in the scope of a system.)
        procs       - Number of processes used by the solver (pbs only)
        ppn         - Processes per node (pbs only)
        pbstemplate - Path to pbs-template file (pbs only, related to mpi-version)
        attr        - A dictionary of additional optional attributes.
        """
        self.name = name
        self.cmdline = cmdline
        self.tag = tag
        self.order = order
        self.procs = procs
        self.ppn = ppn
        self.pbstemplate = pbstemplate
        self.attr = attr
        self.system: "System"

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the setting.

        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """
        tag = " ".join(sorted(self.tag))
        out.write('{1}<setting name="{0.name}" cmdline="{0.cmdline}" tag="{2}"'.format(self, indent, tag))
        if self.procs is not None:
            out.write(' {0}="{1}"'.format("procs", self.procs))
        if self.ppn is not None:
            out.write(' {0}="{1}"'.format("ppn", self.ppn))
        if self.pbstemplate is not None:
            out.write(' {0}="{1}"'.format("pbstemplate", self.pbstemplate))
        for key, val in self.attr.items():
            out.write(' {0}="{1}"'.format(key, val))
        out.write("/>\n")

    def __hash__(self) -> int:
        """
        Calculates a hash value for the setting using its name.
        """
        return hash(self.name)

    def __cmp__(self, setting: "Setting") -> int:
        """
        Compares two settings using their names.
        """
        return cmp(self.name, setting.name)


class Job(Sortable):
    """
    Base class for all jobs.
    """

    def __init__(self, name: str, timeout: int, runs: int, attr: dict[str, Any]):
        """
        Initializes a job.

        Keyword arguments:
        name    - A unique name for a job
        timeout - A timeout in seconds for individual benchmark runs
        runs    - The number of runs per benchmark
        attr    - A dictionary of arbitrary attributes
        """
        self.name = name
        self.timeout = timeout
        self.runs = runs
        self.attr = attr

    def _to_xml(self, out: Any, indent: str, xmltag: str, extra: str) -> None:
        """
        Helper function to dump a (pretty-printed) XML-representation of a job.

        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        xmltag  - Tag name for the job
        extra   - Additional arguments for the job
        """
        out.write(
            '{1}<{2} name="{0.name}" timeout="{0.timeout}" runs="{0.runs}"{3}'.format(self, indent, xmltag, extra)
        )
        for key, val in self.attr.items():
            out.write(' {0}="{1}"'.format(key, val))
        out.write("/>\n")

    def __hash__(self) -> int:
        """
        Calculates a hash value for the job using its name.
        """
        return hash(self.name)

    def __cmp__(self, job: "Job") -> int:
        """
        Compares two jobs using their names.
        """
        return cmp(self.name, job.name)


# pylint: disable=too-few-public-methods
class Run(Sortable):
    """
    Base class for all runs.

    Class members:
    path - Path that holds the target location for start scripts
    root - directory relative to the location of the run's path.
    """

    def __init__(self, path: str):
        """
        Initializes a run.

        Keyword arguments:
        path - A path that holds the location
               where the individual start scripts for the job shall be generated
        """
        self.path = path
        self.root = os.path.relpath(".", self.path)


# pylint: disable=too-many-instance-attributes, too-many-positional-arguments, too-few-public-methods
class SeqRun(Run):
    """
    Describes a sequential run.

    Class members:
    run      - The number of the run
    job      - A reference to the job description
    runspec  - A reference to the run description
    instance - A reference to the instance to benchmark
    file     - A relative path to the instance
    args     - The command line arguments for this run
    solver   - The solver for this run
    timeout  - The timeout of this run
    """

    def __init__(self, path: str, run: int, job: "Job", runspec: "Runspec", instance: "Benchmark.Instance"):
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
        self.run = run
        self.job = job
        self.runspec = runspec
        self.instance = instance
        self.file = os.path.relpath(self.instance.path(), self.path)
        self.encodings = " ".join([f'"{os.path.relpath(e, self.path)}"' for e in instance.encodings])
        self.args = self.runspec.setting.cmdline
        self.solver = self.runspec.system.name + "-" + self.runspec.system.version
        self.timeout = self.job.timeout


class ScriptGen:
    """
    A class providing basic functionality to generate
    start scripts for arbitrary jobs and evaluation of results.
    """

    def __init__(self, job: "Job"):
        """
        Initializes the script generator.

        Keyword arguments:
        job - A reference to the associated job.
        """
        self.skip = False
        self.job = job
        self.startfiles: list[tuple["Runspec", str, str]] = []

    def set_skip(self, skip: bool) -> None:
        """
        Set whether to skip.

        Keyword arguments:
        skip - Whether to skip.
        """
        self.skip = skip

    def _path(self, runspec: "Runspec", instance: "Benchmark.Instance", run: int) -> str:
        """
        Returns the relative path to the start script location.

        Keyword arguments:
        runspec  - The run specification for the start script
        instance - The benchmark instance for the start script
        run      - The number of the run for the start script
        """
        return os.path.join(runspec.path(), instance.benchclass.name, instance.name, "run%d" % run)

    def add_to_script(self, runspec: "Runspec", instance: "Benchmark.Instance") -> None:
        """
        Creates a new start script for the given instance.

        Keyword arguments:
        runspec  - The run specification for the start script
        instance - The benchmark instance for the start script
        """
        skip = self.skip
        if runspec.system.config:
            for run in range(1, self.job.runs + 1):
                path = self._path(runspec, instance, run)
                tools.mkdir_p(path)
                startpath = os.path.join(path, "start.sh")
                finish = os.path.join(path, ".finished")
                if skip and os.path.isfile(finish):
                    continue
                with open(runspec.system.config.template, "r", encoding="utf8") as f:
                    template = f.read()
                with open(startpath, "w", encoding="utf8") as startfile:
                    startfile.write(template.format(run=SeqRun(path, run, self.job, runspec, instance)))
                self.startfiles.append((runspec, path, "start.sh"))
                tools.set_executable(startpath)

    def eval_results(self, out: Any, indent: str, runspec: "Runspec", instance: "Benchmark.Instance") -> None:
        """
        Parses the results of a given benchmark instance and outputs them as XML.

        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        runspec - The run specification of the benchmark
        runspec - The benchmark instance
        """
        for run in range(1, self.job.runs + 1):
            out.write('{0}<run number="{1}">\n'.format(indent, run))
            # result parser call
            result = getattr(benchmarktool.config, runspec.system.measures)(
                self._path(runspec, instance, run), runspec, instance
            )
            for key, valtype, val in sorted(result):
                out.write('{0}<measure name="{1}" type="{2}" val="{3}"/>\n'.format(indent + "\t", key, valtype, val))
            out.write("{0}</run>\n".format(indent))


class SeqScriptGen(ScriptGen):
    """
    A class that generates and evaluates start scripts for sequential runs.
    """

    def __init__(self, seqJob: "SeqJob"):
        """
        Initializes the script generator.

        Keyword arguments:
        seqJob - A reference to the associated sequential job.
        """
        ScriptGen.__init__(self, seqJob)

    # pylint: disable=line-too-long
    def gen_start_script(self, path: str) -> None:
        """
        Generates a start script that can be used to start all scripts
        generated using addToScript().

        Keyword arguments:
        path - The target location for the script
        """
        assert isinstance(self.job, SeqJob)
        tools.mkdir_p(path)
        with open(os.path.join(path, "start.py"), "w", encoding="utf8") as startfile:
            queue = ""
            comma = False
            for _, instpath, instname in self.startfiles:
                relpath = os.path.relpath(instpath, path)
                if comma:
                    queue += ","
                else:
                    comma = True
                queue += repr(os.path.join(relpath, instname))
            startfile.write(
                """\
#!/usr/bin/python -u

import optparse
import threading
import subprocess
import os
import sys
import signal
import time

queue = [{0}]

class Main:
    def __init__(self):
        self.running  = set()
        self.cores    = set()
        self.started  = 0
        self.total    = None
        self.finished = threading.Condition()
        self.coreLock = threading.Lock()
        c = 0
        while len(self.cores) < {1}:
            self.cores.add(c)
            c += 1
    
    def finish(self, thread):
        self.finished.acquire()
        self.running.remove(thread)
        with self.coreLock:
            self.cores.add(thread.core)
        self.finished.notify()
        self.finished.release()
   
    def start(self, cmd):
        core     = 0
        with self.coreLock:
            core = self.cores.pop()
        thread = Run(cmd, self, core)
        self.started += 1
        self.running.add(thread)
        print("({{0}}/{{1}}/{{2}}/{{4}}) {{3}}".format(len(self.running), self.started, self.total, cmd, core))
        thread.start()
    
    def run(self, queue):
        signal.signal(signal.SIGTERM, self.exit)
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        self.finished.acquire()
        self.total = len(queue)
        for cmd in queue:
            while len(self.running) >= {1}:
                self.finished.wait()
            self.start(cmd)
        while len(self.running) != 0:
            self.finished.wait()
        self.finished.release()

    def exit(self, *args):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        print("WARNING: it is not guaranteed that all processes will be terminated!")
        print("sending sigterm ...")
        os.killpg(os.getpgid(0), signal.SIGTERM)
        print("waiting 10s...")
        time.sleep(10)
        print("sending sigkill ...")
        os.killpg(os.getpgid(0), signal.SIGKILL)

class Run(threading.Thread):
    def __init__(self, cmd, main, core):
        threading.Thread.__init__(self)
        self.cmd  = cmd
        self.main = main
        self.core = core
        self.proc = None
    
    def run(self):
        path, script = os.path.split(self.cmd)
        openArgs = dict(cwd=path)
        if sys.version_info[:3] >= (3,2,0):
            openArgs["start_new_session"] = True
        else:
            openArgs["preexec_fn"] = os.setsid
        self.proc = subprocess.Popen(["bash", script, str(self.core)], **openArgs)
        self.proc.wait()
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
    m.run(queue)
""".format(
                    queue, self.job.parallel
                )
            )
        tools.set_executable(os.path.join(path, "start.py"))


class PbsScriptGen(ScriptGen):
    """
    A class that generates and evaluates start scripts for pbs runs.
    """

    class PbsScript:
        """
        Class realizing a pbs script.
        """

        def __init__(self, runspec: "Runspec", path: str, queue: list[str]):
            self.runspec = runspec
            self.path = path
            self.queue = queue
            self.num = 0
            self.time = 0  # = None, next() sets start values anyway, None only causes
            #         issues with typecheck
            self.startscripts = ""  # = None
            self.next()

        def write(self) -> None:
            """
            Write script.
            """
            if self.num > 0:
                assert isinstance(self.runspec.project, Project)
                assert isinstance(self.runspec.project.job, PbsJob)
                self.num = 0
                with open(self.runspec.setting.pbstemplate, "r", encoding="utf8") as f:
                    template = f.read()
                script = os.path.join(self.path, "start{0:04}.pbs".format(len(self.queue)))
                with open(script, "w", encoding="utf8") as f:
                    f.write(
                        template.format(
                            walltime=tools.pbs_time(self.runspec.project.job.walltime),
                            nodes=self.runspec.setting.procs,
                            ppn=self.runspec.setting.ppn,
                            jobs=self.startscripts,
                            cpt=self.runspec.project.job.cpt,
                            partition=self.runspec.project.job.partition,
                        )
                    )
                self.queue.append(script)

        def next(self) -> None:
            """
            Switch to and setup next script.
            """
            self.write()
            self.startscripts = ""
            self.num = 0
            self.time = 0

        def append(self, startfile: str) -> None:
            """
            Add startfile to list of jobs.
            """
            self.num += 1
            self.startscripts += startfile + "\n"

    def __init__(self, pbsJob: "PbsJob"):
        """
        Initializes the script generator.

        Keyword arguments:
        pbsJob - A reference to the associated sequential job.
        """
        ScriptGen.__init__(self, pbsJob)

    def gen_start_script(self, path: str) -> None:
        """
        Generates a start script that can be used to start all scripts
        generated using add_to_script().

        Keyword arguments:
        path - The target location for the script
        """
        assert isinstance(self.job, PbsJob)
        tools.mkdir_p(path)
        queue: list[str] = []
        pbs_scripts: dict[tuple[Optional[int], Optional[int], str, int, int, str], PbsScriptGen.PbsScript] = {}
        for runspec, instpath, instname in self.startfiles:
            assert isinstance(runspec.project, Project)
            assert isinstance(runspec.project.job, PbsJob)
            relpath = os.path.relpath(instpath, path)
            job_script = os.path.join(relpath, instname)
            pbs_key = (
                runspec.setting.ppn,
                runspec.setting.procs,
                runspec.setting.pbstemplate,
                runspec.project.job.walltime,
                runspec.project.job.cpt,
                runspec.project.job.partition,
            )

            if pbs_key not in pbs_scripts:
                pbs_script = PbsScriptGen.PbsScript(runspec, path, queue)
                pbs_scripts[pbs_key] = pbs_script
            else:
                pbs_script = pbs_scripts[pbs_key]

            if self.job.script_mode == "multi":
                if pbs_script.num > 0:
                    pbs_script.next()
                pbs_script.append(job_script)
            elif self.job.script_mode == "timeout":
                if pbs_script.time + runspec.project.job.timeout + 300 >= runspec.project.job.walltime:
                    pbs_script.next()
                pbs_script.time += runspec.project.job.timeout + 300
                pbs_script.append(job_script)

        for pbs_script in pbs_scripts.values():
            pbs_script.write()

        with open(os.path.join(path, "start.sh"), "w", encoding="utf8") as startfile:
            startfile.write(
                """#!/bin/bash\n\ncd "$(dirname $0)"\n"""
                + "\n".join(['sbatch "{0}"'.format(os.path.basename(x)) for x in queue])
            )
        tools.set_executable(os.path.join(path, "start.sh"))


class SeqJob(Job):
    """
    Describes a sequential job.
    """

    def __init__(self, name: str, timeout: int, runs: int, parallel: int, attr: dict[str, Any]):
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

    def script_gen(self) -> "SeqScriptGen":
        """
        Returns a class that can generate start scripts and evaluate benchmark results.
        (see SeqScriptGen)
        """
        return SeqScriptGen(self)

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the sequential job.

        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """
        extra = ' parallel="{0.parallel}"'.format(self)
        Job._to_xml(self, out, indent, "seqjob", extra)


class PbsJob(Job):
    """
    Describes a pbs job.
    """

    def __init__(
        self,
        name: str,
        timeout: int,
        runs: int,
        script_mode: str,
        walltime: int,
        cpt: int,
        partition: str,
        attr: dict[str, Any],
    ):
        """
        Initializes a parallel job description.

        Keyword arguments:
        name        - A unique name for a job
        timeout     - A timeout in seconds for individual benchmark runs
        runs        - The number of runs per benchmark
        script_mode - Specifies the script generation mode
        walltime    - The walltime for a job submitted via PBS
        cpt         - Number of cpus per task for SLURM
        partition   - Partition to be used in the clusters (kr by default)
        attr        - A dictionary of arbitrary attributes
        """
        Job.__init__(self, name, timeout, runs, attr)
        self.script_mode = script_mode
        self.walltime = walltime
        self.cpt = cpt
        self.partition = partition

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the parallel job.

        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """
        extra = ' script_mode="{0.script_mode}" walltime="{0.walltime}" cpt="{0.cpt}" partition="{0.partition}"'.format(
            self
        )
        Job._to_xml(self, out, indent, "pbsjob", extra)

    def script_gen(self) -> "PbsScriptGen":
        """
        Returns a class that can generate start scripts and evaluate benchmark results.
        (see SeqScriptGen)
        """
        return PbsScriptGen(self)


class Config(Sortable):
    """
    Describes a configuration. Currently, this only specifies a template
    that is used for start script generation.
    """

    def __init__(self, name: str, template: str):
        """
        Keyword arguments:
        name     - A name uniquely identifying the configuration
        template - A path to the template for start script generation
        """
        self.name = name
        self.template = template

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the configuration.

        Keyword arguments:
        out     - Output stream to write to
        indent  - Amount of indentation
        """
        out.write('{1}<config name="{0.name}" template="{0.template}"/>\n'.format(self, indent))

    def __hash__(self) -> int:
        """
        Calculates a hash value for the configuration using its name.
        """
        return hash(self.name)

    def __cmp__(self, config: "Config") -> int:
        """
        Compares two configurations using their names.
        """
        return cmp(self.name, config.name)


class Benchmark(Sortable):
    """
    Describes a benchmark. This includes a set of classes
    that describe where to find particular instances.
    """

    class Class(Sortable):
        """
        Describes a benchmark class.
        """

        def __init__(self, name: str):
            """
            Initializes a benchmark class.

            Keyword arguments:
            name - A name uniquely identifying a benchmark class (per benchmark).
            """
            self.name = name
            self.id: Optional[int] = None

        def __cmp__(self, other: "Benchmark.Class") -> int:
            """
            Compares two benchmark classes using their names.
            """
            return cmp(self.name, other.name)

        def __hash__(self) -> int:
            """
            Calculates a hash value for the benchmark class using its name.
            """
            return hash(self.name)

    class Instance(Sortable):
        """
        Describes a benchmark instance.
        """

        def __init__(self, location: str, benchclass: "Benchmark.Class", name: str, encodings: set[str]):
            """
            Initializes a benchmark instance. The instance name uniquely identifies
            an instance (per benchmark class).

            Keyword arguments:
            location  - The location of the benchmark instance.
            classname - The class name of the instance
            name  - The name of the instance
            encodings - Encoding associated with the instance
            """
            self.location = location
            self.benchclass = benchclass
            self.name = name
            self.id: Optional[int] = None
            self.encodings = encodings

        def to_xml(self, out: Any, indent: str) -> None:
            """
            Dump a (pretty-printed) XML-representation of the configuration.

            Keyword arguments:
            out     - Output stream to write to
            indent  - Amount of indentation
            """
            out.write('{1}<instance name="{0.name}" id="{0.id}"/>\n'.format(self, indent))

        def __cmp__(self, instance: "Benchmark.Instance") -> int:
            """
            Compares tow instances using the instance name.
            """
            return cmp(self.name, instance.name)

        def __hash__(self) -> int:
            """
            Calculates a hash using the instance name.
            """
            return hash(self.name)

        def path(self) -> str:
            """
            Returns the location of the instance by concatenating
            location, class name and instance name.
            """
            return os.path.join(self.location, self.benchclass.name, self.name)

    class Folder:
        """
        Describes a folder that should recursively be scanned for benchmarks.
        """

        def __init__(self, path: str):
            """
            Initializes a benchmark folder.

            Keyword arguments:
            path - The location of the folder
            """
            self.path = path
            self.prefixes: set[str] = set()
            self.encodings: set[str] = set()

        def add_ignore(self, prefix: str) -> None:
            """
            Can be used to ignore certain sub-folders or instances
            by giving a path prefix that shall be ignored.

            Keyword arguments:
            prefix - The prefix to be ignored
            """
            self.prefixes.add(os.path.normpath(prefix))

        def add_encoding(self, file: str) -> None:
            """
            Can be used to add encodings, which will be called together
            with all instances in this folder.

            Keyword arguments:
            file - The encoding file
            """
            self.encodings.add(os.path.normpath(file))

        def _skip(self, root: str, path: str) -> bool:
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

        def init(self, benchmark: "Benchmark") -> None:
            """
            Recursively scans the folder and adds all instances found to the given benchmark.

            Keyword arguments:
            benchmark - The benchmark to be populated.
            """
            for root, dirs, files in os.walk(self.path):
                relroot = os.path.relpath(root, self.path)
                sub = []
                for dirname in dirs:
                    if self._skip(relroot, dirname):
                        continue
                    sub.append(dirname)
                dirs[:] = sub
                for filename in files:
                    if self._skip(relroot, filename):
                        continue
                    benchmark.add_instance(self.path, relroot, filename, self.encodings)

    class Files:
        """
        Describes a set of individual files in a benchmark.
        """

        def __init__(self, path: str):
            """
            Initializes to the empty set of files.

            Keyword arguments:
            path - Root path, all file paths are relative to this path
            """
            self.path = path
            self.files: set[str] = set()
            self.encodings: set[str] = set()

        def add_file(self, path: str) -> None:
            """
            Adds a file to the set of files.

            Keyword arguments:
            path - Location of the file
            """
            self.files.add(os.path.normpath(path))

        def add_encoding(self, file: str) -> None:
            """
            Can be used to add encodings, which will be called together
            with all instances in these files.

            Keyword arguments:
            file - The encoding file
            """
            self.encodings.add(os.path.normpath(file))

        def init(self, benchmark: "Benchmark") -> None:
            """
            Adds a files in the set to the given benchmark (if they exist).

            Keyword arguments:
            benchmark - The benchmark to be populated
            """
            for path in self.files:
                if os.path.exists(os.path.join(self.path, path)):
                    relroot, filename = os.path.split(path)
                    benchmark.add_instance(self.path, relroot, filename, self.encodings)

    def __init__(self, name: str):
        """
        Initializes an empty benchmark set.

        Keyword arguments:
        name - The name of the benchmark set
        """
        self.name = name
        self.elements: list[Any] = []
        self.instances: dict[Benchmark.Class, set[Benchmark.Instance]] = {}
        self.initialized = False

    def add_element(self, element: Any) -> None:
        """
        Adds elements to the benchmark, e.g, files or folders.

        Keyword arguments:
        element - The element to add
        """
        self.elements.append(element)

    def add_instance(self, root: str, relroot: str, filename: str, encodings: set[str]) -> None:
        """
        Adds an instance to the benchmark set. (This function
        is called during initialization by the benchmark elements)

        Keyword arguments:
        root     - The root folder of the instance
        relroot  - The folder relative to the root folder
        filename - The filename of the instance
        encodings - The encodings associated to the instance
        """
        classname = Benchmark.Class(relroot)
        if classname not in self.instances:
            self.instances[classname] = set()
        self.instances[classname].add(Benchmark.Instance(root, classname, filename, encodings))

    def init(self) -> None:
        """
        Populates the benchmark set with instances specified by the
        benchmark elements added.
        """
        if not self.initialized:
            for element in self.elements:
                element.init(self)
            classid = 0
            for classname in sorted(self.instances.keys()):
                classname.id = classid
                classid += 1
                instanceid = 0
                for instance in sorted(self.instances[classname]):
                    instance.id = instanceid
                    instanceid += 1
            self.initialized = True

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump the (pretty-printed) XML-representation of the benchmark set.

        Keyword arguments:
        out    - Output stream to write to
        indent - Amount of indentation
        """
        self.init()
        out.write('{1}<benchmark name="{0}">\n'.format(self.name, indent))
        for classname in sorted(self.instances.keys()):
            instances = self.instances[classname]
            out.write('{1}<class name="{0.name}" id="{0.id}">\n'.format(classname, indent + "\t"))
            for instance in sorted(instances):
                instance.to_xml(out, indent + "\t\t")
            out.write("{0}</class>\n".format(indent + "\t"))
        out.write("{0}</benchmark>\n".format(indent))

    def __hash__(self) -> int:
        """
        Return a hash values using the name of the machine.
        """
        return hash(self.name)

    def __cmp__(self, benchmark: "Benchmark") -> int:
        """
        Compare two benchmark sets.
        """
        return cmp(benchmark.name, benchmark.name)


class Runspec(Sortable):
    """
    Describes a run specification. This specifies system, settings, machine
    to run a benchmark with.
    """

    def __init__(self, machine: "Machine", setting: "Setting", benchmark: "Benchmark"):
        """
        Initializes a run specification.

        Keyword arguments:
        machine   - The machine to run on
        setting   - The setting to run with (includes system)
        benchmark - The benchmark
        """
        self.machine = machine
        self.setting = setting
        self.system = setting.system
        self.benchmark = benchmark
        self.project: Optional[Project] = None

    def path(self) -> str:
        """
        Returns an output path under which start scripts
        and benchmark results are stored.
        """
        assert isinstance(self.project, Project)
        name = self.setting.system.name + "-" + self.setting.system.version + "-" + self.setting.name
        return os.path.join(self.project.path(), self.machine.name, "results", self.benchmark.name, name)

    def gen_scripts(self, script_gen: "ScriptGen") -> None:
        """
        Generates start scripts needed to start the benchmark described
        by this run specification. This will simply add all instances
        and their associated encodings to the given script generator.

        Keyword arguments:
        script_gen - A generator that is responsible for the start script generation
        """
        self.benchmark.init()
        for instances in self.benchmark.instances.values():
            for instance in instances:
                script_gen.add_to_script(self, instance)

    def __cmp__(self, runspec: "Runspec") -> int:
        """
        Compares two run specifications.
        """
        return cmp(
            (self.machine, self.system, self.setting, self.benchmark),
            (runspec.machine, runspec.system, runspec.setting, runspec.benchmark),
        )


class Project(Sortable):
    """
    Describes a benchmark project, i.e., a set of run specifications
    that belong together.
    """

    def __init__(self, name: str):
        """
        Initializes an empty project.

        Keyword arguments:
        name - The name of the project
        """
        self.name = name
        self.runspecs: dict[str, list[Runspec]] = {}
        self.runscript: Optional[Runscript] = None
        self.job: Optional[Job] = None

    def add_runtag(self, machine_name: str, benchmark_name: str, tag: str) -> None:
        """
        Adds a run tag to the project, i.e., a set of run specifications
        identified by certain tags.

        Keyword arguments:
        machine_name   - The machine to run on
        benchmark_name - The benchmark set to evaluate
        tag            - The tags of systems+settings to run
        """
        disj = TagDisj(tag)
        assert isinstance(self.runscript, Runscript)
        for system in self.runscript.systems.values():
            for setting in system.settings.values():
                if disj.match(setting.tag):
                    self.add_runspec(machine_name, system.name, system.version, setting.name, benchmark_name)

    def add_runspec(
        self, machine_name: str, system_name: str, version: str, setting_name: str, benchmark_name: str
    ) -> None:
        """
        Adds a run specification, described by machine, system+settings, and benchmark set,
        to the project.

        Keyword arguments:
        machine_name   - The machine to run on
        system_name    - The system to evaluate
        version        - The version of the system
        setting_name   - The settings to run the system with
        benchmark_name - The benchmark set to evaluate
        """
        assert isinstance(self.runscript, Runscript)
        runspec = Runspec(
            self.runscript.machines[machine_name],
            self.runscript.systems[(system_name, version)].settings[setting_name],
            self.runscript.benchmarks[benchmark_name],
        )
        runspec.project = self
        if not machine_name in self.runspecs:
            self.runspecs[machine_name] = []
        self.runspecs[machine_name].append(runspec)

    def path(self) -> str:
        """
        Returns an output path under which start scripts
        and benchmark results are stored for this project.
        """
        assert isinstance(self.runscript, Runscript)
        return os.path.join(self.runscript.path(), self.name)

    def gen_scripts(self, skip: bool) -> None:
        """
        Generates start scripts for this project.
        """
        assert isinstance(self.job, (SeqJob, PbsJob))
        for machine, runspecs in self.runspecs.items():
            script_gen = self.job.script_gen()
            script_gen.set_skip(skip)
            for runspec in runspecs:
                runspec.gen_scripts(script_gen)
            script_gen.gen_start_script(os.path.join(self.path(), machine))

    def __hash__(self) -> int:
        """
        Return a hash values using the name of the project.
        """
        return hash(self.name)

    def __cmp__(self, project: "Project") -> int:
        """
        Compares two projects.
        """
        return cmp(project.name, project.name)


class Runscript:
    """
    Describes a run script, i.e., everything that is needed
    to start and evaluate a set of benchmarks.
    """

    def __init__(self, output: str):
        """
        Initializes an empty run script.

        Keyword arguments:
        output - The output folder to store start scripts and result files
        """
        self.output = output
        self.jobs: dict[str, Job] = {}
        self.projects: dict[str, Project] = {}
        self.machines: dict[str, Machine] = {}
        self.systems: dict[tuple[str, str], System] = {}
        self.configs: dict[str, Config] = {}
        self.benchmarks: dict[str, Benchmark] = {}

    def add_machine(self, machine: "Machine") -> None:
        """
        Adds a given machine to the run script.

        Keyword arguments:
        machine - The machine to be added
        """
        self.machines[machine.name] = machine

    def add_system(self, system: "System", config: str) -> None:
        """
        Adds a given system to the run script.
        Additionally, each system will be associated with a config.

        Keyword arguments:
        system - The system to add
        config - The name of the config of the system
        """
        system.config = self.configs[config]
        self.systems[(system.name, system.version)] = system

    def add_config(self, config: "Config") -> None:
        """
        Adds a configuration to the run script.

        Keyword arguments:
        config - The config to be added
        """
        self.configs[config.name] = config

    def add_benchmark(self, benchmark: "Benchmark") -> None:
        """
        Adds a benchmark to the run script.

        Keyword arguments:
        benchmark - The benchmark to be added
        """
        self.benchmarks[benchmark.name] = benchmark

    def add_job(self, job: "Job") -> None:
        """
        Adds a job to the runscript.

        Keyword arguments:
        job - The job to be added
        """
        self.jobs[job.name] = job

    def add_project(self, project: "Project", job_name: str) -> None:
        """
        Adds a project to therun script.
        Additionally, the project ill be associated with a job.

        Keyword arguments:
        project - The project to add
        job     - The name of the job of the project
        """
        project.runscript = self
        project.job = self.jobs[job_name]
        self.projects[project.name] = project

    def gen_scripts(self, skip: bool) -> None:
        """
        Generates the start scripts for all benchmarks described by
        this run script.
        """
        for project in self.projects.values():
            project.gen_scripts(skip)

    def path(self) -> str:
        """
        Returns the output path of this run script.
        """
        return self.output

    # pylint: disable=too-many-branches
    def eval_results(self, out: Any) -> None:
        """
        Evaluates and prints the results of all benchmarks described
        by this run script. (Start scripts have to be run first.)

        Keyword arguments:
        out - Output stream for xml output
        """
        machines: set[Machine] = set()
        jobs: set[SeqJob | PbsJob] = set()
        configs: set[Config] = set()
        systems: dict[System, list[Setting]] = {}
        benchmarks: set[Benchmark] = set()

        for project in self.projects.values():
            assert isinstance(project.job, (SeqJob, PbsJob))
            jobs.add(project.job)
            for runspecs in project.runspecs.values():
                for runspec in runspecs:
                    assert isinstance(runspec.system.config, Config)
                    machines.add(runspec.machine)
                    configs.add(runspec.system.config)
                    if not runspec.system in systems:
                        systems[runspec.system] = []
                    systems[runspec.system].append(runspec.setting)
                    benchmarks.add(runspec.benchmark)

        out.write("<result>\n")

        for machine in sorted(machines):
            machine.to_xml(out, "\t")
        for config in sorted(configs):
            config.to_xml(out, "\t")
        for system in sorted(systems.keys(), key=lambda s: s.order):
            system.to_xml(out, "\t", systems[system])
        for job in sorted(jobs):
            job.to_xml(out, "\t")
        for benchmark in sorted(benchmarks):
            benchmark.to_xml(out, "\t")

        for project in self.projects.values():
            assert isinstance(project.job, (SeqJob, PbsJob))
            out.write('\t<project name="{0.name}" job="{0.job.name}">\n'.format(project))
            job_gen = project.job.script_gen()
            jobs.add(project.job)
            for runspecs in project.runspecs.values():
                for runspec in runspecs:
                    out.write(
                        (
                            '\t\t<runspec machine="{0.machine.name}" system="{0.system.name}" '
                            'version="{0.system.version}" benchmark="{0.benchmark.name}" '
                            'setting="{0.setting.name}">\n'
                        ).format(runspec)
                    )
                    for classname in sorted(runspec.benchmark.instances):
                        out.write('\t\t\t<class id="{0.id}">\n'.format(classname))
                        instances = runspec.benchmark.instances[classname]
                        for instance in instances:
                            out.write('\t\t\t\t<instance id="{0.id}">\n'.format(instance))
                            job_gen.eval_results(out, "\t\t\t\t\t", runspec, instance)
                            out.write("\t\t\t\t</instance>\n")
                        out.write("\t\t\t</class>\n")
                    out.write("\t\t</runspec>\n")
            out.write("\t</project>\n")
        out.write("</result>\n")


class TagDisj:
    """Represents tags in form of a disjunctive normal form."""

    ALL = 1

    def __init__(self, tag: str):
        """
        Transforms a string into a disjunctive normal form of tags.
        Spaces between tags are interpreted as conjunctions and |
        is interpreted as disjunction. The special value "*all*"
        matches everything.

        Keyword arguments:
        tag - a string representing a disjunctive normal form of tags
        """
        self.tag: Any  # int | list[frozenset[...]]
        if tag == "*all*":
            self.tag = self.ALL
        else:
            self.tag = []
            tag_disj = tag.split("|")
            for tag_conj in tag_disj:
                tag_list = tag_conj.split(None)
                self.tag.append(frozenset(tag_list))

    def match(self, tag: Any) -> bool:
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
