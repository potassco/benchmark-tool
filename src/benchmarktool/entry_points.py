"""
Entry points for different components.
"""

import optparse
import sys

from benchmarktool.result.ipynb_gen import gen_ipynb
from benchmarktool.result.parser import Parser as ResParser
from benchmarktool.runscript.parser import Parser as RunParser


def start_bconv() -> None:
    """
    Start bconv component.
    """
    usage = "usage: %prog [options] [resultfile]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-o", "--output", dest="output", default="out.ods", help="name of generated ods file")
    parser.add_option(
        "-p", "--projects", dest="projects", default="", help="projects to display (by default all projects are shown)"
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
    parser.add_option(
        "-e",
        "--export",
        dest="export",
        action="store_true",
        help="export instance data to parquet file (same name as ods file).",
    )
    parser.add_option(
        "-j",
        "--jupyter-notebook",
        dest="jupyter_notebook",
        default=None,
        help=("name of generated .ipynb file (if none given, no notebook is generated); "
              "can be started using 'jupyter notebook <notebook>'"),
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
    ex_file = None
    if opts.jupyter_notebook is not None:
        opts.export = True
    if len(files) == 0:
        res = p.parse(sys.stdin)
        ex_file = res.gen_office(opts.output, opts.projects, measures, opts.export)
    elif len(files) == 1:
        with open(files[0], encoding="utf8") as in_file:
            res = p.parse(in_file)
        ex_file = res.gen_office(opts.output, opts.projects, measures, opts.export)
    else:
        parser.error("Exactly on file has to be given")
    if ex_file is not None:
        gen_ipynb(ex_file, opts.jupyter_notebook)


def start_beval() -> None:
    """
    Start beval component.
    """
    usage = "usage: %prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)

    _, files = parser.parse_args(sys.argv[1:])

    if len(files) == 1:
        file_name = files[0]
        p = RunParser()
        run = p.parse(file_name)
        run.eval_results(sys.stdout)
    else:
        parser.error("Exactly on file has to be given")


def start_bgen() -> None:
    """
    Start bgen component.
    """
    usage = "usage: %prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-e", "--exclude", action="store_true", dest="exclude", default=False, help="exclude finished runs"
    )

    opts, files = parser.parse_args(sys.argv[1:])

    if len(files) == 1:
        file_name = files[0]
        p = RunParser()
        run = p.parse(file_name)
        run.gen_scripts(opts.exclude)
    else:
        parser.error("Exactly on file has to be given")
