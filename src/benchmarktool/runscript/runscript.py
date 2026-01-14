"""
This module contains classes that describe a run script.
It can be used to create scripts to start a benchmark
specified by the run script.
"""

__author__ = "Roland Kaminski"

import importlib
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from functools import total_ordering
from types import ModuleType
from typing import Any, Iterator, Optional

from benchmarktool import tools

# pylint: disable=too-many-lines


@dataclass(order=True, frozen=True)
class Machine:
    """
    Describes a machine.

    Attributes:
        name (str):   Name of the machine.
        cpu (str):    Some cpu description.
        memory (str): Some memory description.
    """

    name: str
    cpu: str = field(compare=False)
    memory: str = field(compare=False)

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump the (pretty-printed) XML-representation of the machine.

        Attributes:
            out (Any):    Output stream to write to.
            indent (str): Amount of indentation.
        """
        out.write(f'{indent}<machine name="{self.name}" cpu="{self.cpu}" memory="{self.memory}"/>\n')


@dataclass(order=True, frozen=True)
class System:
    """
    Describes a system. This includes a solver description
    together with a set of settings.

    Attributes:
        name (str):      The name of the system.
        version (str):   The version of the system.
        measures (str):  A string specifying the measurement function.
                         This must be a function given in the config.
        order (int):     An integer used to order different system.
                         This integer should denote the occurrence in
                         the run specification.
        config (Config): The system configuration.
        settings (dict[str, Setting]): Settings used with the system.
    """

    name: str
    version: str
    measures: str = field(compare=False)
    order: int = field(compare=False)
    config: "Config" = field(compare=False)
    settings: dict[str, "Setting"] = field(default_factory=dict, compare=False)

    def add_setting(self, setting: "Setting") -> None:
        """
        Adds a given setting to the system.
        """
        self.settings[setting.name] = setting

    def to_xml(self, out: Any, indent: str, settings: Optional[list["Setting"]] = None) -> None:
        """
        Dump the (pretty-printed) XML-representation of the system.

        Attributes:
            out (Any):    Output stream to write to.
            indent (str): Amount of indentation.
            settings (Optional[list["Setting"]]): If None all the settings of the system are printed,
                                                  otherwise the given settings are printed.
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
        out.write(f"{indent}</system>\n")


# pylint: disable=too-many-instance-attributes
@dataclass(order=True, frozen=True, kw_only=True)
class Setting:
    """
    Describes a setting for a system. This are command line options
    that can be passed to the system. Additionally, settings can be tagged.

    Attributes:
        name (str):     A name uniquely identifying a setting.
                        (In the scope of a system)
        cmdline (str):  A string of command line options.
        tag (set[str]): A set of tags.
        order (int):    An integer specifying the order of settings.
                        (This should denote the occurrence in the job specification.
                        Again in the scope of a system.)
        dist_template (str):             Path to dist-template file. (dist only, related to mpi-version)
        attr (dict[str, Any]):           A dictionary of additional optional attributes.
        dist_options (Optional[str]):    Additional dist options for this setting.
        encodings (dict[str, set[str]]): Encodings used with this setting, keyed with tags.
    """

    name: str
    cmdline: str = field(compare=False)
    tag: set[str] = field(compare=False)
    order: int = field(compare=False)
    dist_template: str = field(compare=False)
    attr: dict[str, Any] = field(compare=False)

    dist_options: str = field(default="", compare=False)
    encodings: dict[str, set[str]] = field(compare=False, default_factory=dict)

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the setting.

        Attributes:
            out (Any):    Output stream to write to.
            indent (str): Amount of indentation.
        """
        tag = " ".join(sorted(self.tag))
        out.write(f'{indent}<setting name="{self.name}" cmdline="{self.cmdline}" tag="{tag}"')
        if self.dist_template is not None:
            out.write(f' dist_template="{self.dist_template}"')
        for key, val in self.attr.items():
            out.write(f' {key}="{val}"')
        if self.dist_options != "":
            out.write(f' dist_options="{self.dist_options}"')
        out.write(">\n")
        for enctag, encodings in self.encodings.items():
            for enc in sorted(encodings):
                if enctag == "_default_":
                    out.write(f'{indent}\t<encoding file="{enc}"/>\n')
                else:
                    out.write(f'{indent}\t<encoding file="{enc}" tag="{enctag}"/>\n')
        out.write(f"{indent}</setting>\n")


@total_ordering
@dataclass(eq=False, frozen=True, kw_only=True)
class Job:
    """
    Base class for all jobs.

    Attributes:
        name (str):    A unique name for a job.
        timeout (int): A timeout in seconds for individual benchmark runs.
        memout (int):  A memory limit in MB for individual benchmark runs (20GB).
        runs (int):    The number of runs per benchmark.
        template_options (str): Template options.
        attr (dict[str, Any]): A dictionary of arbitrary attributes.
    """

    name: str
    timeout: int = field(compare=False)
    runs: int = field(compare=False)
    attr: dict[str, Any] = field(compare=False)
    memout: int = field(compare=False, default=20000)
    template_options: str = field(compare=False, default="")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Job):
            raise RuntimeError("Cannot compare Job to non-Job")
        return self.name == other.name

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Job):
            raise RuntimeError("Cannot compare Job to non-Job")
        return self.name < other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def _to_xml(self, out: Any, indent: str, xmltag: str, extra: str) -> None:
        """
        Helper function to dump a (pretty-printed) XML-representation of a job.

        Attributes:
            out (Any):    Output stream to write to.
            indent (str): Amount of indentation.
            xmltag (str): Tag name for the job.
            extra (str):  Additional arguments for the job.
        """
        out.write(
            f'{indent}<{xmltag} name="{self.name}" timeout="{self.timeout}" memout="{self.memout}" '
            f'runs="{self.runs}" template_options="{self.template_options}"{extra}'
        )
        for key, val in self.attr.items():
            out.write(f' {key}="{val}"')
        out.write("/>\n")

    def script_gen(self) -> Any:
        """
        Has to be overwritten by subclasses.
        """
        raise NotImplementedError


class ScriptGen:
    """
    A class providing basic functionality to generate
    start scripts for arbitrary jobs and evaluation of results.
    """

    def __init__(self, job: "Job"):
        """
        Initializes the script generator.

        Attributes:
            job (Job): A reference to the associated job.
        """
        self.skip = False
        self.job = job
        self.startfiles: list[tuple["Runspec", str, str]] = []

    def set_skip(self, skip: bool) -> None:
        """
        Set whether to skip.

        Attributes:
            skip (bool): Whether to skip.
        """
        self.skip = skip

    def _path(self, runspec: "Runspec", instance: "Benchmark.Instance", run: int) -> str:
        """
        Returns the relative path to the start script location.

        Attributes:
            runspec (Runspec):             The run specification for the start script.
            instance (Benchmark.Instance): The benchmark instance for the start script.
            run (int):                     The number of the run for the start script.
        """
        return os.path.join(runspec.path(), instance.benchclass.name, instance.name, f"run{run}")

    def add_to_script(self, runspec: "Runspec", instance: "Benchmark.Instance") -> None:
        """
        Creates a new start script for the given instance.

        Attributes:
            runspec (Runspec):             The run specification for the start script.
            instance (Benchmark.Instance): The benchmark instance for the start script.
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

                template_options = self.job.template_options
                if template_options != "":
                    template_options = " \\\n\t".join(template_options.split(",")) + " \\\n"
                else:
                    template_options = ""
                encodings = instance.encodings
                encodings = encodings.union(runspec.setting.encodings.get("_default_", set()))
                for i in instance.enctags:
                    encodings = encodings.union(runspec.setting.encodings.get(i, set()))
                encodings_str = " ".join([f'"{os.path.relpath(e, path)}"' for e in sorted(encodings)])

                with open(startpath, "w", encoding="utf8") as startfile:
                    startfile.write(
                        template.format(
                            root=os.path.relpath(".", path),
                            options=template_options,
                            memout=self.job.memout,
                            timeout=self.job.timeout,
                            solver=runspec.system.name + "-" + runspec.system.version,
                            args=runspec.setting.cmdline,
                            files=" ".join([f'"{os.path.relpath(i, path)}"' for i in sorted(instance.paths())]),
                            encodings=encodings_str,
                        )
                    )
                self.startfiles.append((runspec, path, "start.sh"))
                tools.set_executable(startpath)

    def eval_results(
        self,
        *,
        out: Any,
        indent: str,
        runspec: "Runspec",
        instance: "Benchmark.Instance",
        result_parser: Optional[ModuleType],
        parx: int = 2,
    ) -> None:
        """
        Parses the results of a given benchmark instance and outputs them as XML.

        Attributes:
            out (Any):                     Output stream to write to.
            indent (str):                  Amount of indentation.
            runspec (Runspec):             The run specification of the benchmark.
            instance (Benchmark.Instance): The benchmark instance.
            parx (int):                    Factor for penalized-average-runtime score.
        """

        for run in range(1, self.job.runs + 1):
            out.write(f'{indent}<run number="{run}">\n')
            # result parser call
            try:
                result: dict[str, tuple[str, Any]] = result_parser.parse(  # type: ignore
                    self._path(runspec, instance, run), runspec, instance, run
                )
                # penalized-average-runtime score
                if all(key in result for key in ["time", "timeout"]):
                    value = parx * self.job.timeout if result["timeout"][1] else result["time"][1]
                    result[f"par{parx}"] = ("float", value)

                for key, (valtype, val) in sorted(result.items()):
                    out.write(f'{indent}\t<measure name="{key}" type="{valtype}" val="{val}"/>\n')
            except AttributeError:
                # skip if parser import failed or no parse function is defined
                pass

            out.write(f"{indent}</run>\n")


class SeqScriptGen(ScriptGen):
    """
    A class that generates and evaluates start scripts for sequential runs.
    """

    def __init__(self, seq_job: "SeqJob"):
        """
        Initializes the script generator.

        Attributes:
            seqJob (SeqJob): A reference to the associated sequential job.
        """
        ScriptGen.__init__(self, seq_job)

    # pylint: disable=line-too-long
    def gen_start_script(self, path: str) -> None:
        """
        Generates a start script that can be used to start all scripts
        generated using addToScript().

        Attributes:
            path (str): The target location for the script.
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
                f"""\
#!/usr/bin/python -u

import optparse
import threading
import subprocess
import os
import sys
import signal
import time

queue = [{queue}]

class Main:
    def __init__(self):
        self.running  = set()
        self.cores    = set()
        self.started  = 0
        self.total    = None
        self.finished = threading.Condition()
        self.coreLock = threading.Lock()
        c = 0
        while len(self.cores) < {self.job.parallel}:
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
        print(f"({{len(self.running)}}/{{self.started}}/{{self.total}}/{{core}}) {{cmd}}")
        thread.start()

    def run(self, queue):
        signal.signal(signal.SIGTERM, self.exit)
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        self.finished.acquire()
        self.total = len(queue)
        for cmd in queue:
            while len(self.running) >= {self.job.parallel}:
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
"""
            )
        tools.set_executable(os.path.join(path, "start.py"))


class DistScriptGen(ScriptGen):
    """
    A class that generates and evaluates start scripts for dist runs.
    """

    class DistScript:
        """
        Class realizing a dist script.
        """

        def __init__(self, runspec: "Runspec", path: str, queue: list[str]):
            """
            Initializes dist script.

            Attributes:
                runspec (Runspec): Associated runspecification.
                path (str):        Target location for the script.
                queue (list[str]): Script queue.
            """
            self.runspec = runspec
            self.path = path
            self.queue = queue
            self.num = 0
            self.time = 0  # = None, next() sets start values anyway,
            # None only causes issues with typecheck
            self.startscripts = ""  # = None
            self.next()

        def write(self) -> None:
            """
            Write script.
            """
            if self.num > 0:
                assert isinstance(self.runspec.project, Project)
                assert isinstance(self.runspec.project.job, DistJob)
                self.num = 0
                with open(self.runspec.setting.dist_template, "r", encoding="utf8") as f:
                    template = f.read()
                script = os.path.join(self.path, f"start{len(self.queue):04}.dist")
                if self.runspec.setting.dist_options != "":
                    dist_options = "\n".join(self.runspec.setting.dist_options.split(",")) + "\n"
                else:
                    dist_options = ""
                with open(script, "w", encoding="utf8") as f:
                    f.write(
                        template.format(
                            walltime=tools.seconds_to_slurm_time(self.runspec.project.job.walltime),
                            jobs=self.startscripts,
                            cpt=self.runspec.project.job.cpt,
                            partition=self.runspec.project.job.partition,
                            dist_options=dist_options,
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

            Attributes:
                startfile (str): Start script.
            """
            self.num += 1
            self.startscripts += startfile + "\n"

    def __init__(self, dist_job: "DistJob"):
        """
        Initializes the script generator.

        Attributes:
            distJob (DistJob): A reference to the associated sequential job.
        """
        ScriptGen.__init__(self, dist_job)

    def gen_start_script(self, path: str) -> None:
        """
        Generates a start script that can be used to start all scripts
        generated using add_to_script().

        Attributes:
            path (str): The target location for the script.
        """
        assert isinstance(self.job, DistJob)
        tools.mkdir_p(path)
        queue: list[str] = []
        dist_scripts: dict[tuple[str, Optional[str], int, int, str], DistScriptGen.DistScript] = {}
        for runspec, instpath, instname in self.startfiles:
            assert isinstance(runspec.project, Project)
            assert isinstance(runspec.project.job, DistJob)
            relpath = os.path.relpath(instpath, path)
            job_script = os.path.join(relpath, instname)
            dist_key = (
                runspec.setting.dist_template,
                runspec.setting.dist_options,
                runspec.project.job.walltime,
                runspec.project.job.cpt,
                runspec.project.job.partition,
            )

            if dist_key not in dist_scripts:
                dist_script = DistScriptGen.DistScript(runspec, path, queue)
                dist_scripts[dist_key] = dist_script
            else:
                dist_script = dist_scripts[dist_key]

            if self.job.script_mode == "multi":
                if dist_script.num > 0:
                    dist_script.next()
                dist_script.append(job_script)
            elif self.job.script_mode == "timeout":
                if dist_script.time + runspec.project.job.timeout + 300 >= runspec.project.job.walltime:
                    dist_script.next()
                dist_script.time += runspec.project.job.timeout + 300
                dist_script.append(job_script)

        for dist_script in dist_scripts.values():
            dist_script.write()

        with open(os.path.join(path, "start.sh"), "w", encoding="utf8") as startfile:
            startfile.write(
                '#!/bin/bash\n\ncd "$(dirname $0)"\n' + "\n".join([f'sbatch "{os.path.basename(x)}"' for x in queue])
            )
        tools.set_executable(os.path.join(path, "start.sh"))


@dataclass(eq=False, frozen=True, kw_only=True)
class SeqJob(Job):
    """
    Describes a sequential job.

    Attributes:
        name (str):    A unique name for a job.
        timeout (int): A timeout in seconds for individual benchmark runs.
        memout (int):  A memory limit in MB for individual benchmark runs (20GB).
        runs (int):    The number of runs per benchmark.
        template_options (str): Template options.
        attr (dict[str, Any]): A dictionary of arbitrary attributes.
        parallel (int): The number of runs that can be started in parallel.
    """

    parallel: int = field(compare=False)

    def script_gen(self) -> "SeqScriptGen":
        """
        Returns a class that can generate start scripts and evaluate benchmark results.
        (see SeqScriptGen)
        """
        return SeqScriptGen(self)

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the sequential job.

        Attributes:
            out (Any):    Output stream to write to.
            indent (str): Amount of indentation.
        """
        extra = f' parallel="{self.parallel}"'
        Job._to_xml(self, out, indent, "seqjob", extra)


@dataclass(eq=False, frozen=True, kw_only=True)
class DistJob(Job):
    """
    Describes a dist job.

    Attributes:
        name (str):    A unique name for a job.
        timeout (int): A timeout in seconds for individual benchmark runs.
        memout (int):  A memory limit in MB for individual benchmark runs (20GB).
        runs (int):    The number of runs per benchmark.
        template_options (str): Template options.
        attr (dict[str, Any]): A dictionary of arbitrary attributes.
        script_mode (str):    Specifies the script generation mode.
        walltime (int):  The walltime for a distributed job.
        cpt (int):       Number of cpus per task for distributed jobs.
        partition (str): Partition to be used in the clusters (kr by default).
    """

    script_mode: str = field(compare=False)
    walltime: int = field(compare=False)
    cpt: int = field(compare=False)
    partition: str = field(compare=False, default="kr")

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the parallel job.

        Attributes:
            out (Any):    Output stream to write to
            indent (str): Amount of indentation
        """
        extra = (
            f' script_mode="{self.script_mode}" walltime="{self.walltime}" cpt="{self.cpt}" '
            f'partition="{self.partition}"'
        )
        Job._to_xml(self, out, indent, "distjob", extra)

    def script_gen(self) -> "DistScriptGen":
        """
        Returns a class that can generate start scripts and evaluate benchmark results.
        (see SeqScriptGen)
        """
        return DistScriptGen(self)


@dataclass(order=True, frozen=True)
class Config:
    """
    Describes a configuration. Currently, this only specifies a template
    that is used for start script generation.

    Attributes:
        name (str):     A name uniquely identifying the configuration.
        template (str): A path to the template for start script generation.
    """

    name: str
    template: str = field(compare=False)

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump a (pretty-printed) XML-representation of the configuration.

        Attributes:
            out (Any):    Output stream to write to.
            indent (str): Amount of indentation.
        """
        out.write(f'{indent}<config name="{self.name}" template="{self.template}"/>\n')


@dataclass(order=True, unsafe_hash=True)
class Benchmark:
    """
    Describes a benchmark. This includes a set of classes
    that describe where to find particular instances.

    Attributes:
        name (str):- The name of the benchmark set.
        elements (list[Any]): A list of all benchmark elements.
        instances (dict[benchmark.Class, set[Benchmark.Instance]]): A list of all benchmark instances.
        initialized (bool): Whether the benchmark set is initialized or not.
    """

    name: str
    elements: list[Any] = field(default_factory=list, compare=False)
    instances: dict["Benchmark.Class", set["Benchmark.Instance"]] = field(default_factory=dict, compare=False)
    initialized: bool = field(default=False, compare=False)

    @dataclass(order=True, frozen=True)
    class Class:
        """
        Describes a benchmark class.
        Attributes:
            name (str): A name uniquely identifying a benchmark class (per benchmark).
            id (int):   A numeric identifier.
        """

        name: str
        id: Optional[int] = field(default=None, compare=False)

    @dataclass(order=True, frozen=True)
    class Instance:
        """
        Describes a benchmark instance.

        Attributes:
            location (str):       The location of the benchmark instance.
            benchclass (Benchmark.Class): The class name of the instance.
            name (str):           The name of the instance.
            files set(str):       Instance files associated with the instance.
            encodings (set[str]): Encoding associated with the instance.
            enctags (set[str]):   Encoding tags associated with the instance.
            id (int):             A numeric identifier.
        """

        location: str = field(compare=False)
        benchclass: "Benchmark.Class" = field(compare=False)
        name: str
        files: set[str] = field(compare=False)
        encodings: set[str] = field(compare=False)
        enctags: set[str] = field(compare=False)
        id: Optional[int] = field(default=None, compare=False)

        def to_xml(self, out: Any, indent: str) -> None:
            """
            Dump a (pretty-printed) XML-representation of the configuration.

            Attributes:
                out (Any):    Output stream to write to
                indent (str): Amount of indentation
            """
            out.write(f'{indent}<instance name="{self.name}" id="{self.id}">\n')
            for instance in sorted(self.files):
                out.write(f'{indent}\t<file name="{instance}"/>\n')
            out.write(f"{indent}</instance>\n")

        def paths(self) -> Iterator[str]:
            """
            Returns the location of the instance files by concatenating
            location, class name and instance name.
            """
            for file in self.files:
                yield os.path.join(self.location, self.benchclass.name, file)

    class Folder:
        """
        Describes a folder that should recursively be scanned for benchmarks.
        """

        def __init__(self, path: str, group: bool = False):
            """
            Initializes a benchmark folder.

            Attributes:
                path (str):   The location of the folder.
                group (bool): Whether to group instances by their file name prefix.
            """
            self.path = path
            self.group = group
            self.prefixes: set[str] = set()
            self.encodings: set[str] = set()
            self.enctags: set[str] = set()

        def add_ignore(self, prefix: str) -> None:
            """
            Can be used to ignore certain sub-folders or instances
            by giving a path prefix that shall be ignored.

            Attributes:
                prefix (str): The prefix to be ignored.
            """
            self.prefixes.add(os.path.normpath(prefix))

        def add_encoding(self, file: str) -> None:
            """
            Can be used to add encodings, which will be called together
            with all instances in this folder.

            Attributes:
                file (str): The encoding file.
            """
            self.encodings.add(os.path.normpath(file))

        def add_enctags(self, tags: set[str]) -> None:
            """
            Can be used to add encoding tags, which refers to encodings
            specified by the setting, whic will be called together
            with all instances in this folder.

            Attributes:
                tag (set[str]): The encoding tags.
            """
            self.enctags = self.enctags.union(tags)

        def _skip(self, root: str, path: str) -> bool:
            """
            Returns whether a given path should be ignored.

            Attributes:
                root (str): The root path.
                path (str): Some path relative to the root path.
            """
            if path == ".svn":
                return True
            path = os.path.normpath(os.path.join(root, path))
            return path in self.prefixes

        def init(self, benchmark: "Benchmark") -> None:
            """
            Recursively scans the folder and adds all instances found to the given benchmark.

            Attributes:
                benchmark (Benchmark): The benchmark to be populated.
            """
            for root, dirs, files in os.walk(self.path):
                relroot = os.path.relpath(root, self.path)
                sub = []
                instances: dict[str, set[str]] = {}
                for dirname in dirs:
                    if self._skip(relroot, dirname):
                        continue
                    sub.append(dirname)
                dirs[:] = sub
                for filename in files:
                    if self._skip(relroot, filename):
                        continue
                    m = re.match(r"^(([^.]+(?:\.[^.]+)*?)(?:\.[^.]+)?)\.[^.]+$", filename)
                    if m is None:
                        sys.stderr.write(f"*** WARNING: skipping invalid file name: {filename}\n")
                        continue
                    if self.group:
                        # remove last 2 file extensions, file.1.txt -> file
                        group = m.group(2)
                    else:
                        # remove last file extension, file.1.txt -> file.1
                        group = m.group(1)
                    if group not in instances:
                        instances[group] = set()
                    instances[group].add(filename)
                for group, instfiles in instances.items():
                    benchmark.add_instance(
                        root=self.path,
                        relroot=relroot,
                        files=(group, instfiles),
                        encodings=self.encodings,
                        enctags=self.enctags,
                    )

    class Files:
        """
        Describes a set of individual files in a benchmark.
        """

        def __init__(self, path: str):
            """
            Initializes to the empty set of files.

            Attributes:
                path (str): Root path, all file paths are relative to this path.
            """
            self.path = path
            self.files: dict[str, set[str]] = {}
            self.encodings: set[str] = set()
            self.enctags: set[str] = set()

        def add_file(self, path: str, group: Optional[str] = None) -> None:
            """
            Adds a file to the set of files.

            Attributes:
                path (str):            Location of the file.
                group (Optional[str]): Instance group.
            """
            if group is None:
                m = re.match(r"^([^.]+(?:\.[^.]+)*)\.[^.]+$", os.path.basename(path))
                if m is None:
                    sys.stderr.write(f"*** WARNING: skipping invalid file name: {path}\n")
                    return
                # remove file extension, file.1.txt -> file.1
                group = m.group(1)
            if group not in self.files:
                self.files[group] = set()
            self.files[group].add(os.path.normpath(path))

        def add_encoding(self, file: str) -> None:
            """
            Can be used to add encodings, which will be called together
            with all instances in these files.

            Attributes:
                file (str): The encoding file.
            """
            self.encodings.add(os.path.normpath(file))

        def add_enctags(self, tags: set[str]) -> None:
            """
            Can be used to add encoding tags, which refers to encodings
            specified by the setting, whic will be called together
            with all instances in this folder.

            Attributes:
                tag (set[str]): The encoding tags.
            """
            self.enctags = self.enctags.union(tags)

        def init(self, benchmark: "Benchmark") -> None:
            """
            Adds a files in the set to the given benchmark (if they exist).

            Attributes:
                benchmark (Benchmark): The benchmark to be populated.
            """
            for group, files in self.files.items():
                if not all(os.path.exists(os.path.join(self.path, file)) for file in files):
                    sys.stderr.write(f"*** WARNING: skipping instance '{group}' due to missing files!\n")
                    continue
                paths = list(map(os.path.split, sorted(files)))
                if len(set(map(lambda x: x[0], paths))) != 1:
                    sys.stderr.write(
                        f"*** WARNING: skipping instance '{group}' due to inconsistent file paths!\n"
                        "Grouped files must be located in the same folder.\n"
                    )
                    continue
                relroot = paths[0][0]
                benchmark.add_instance(
                    root=self.path,
                    relroot=relroot,
                    files=(group, set(map(lambda x: x[1], paths))),
                    encodings=self.encodings,
                    enctags=self.enctags,
                )

    def add_element(self, element: Any) -> None:
        """
        Adds elements to the benchmark, e.g, files or folders.

        Attributes:
            element (Any): The element to add.
        """
        self.elements.append(element)

    def add_instance(
        self, *, root: str, relroot: str, files: tuple[str, set[str]], encodings: set[str], enctags: set[str]
    ) -> None:
        """
        Adds an instance to the benchmark set. (This function
        is called during initialization by the benchmark elements)

        Attributes:
            root (str):                  The root folder of the instance.
            relroot (str):               The folder relative to the root folder.
            files (tuple[str,set[str]]): The name and files of the instance.
            encodings (set[str]):        The encodings associated to the instance.
            enctags (set[str]):          The encoding tags associated to the instance.
        """
        classname = Benchmark.Class(relroot)
        if classname not in self.instances:
            self.instances[classname] = set()
        self.instances[classname].add(Benchmark.Instance(root, classname, files[0], files[1], encodings, enctags))

    def init(self) -> None:
        """
        Populates the benchmark set with instances specified by the
        benchmark elements added.
        """
        if not self.initialized:
            for element in self.elements:
                element.init(self)
            id_instances: dict["Benchmark.Class", set["Benchmark.Instance"]] = {}
            classid = 0
            for classname in sorted(self.instances.keys()):
                id_class = Benchmark.Class(classname.name, classid)
                id_instances[id_class] = set()
                classid += 1
                instanceid = 0
                for instance in sorted(self.instances[classname]):
                    id_instances[id_class].add(
                        Benchmark.Instance(
                            instance.location,
                            id_class,
                            instance.name,
                            instance.files,
                            instance.encodings,
                            instance.enctags,
                            instanceid,
                        )
                    )
                    instanceid += 1
            self.instances = id_instances
            self.initialized = True

    def to_xml(self, out: Any, indent: str) -> None:
        """
        Dump the (pretty-printed) XML-representation of the benchmark set.

        Attributes:
            out (Any):    Output stream to write to.
            indent (str): Amount of indentation.
        """
        self.init()
        out.write(f'{indent}<benchmark name="{self.name}">\n')
        for classname in sorted(self.instances.keys()):
            instances = self.instances[classname]
            out.write(f'{indent}\t<class name="{classname.name}" id="{classname.id}">\n')
            for instance in sorted(instances):
                instance.to_xml(out, indent + "\t\t")
            out.write(f"{indent}\t</class>\n")
        out.write(f"{indent}</benchmark>\n")


@dataclass(order=True, frozen=True)
class Runspec:
    """
    Describes a run specification. This specifies machine, system, settings, project
    to run a benchmark with.

    Attributes:
        machine (Machine):     The machine to run on.
        system (System):       The system to run with.
        setting (Setting):     The setting to run with.
        benchmark (Benchmark): The benchmark.
        project (Project):     The associated project.
    """

    machine: "Machine"
    system: "System"
    setting: "Setting"
    benchmark: "Benchmark"
    project: "Project"

    def path(self) -> str:
        """
        Returns an output path under which start scripts
        and benchmark results are stored.
        """
        name = f"{self.system.name}-{self.system.version}-{self.setting.name}"
        return os.path.join(self.project.path(), self.machine.name, "results", self.benchmark.name, name)

    def gen_scripts(self, script_gen: "ScriptGen") -> None:
        """
        Generates start scripts needed to start the benchmark described
        by this run specification. This will simply add all instances
        and their associated encodings to the given script generator.

        Attributes:
            script_gen (ScriptGen): A generator that is responsible for the start script generation.
        """
        self.benchmark.init()
        for instances in self.benchmark.instances.values():
            for instance in instances:
                script_gen.add_to_script(self, instance)


@dataclass(order=True, frozen=True)
class Project:
    """
    Describes a benchmark project, i.e., a set of run specifications
    that belong together.
    Attributes:
        name (str):                            The name of the project.
        runscript (Runscript):                 Associated runscript.
        job (Job):                             Associated job.
        runspecs (dict[str, list['Runspec']]): Run specifications of the project.
    """

    name: str
    runscript: "Runscript" = field(compare=False)
    job: Job = field(compare=False)
    runspecs: dict[str, list["Runspec"]] = field(default_factory=dict, compare=False)

    def add_runtag(self, machine_name: str, benchmark_name: str, tag: str) -> None:
        """
        Adds a run tag to the project, i.e., a set of run specifications
        identified by certain tags.

        Attributes:
            machine_name (str):   The machine to run on.
            benchmark_name (str): The benchmark set to evaluate.
            tag (str):            The tags of systems+settings to run.
        """
        disj = TagDisj(tag)
        assert isinstance(self.runscript, Runscript)
        for system in self.runscript.systems.values():
            for setting in system.settings.values():
                if disj.match(setting.tag):
                    self.add_runspec(
                        machine_name=machine_name,
                        system_name=system.name,
                        system_version=system.version,
                        setting_name=setting.name,
                        benchmark_name=benchmark_name,
                    )

    def add_runspec(
        self, *, machine_name: str, system_name: str, system_version: str, setting_name: str, benchmark_name: str
    ) -> None:
        """
        Adds a run specification, described by machine, system+settings, and benchmark set,
        to the project.

        Attributes:
            machine_name (str):   The machine to run on.
            system_name (str):    The system to evaluate.
            version (str):        The version of the system.
            setting_name (str):   The settings to run the system with.
            benchmark_name (str): The benchmark set to evaluate.
        """
        runspec = Runspec(
            self.runscript.machines[machine_name],
            self.runscript.systems[(system_name, system_version)],
            self.runscript.systems[(system_name, system_version)].settings[setting_name],
            self.runscript.benchmarks[benchmark_name],
            self,
        )
        if not machine_name in self.runspecs:
            self.runspecs[machine_name] = []
        self.runspecs[machine_name].append(runspec)

    def path(self) -> str:
        """
        Returns an output path under which start scripts
        and benchmark results are stored for this project.
        """
        return os.path.join(self.runscript.path(), self.name)

    def gen_scripts(self, skip: bool) -> None:
        """
        Generates start scripts for this project.
        """
        for machine, runspecs in self.runspecs.items():
            script_gen = self.job.script_gen()
            script_gen.set_skip(skip)
            for runspec in runspecs:
                runspec.gen_scripts(script_gen)
            script_gen.gen_start_script(os.path.join(self.path(), machine))


class Runscript:
    """
    Describes a run script, i.e., everything that is needed
    to start and evaluate a set of benchmarks.
    """

    def __init__(self, output: str):
        """
        Initializes an empty run script.

        Attributes:
            output (str): The output folder to store start scripts and result files.
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

        Attributes:
            machine (Machine): The machine to be added.
        """
        self.machines[machine.name] = machine

    def add_system(self, system: "System") -> None:
        """
        Adds a given system to the run script.

        Attributes:
            system (System): The system to add.
        """
        self.systems[(system.name, system.version)] = system

    def add_config(self, config: "Config") -> None:
        """
        Adds a configuration to the run script.

        Attributes:
            config (Config): The config to be added.
        """
        self.configs[config.name] = config

    def add_benchmark(self, benchmark: "Benchmark") -> None:
        """
        Adds a benchmark to the run script.

        Attributes:
            benchmark (Benchmark): The benchmark to be added.
        """
        self.benchmarks[benchmark.name] = benchmark

    def add_job(self, job: "Job") -> None:
        """
        Adds a job to the runscript.

        Attributes:
            job (Job): The job to be added.
        """
        self.jobs[job.name] = job

    def add_project(self, project: "Project") -> None:
        """
        Adds a project to therun script.

        Attributes:
            project (Project): The project to add.
        """
        self.projects[project.name] = project

    def gen_scripts(self, skip: bool, overwrite: bool = False) -> None:
        """
        Generates the start scripts for all benchmarks described by
        this run script.
        """
        if os.path.isdir(self.output):
            if overwrite:
                shutil.rmtree(self.output)
            else:
                sys.stderr.write("*** ERROR: Output directory already exists.\n")
                sys.exit(1)
        for project in self.projects.values():
            project.gen_scripts(skip)

    def path(self) -> str:
        """
        Returns the output path of this run script.
        """
        return self.output

    def _get_result_parser(self, runspec: Runspec) -> Optional[ModuleType]:  # nocoverage
        """
        Helper function to obtain result parsers.

        Attributes:
            runspec (Runspec): The run specification.
        """
        result_parser: Optional[ModuleType] = None
        # dynamicly import result parser
        # prioritize local resultparsers over included in package
        rp_name = runspec.system.measures
        try:
            result_parser = tools.import_from_path(rp_name, os.path.join(os.getcwd(), "resultparsers", f"{rp_name}.py"))
        except FileNotFoundError:
            try:
                result_parser = importlib.import_module(f"benchmarktool.resultparser.{rp_name}")
            except ModuleNotFoundError:
                sys.stderr.write(
                    f"*** WARNING: Import of resultparser '{rp_name}' for system "
                    f"'{runspec.system.name}-{runspec.system.version}' failed! "
                    "All runs using this parser will have no measures recorded!\n"
                )
        if result_parser is not None and not callable(getattr(result_parser, "parse", None)):
            sys.stderr.write(
                f"*** WARNING: Resultparser '{rp_name}' for system "
                f"'{runspec.system.name}-{runspec.system.version}' has no callable 'parse' function! "
                "All runs using this parser will have no measures recorded!\n"
            )
        return result_parser

    # pylint: disable=too-many-branches
    def eval_results(self, out: Any, parx: int = 2) -> None:
        """
        Evaluates and prints the results of all benchmarks described
        by this run script. (Start scripts have to be run first.)

        Attributes:
            out (Any): Output stream for xml output.
            parx (int): Factor for penalized-average-runtime score.
        """
        machines: set[Machine] = set()
        jobs: set[SeqJob | DistJob] = set()
        configs: set[Config] = set()
        systems: dict[System, list[Setting]] = {}
        benchmarks: set[Benchmark] = set()

        for project in self.projects.values():
            assert isinstance(project.job, (SeqJob, DistJob))
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
            assert isinstance(project.job, (SeqJob, DistJob))
            out.write(f'\t<project name="{project.name}" job="{project.job.name}">\n')
            job_gen = project.job.script_gen()
            jobs.add(project.job)
            for runspecs in project.runspecs.values():
                for runspec in runspecs:
                    out.write(
                        (
                            f'\t\t<runspec machine="{runspec.machine.name}" system="{runspec.system.name}" '
                            f'version="{runspec.system.version}" benchmark="{runspec.benchmark.name}" '
                            f'setting="{runspec.setting.name}">\n'
                        )
                    )
                    for classname in sorted(runspec.benchmark.instances):
                        out.write(f'\t\t\t<class id="{classname.id}">\n')
                        instances = runspec.benchmark.instances[classname]
                        for instance in instances:
                            out.write(f'\t\t\t\t<instance id="{instance.id}">\n')
                            job_gen.eval_results(
                                out=out,
                                indent="\t\t\t\t\t",
                                runspec=runspec,
                                instance=instance,
                                result_parser=self._get_result_parser(runspec),
                                parx=parx,
                            )
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

        Attributes:
            tag (str): a string representing a disjunctive normal form of tags.
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

        Attributes:
            tag (Any): a set of tags.
        """
        if self.tag == self.ALL:
            return True
        for conj in self.tag:
            if conj.issubset(tag):
                return True
        return False
