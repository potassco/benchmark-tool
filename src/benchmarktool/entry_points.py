"""
Entry points for different components.
"""

import argparse
import optparse
import os
import subprocess
import sys
import time
from typing import Any

from benchmarktool.result.parser import Parser as ResParser
from benchmarktool.runscript.parser import Parser as RunParser


def start_bconv() -> None:
    """
    Start bconv component.
    """
    usage = "usage: %prog [options] [resultfile]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-o",
        "--output",
        dest="output",
        default="out.ods",
        help="name of generated ods file",
    )
    parser.add_option(
        "-p",
        "--projects",
        dest="projects",
        default="",
        help="projects to display (by default all projects are shown)",
    )
    parser.add_option(
        "-m",
        "--measures",
        dest="measures",
        default="time:t,timeout:to",
        help=(
            "comma separated list of measures of form name[:{t,to,-}] "
            "to include in table (optional argument determines coloring)"
        ),
    )

    opts, files = parser.parse_args(sys.argv[1:])

    if opts.projects != "":
        opts.projects = set(opts.projects.split(","))
    measures = []
    if opts.measures != "":
        for t in opts.measures.split(","):
            x = t.split(":", 1)
            if len(x) == 1:
                measures.append((x[0], None))
            else:
                measures.append(tuple(x))
    p = ResParser()
    if len(files) == 0:
        res = p.parse(sys.stdin)
        res.gen_office(opts.output, opts.projects, measures)
    elif len(files) == 1:
        with open(files[0], encoding="utf-8") as in_file:
            res = p.parse(in_file)
        res.gen_office(opts.output, opts.projects, measures)
    else:
        parser.error("Exactly one file has to be given")


def start_beval() -> None:
    """
    Start beval component.
    """
    usage = "usage: %prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "--par-x",
        type="int",
        dest="parx",
        default=2,
        help="penalized-average-runtime score factor [default: %default]",
    )

    opts, files = parser.parse_args(sys.argv[1:])

    if len(files) == 1:
        file_name = files[0]
        p = RunParser()
        run = p.parse(file_name)
        run.eval_results(sys.stdout, opts.parx)
    else:
        parser.error("Exactly one file has to be given")


def start_bgen() -> None:
    """
    Start bgen component.
    """
    usage = "usage: %prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-e",
        "--exclude",
        action="store_true",
        dest="exclude",
        default=False,
        help="exclude finished runs",
    )

    opts, files = parser.parse_args(sys.argv[1:])

    if len(files) == 1:
        file_name = files[0]
        p = RunParser()
        run = p.parse(file_name)
        run.gen_scripts(opts.exclude)
    else:
        parser.error("Exactly one file has to be given")


def btool_conv(subparsers: Any) -> None:
    """
    Register bconv subcommand.
    """

    def parse_set(s: str) -> set[str]:
        return set(filter(None, (x.strip() for x in s.split(","))))

    def parse_measures(s: str) -> list[tuple[str, str | None]]:
        result = []
        for x in s.split(","):
            parts = x.split(":", 1)
            if not parts[0]:
                raise argparse.ArgumentTypeError(f"Invalid measure: '{x}'")
            result.append((parts[0], parts[1] if len(parts) > 1 else None))
        return result

    def run(args: Any) -> None:
        p = ResParser()
        if args.resultfile:
            with open(args.resultfile, encoding="utf-8") as in_file:
                res = p.parse(in_file)
        else:
            res = p.parse(sys.stdin)
        res.gen_office(args.output, args.projects, args.measures)

    conv_parser = subparsers.add_parser("conv", help="Convert result files to ODS")
    conv_parser.add_argument("resultfile", nargs="?", type=str, help="Result file (default: stdin)")
    conv_parser.add_argument("-o", "--output", default="out.ods", help="Name of generated ods file")
    conv_parser.add_argument(
        "-p",
        "--projects",
        type=parse_set,
        default=set(),
        help="Projects to display (comma separated)",
    )
    conv_parser.add_argument(
        "-m",
        "--measures",
        type=parse_measures,
        default=[("time", "t"), ("timeout", "to")],
        help="Comma separated list of measures of form name[:{t,to,-}]",
    )
    conv_parser.set_defaults(func=run)


def btool_eval(subparsers: Any) -> None:
    """
    Register beval subcommand.
    """

    def run(args: Any) -> None:
        p = RunParser()
        run = p.parse(args.runscript)
        run.eval_results(sys.stdout, args.par_x)

    eval_parser = subparsers.add_parser("eval", help="Evaluate runscript")
    eval_parser.add_argument("runscript", type=str, help="Runscript file")
    eval_parser.add_argument("--par-x", type=int, default=2, help="Penalized-average-runtime score factor")
    eval_parser.set_defaults(func=run)


def btool_gen(subparsers: Any) -> None:
    """
    Register bgen subcommand.
    """

    def run(args: Any) -> None:
        p = RunParser()
        run = p.parse(args.runscript)
        run.gen_scripts(args.exclude)

    gen_parser = subparsers.add_parser("gen", help="Generate scripts from runscript")
    gen_parser.add_argument("runscript", type=str, help="Runscript file")
    gen_parser.add_argument("-e", "--exclude", action="store_true", help="Exclude finished runs")
    gen_parser.set_defaults(func=run)


def btool_run_dist(subparsers: Any) -> None:
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

    parser = subparsers.add_parser("run-dist", help="Run distributed jobs")
    parser.add_argument(
        "folder",
        help="Folder with *.dist files to dispatch",
        type=str,
    )
    parser.add_argument(
        "-u",
        "--user",
        type=str,
        default=os.environ.get("USER", "unknown"),
        help="Username for job querying (default: current user)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        help="Maximum number of jobs running at once",
        type=int,
        default=100,
    )
    parser.add_argument(
        "-w",
        "--wait",
        help="Time to wait between checks in seconds",
        type=int,
        default=1,
    )
    parser.set_defaults(func=run)


def btool_verify(subparsers: Any) -> None:
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

    parser = subparsers.add_parser("verify", help="Check for runlim errors and re-run failed instances")
    parser.add_argument("folder", type=str, help="Folder containing the benchmark results")
    parser.set_defaults(func=run)


def main() -> None:
    """
    Entry point for benchmark tool CLI.
    """
    parser = argparse.ArgumentParser(prog="btool", description="Benchmark Tool CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    btool_conv(subparsers)
    btool_eval(subparsers)
    btool_gen(subparsers)
    btool_run_dist(subparsers)
    btool_verify(subparsers)

    args = parser.parse_args()
    args.func(args)
