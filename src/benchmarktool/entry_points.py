"""
Entry points for different components.
"""

import importlib.metadata
import os
import shutil
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
        ex_file = res.gen_spreadsheet(args.output, args.projects, args.measures, export, args.max_col_width)
        if args.jupyter_notebook is not None and ex_file is not None:
            gen_ipynb(ex_file, args.jupyter_notebook)

    def parse_set(s: str) -> set[str]:
        return set(filter(None, (x.strip() for x in s.split(","))))

    def parse_measures(s: str) -> dict[str, Any]:
        measures = {}
        if s != "all":  # empty list = select all measures
            for x in s.split(","):
                parts = x.split(":", 1)
                if not parts[0]:
                    raise ArgumentTypeError(f"Invalid measure: '{x}'")
                measures[parts[0]] = parts[1] if len(parts) > 1 else None
        return measures

    conv_parser = subparsers.add_parser(
        "conv",
        help="Convert results to XLSX or other formats",
        description=dedent(
            """\
            Convert previously collected benchmark results to XLSX
            spreadsheet and optionally generate Jupyter notebook.
            """
        ),
        formatter_class=formatter,
    )

    conv_parser.register("type", "project_set", parse_set)
    conv_parser.register("type", "measure_list", parse_measures)

    conv_parser.add_argument("resultfile", nargs="?", type=str, help="Result file (default: stdin)")
    conv_parser.add_argument(
        "-o",
        "--output",
        default="out.xlsx",
        help="Name of generated xlsx file (default: %(default)s)",
        metavar="<file.xlsx>",
    )
    conv_parser.add_argument(
        "--max-col-width",
        type=int,
        default=300,
        help="Maximum column width for spreadsheet (default: %(default)d)",
        metavar="<n>",
        dest="max_col_width",
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
            (default: %(default)s)
            """
        ),
        metavar="<measure[:{t,to,-}][,measure[:{t,to,-}],...]>",
    )
    conv_parser.add_argument(
        "-e",
        "--export",
        action="store_true",
        help="Export instance data to parquet file (same name as .xlsx file)",
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
        help="Add penalized-average-runtime score factor as measure (default: %(default)d)",
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


def btool_init(subparsers: "_SubParsersAction[ArgumentParser]") -> None:  # nocoverage
    """
    Register init subcommand.
    """

    def copy_dir(src_dir: str, dst_dir: str, overwrite: bool = False) -> None:
        """
        Copy directory src_dir to dst_dir.
        By default existing files are not overwritten.

        Attributes:
            src_dir (str): Source directory path.
            dst_dir (str): Destination directory path.
            overwrite (bool): Whether to overwrite existing files.
        """
        if not os.path.isdir(src_dir) or not os.path.isdir(dst_dir):
            raise SystemExit("Source and target must be directories.")
        for root, dirs, files in os.walk(src_dir):
            rel_path = os.path.relpath(root, src_dir)
            target_root = os.path.join(dst_dir, rel_path)
            # Directories
            for d in dirs:
                target_dir = os.path.join(target_root, d)
                if not os.path.isdir(target_dir):
                    os.mkdir(target_dir)
                else:
                    sys.stderr.write(f"INFO: Directory already exists:\t{target_dir}\n")
            # Files
            for file in files:
                source_name = os.path.join(root, file)
                target_name = os.path.join(target_root, file)
                if os.path.isfile(target_name):
                    sys.stderr.write(f"INFO: File already exists:\t{target_name}\n")
                    if not overwrite:
                        continue
                shutil.copy(source_name, target_name)

    def run(args: Any) -> None:
        src_dir = os.path.join(os.path.dirname(__file__), "init")
        if not os.path.isdir(src_dir):
            raise SystemExit(f"Resources missing: '{src_dir}' does not exist.\nTry reinstalling the package.")
        cwd = os.getcwd()
        copy_dir(src_dir, cwd, args.overwrite)
        rp_dir = os.path.join(cwd, "resultparsers")
        if not os.path.isdir(rp_dir):
            os.mkdir(rp_dir)
        else:
            sys.stderr.write(f"INFO: Directory already exists:\t{rp_dir}\n")
        if args.resultparser_template:
            rp_tmp = os.path.join(rp_dir, "rp_tmp.py")
            if os.path.isfile(rp_tmp):
                sys.stderr.write(f"INFO: File already exists:\t{rp_tmp}\n")
                if not args.overwrite:
                    return
            shutil.copy(os.path.join(os.path.dirname(__file__), "resultparser", "clasp.py"), rp_tmp)

    parser = subparsers.add_parser(
        "init",
        help="Initialize benchmark environment",
        description=dedent(
            """\
            Initialize the benchmark environment with the necessary directory structure
            and example runscript and templates.
            By default existing files are not overwritten; use --overwrite to change this behavior.
            """
        ),
        formatter_class=formatter,
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Overwrite existing files",
    )
    parser.add_argument(
        "--resultparser-template",
        action="store_true",
        help="Also create a copy of the default 'clasp' resultparser as 'rp_tmp.py'",
    )
    parser.set_defaults(func=run)


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
        type=int,
        default=100,
        help="Maximum number of jobs running at once (default: %(default)d)",
        metavar="<n>",
    )
    parser.add_argument(
        "-w",
        "--wait",
        type=int,
        default=1,
        help="Time to wait between checks in seconds (default: %(default)d)",
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
        help="Check for runlim errors",
        description=dedent(
            """\
            Checks benchmark results in the given folder for runlim errors
            and removes '.finished' files for affected instances.
            Use 'btool gen -e <runscript.xml>' to re-generate new start scripts
            which exclude finished/valid runs.
            """
        ),
        formatter_class=formatter,
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
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"potassco-benchmark-tool {importlib.metadata.version('potassco-benchmark-tool')}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    btool_conv(subparsers)
    btool_eval(subparsers)
    btool_gen(subparsers)
    btool_init(subparsers)
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
