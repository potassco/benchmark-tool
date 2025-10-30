"""
Entry points for different components.
"""

import os
import subprocess
import sys
import time
from argparse import ArgumentParser, ArgumentTypeError, RawTextHelpFormatter, _SubParsersAction
from textwrap import dedent
from typing import Any

from benchmarktool.result.ipynb_gen import gen_ipynb
from benchmarktool.result.parser import Parser as ResParser
from benchmarktool.runscript.parser import Parser as RunParser


def formatter(prog: str) -> RawTextHelpFormatter:
    """
    Custom formatter for argparse help messages.

    Attributes:
        prog (str): The program name.
    """
    return RawTextHelpFormatter(prog, max_help_position=15, width=100)


def btool_conv(subparsers: "_SubParsersAction[ArgumentParser]") -> None:
    """
    Register conv subcommand.
    """

    def run(args: Any) -> None:
        p = ResParser()
        if args.resultfile:
            with open(args.resultfile, encoding="utf-8") as in_file:
                res = p.parse(in_file)
        else:
            res = p.parse(sys.stdin)
        export: bool = args.export
        if args.jupyter_notebook is not None:
            export = True
        ex_file = res.gen_office(args.output, args.projects, args.measures, export)
        if args.jupyter_notebook is not None and ex_file is not None:
            gen_ipynb(ex_file, args.jupyter_notebook)

    def parse_set(s: str) -> set[str]:
        return set(filter(None, (x.strip() for x in s.split(","))))

    def parse_measures(s: str) -> list[tuple[str, str | None]]:
        measures = []
        if s != "all":  # empty list = select all measures
            for x in s.split(","):
                parts = x.split(":", 1)
                if not parts[0]:
                    raise ArgumentTypeError(f"Invalid measure: '{x}'")
                measures.append((parts[0], parts[1] if len(parts) > 1 else None))
        return measures

    conv_parser = subparsers.add_parser(
        "conv",
        help="Convert results to ODS or other formats",
        description=dedent(
            """\
            Convert previously collected benchmark results to ODS file
            and optionally generate Jupyter notebook.
            """
        ),
        formatter_class=formatter,
    )

    conv_parser.register("type", "project_set", parse_set)
    conv_parser.register("type", "measure_list", parse_measures)

    conv_parser.add_argument("resultfile", nargs="?", type=str, help="Result file (default: stdin)")
    conv_parser.add_argument(
        "-o", "--output", default="out.ods", help="Name of generated ods file (default: out.ods)", metavar="<file.ods>"
    )
    conv_parser.add_argument(
        "-p",
        "--projects",
        type="project_set",
        default=set(),
        help="Projects to display (comma separated)\nBy default all projects are shown",
        metavar="<project[,project,...]>",
    )
    conv_parser.add_argument(
        "-m",
        "--measures",
        type="measure_list",
        default="time:t,timeout:to",
        help=dedent(
            """\
            Measures to display
            Comma separated list of form 'name[:{t,to,-}]' (optional argument determines coloring)
            Use '-m all' to display all measures
            (default: time:t,timeout:to)
            """
        ),
        metavar="<measure[:{t,to,-}][,measure[:{t,to,-}],...]>",
    )
    conv_parser.add_argument(
        "-e",
        "--export",
        action="store_true",
        help="Export instance data to parquet file (same name as ods file)",
    )
    conv_parser.add_argument(
        "-j",
        "--jupyter-notebook",
        type=str,
        nargs="?",
        help=dedent(
            """\
            Name of generated .ipynb file
            Can be started using 'jupyter notebook <notebook>'
            All dependencies for the notebook can be installed using 'pip install .[plot]'
            """
        ),
        metavar="<file.ipynb>",
    )
    conv_parser.set_defaults(func=run)


def btool_eval(subparsers: "_SubParsersAction[ArgumentParser]") -> None:
    """
    Register eval subcommand.
    """

    def run(args: Any) -> None:
        p = RunParser()
        run = p.parse(args.runscript)
        run.eval_results(sys.stdout, args.par_x)

    eval_parser = subparsers.add_parser(
        "eval",
        help="Collect results",
        description="Collect benchmark results belonging to a runscript.",
        formatter_class=formatter,
    )
    eval_parser.add_argument("runscript", type=str, help="Runscript file", metavar="<runscript.xml>")
    eval_parser.add_argument(
        "--par-x",
        type=int,
        default=2,
        dest="par_x",
        help="Add penalized-average-runtime score factor as measure (default: 2)",
        metavar="<n>",
    )
    eval_parser.set_defaults(func=run)


def btool_gen(subparsers: "_SubParsersAction[ArgumentParser]") -> None:
    """
    Register gen subcommand.
    """

    def run(args: Any) -> None:
        p = RunParser()
        run = p.parse(args.runscript)
        run.gen_scripts(args.exclude)

    gen_parser = subparsers.add_parser(
        "gen",
        help="Generate scripts from runscript",
        description="Generate benchmark scripts defined by a runscript.",
        formatter_class=formatter,
    )
    gen_parser.add_argument("runscript", type=str, help="Runscript file", metavar="<runscript.xml>")
    gen_parser.add_argument("-e", "--exclude", action="store_true", help="Exclude finished runs")
    gen_parser.set_defaults(func=run)


def btool_run_dist(subparsers: "_SubParsersAction[ArgumentParser]") -> None:  # nocoverage
    """
    Run distributed jobs from a folder.
    """

    def running_jobs(user: str) -> int:
        result = subprocess.run(
            ["squeue", "-u", user, "-h", "-o", "%j"],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        return len([f for f in result.stdout.strip().splitlines() if f])

    def run(args: Any) -> None:
        pending = [
            f for f in os.listdir(args.folder) if os.path.isfile(os.path.join(args.folder, f)) and f.endswith(".dist")
        ]
        print(f"Found {len(pending)} jobs to dispatch.")
        while pending:
            jobs = running_jobs(args.user)
            while jobs < args.jobs and pending:
                job = pending[0]
                res = subprocess.run(["sbatch", job], cwd=args.folder, check=False)
                if res.returncode != 0:
                    print(f"Failed to submit {job}, try again later.")
                    break
                print(f"Submitted {job}")
                pending.pop(0)
                jobs += 1
            time.sleep(args.wait)
        print("All jobs submitted.")

    parser = subparsers.add_parser(
        "run-dist",
        help="Run distributed jobs",
        description="Dispatch all distributed jobs (*.dist files) in a given folder.",
        formatter_class=formatter,
    )
    parser.add_argument(
        "folder",
        help="Folder with *.dist files to dispatch",
        type=str,
        metavar="<folder>",
    )
    parser.add_argument(
        "-u",
        "--user",
        type=str,
        default=os.environ.get("USER", "unknown"),
        help="Username for job querying (default: current user)",
        metavar="<user>",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        help="Maximum number of jobs running at once",
        type=int,
        default=100,
        metavar="<n>",
    )
    parser.add_argument(
        "-w",
        "--wait",
        help="Time to wait between checks in seconds",
        type=int,
        default=1,
        metavar="<n>",
    )
    parser.set_defaults(func=run)


def btool_verify(subparsers: Any) -> None:  # nocoverage
    """
    Register verify subcommand.

    Checks benchmark results for runlim errors and re-runs such instances.
    """

    def find_runlim_errors(folder: str) -> list[str]:
        error_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file == "runsolver.watcher":
                    watcher_path = os.path.join(root, file)
                    with open(watcher_path, encoding="utf-8") as f:
                        if "runlim error" in f.read():
                            error_files.append(watcher_path)
        return error_files

    def run(args: Any) -> None:
        folder = args.folder
        if not os.path.isdir(folder):
            print("Error: provided folder doesn't exist", file=sys.stderr)
            sys.exit(1)

        if error_files := find_runlim_errors(folder):
            for watcher_file in error_files:
                finished_file = os.path.join(os.path.dirname(watcher_file), ".finished")
                if os.path.isfile(finished_file):
                    os.remove(finished_file)
                    print(f"Removed: {finished_file}")
                else:
                    print(f"Pending: {os.path.dirname(finished_file)}")

        else:
            print("No runlim errors found")

    parser = subparsers.add_parser(
        "verify",
        help="Check for runlim errors and re-run failed instances",
        description=dedent(
            """\
            Checks benchmark results in the given folder for runlim errors
            and removes .finished files for affected instances.
            Use 'btool gen -e <runscript.xml>' to re-generate new start scripts
            which exclude finished/valid runs.
            """
        ),
    )
    parser.add_argument("folder", type=str, help="Folder containing the benchmark results", metavar="<folder>")
    parser.set_defaults(func=run)


def get_parser() -> ArgumentParser:
    """
    Get parser.
    """
    parser = ArgumentParser(
        prog="btool",
        description="Benchmark Tool CLI",
        formatter_class=formatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    btool_conv(subparsers)
    btool_eval(subparsers)
    btool_gen(subparsers)
    btool_run_dist(subparsers)
    btool_verify(subparsers)

    return parser


def main() -> None:  # nocoverage
    """
    Entry point for benchmark tool CLI.
    """
    parser = get_parser()

    args = parser.parse_args()
    args.func(args)
