"""
Entry points for different components.
"""

import optparse
import sys

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
        help="comma separated list of measures of form name[:{t,to,-}] to include in table (optional argument determines coloring)",
    )

    opts, files = parser.parse_args(sys.argv[1:])

    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")

    if opts.projects != "":
        opts.projects = set(opts.projects.split(","))
    if opts.measures != "":
        measures = []
        for t in opts.measures.split(","):
            x = t.split(":", 1)
            if len(x) == 1:
                measures.append((x[0], None))
            else:
                measures.append(tuple(x))
        opts.measures = measures
    p = ResParser()
    res = p.parse(inFile)

    res.genOffice(opts.output, opts.projects, opts.measures)


def start_beval() -> None:
    """
    Start beval component.
    """
    usage = "usage: %prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)

    opts, files = parser.parse_args(sys.argv[1:])

    if len(files) == 1:
        fileName = files[0]
    else:
        parser.error("Exactly on file has to be given")

    p = RunParser()
    run = p.parse(fileName)
    run.eval_results(sys.stdout)


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
        fileName = files[0]
    else:
        parser.error("Exactly on file has to be given")
    p = RunParser()
    run = p.parse(fileName)
    run.gen_scripts(opts.exclude)
