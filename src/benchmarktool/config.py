"""
Created on Jan 17, 2010

@author: Roland Kaminski
"""

import os
import re
from typing import Any

# pylint: disable=unused-import
from benchmarktool.resultparser.clasp import clasp
from benchmarktool.resultparser.clasp_d import clasp_d
from benchmarktool.resultparser.claspar import claspar
from benchmarktool.resultparser.clingo import clingo
from benchmarktool.resultparser.cudf import cudf
from benchmarktool.runscript import runscript

claspre_features = re.compile(r"^Features[ ]*:[ ]*(([0-9]+\.?[0-9]*)([,](.+\.?.*))*)\+?[ ]*$")
claspre_conf = re.compile(r"^Chosen configuration:[ ]*(.*)\+?[ ]*$")


def claspre(
    root: str, runspec: "runscript.Runspec", instance: "runscript.Benchmark.Instance"
) -> list[tuple[str, str, Any]]:
    """
    Extracts clasp features.

    Attributes:
        root (str):                    The folder with results.
        runspec (Runspec):             The run specification of the benchmark.
        instance (Benchmark.Instance): The benchmark instance.
    """
    result = clasp(root, runspec, instance)
    with open(os.path.join(root, "runsolver.solver"), encoding="utf8") as f:
        for line in f:
            m = claspre_features.match(line)
            if m:
                result.append(("features", "list float", m.group(1)))
            m = claspre_conf.match(line)
            if m:
                result.append(("configuration", "string", m.group(1)))
    return result


smodels_status = re.compile(r"^(True|False)")
smodels_choices = re.compile(r"^Number of choice points: ([0-9]+)")
smodels_time = re.compile(r"^Real time \(s\): ([0-9]+\.[0-9]+)$")


# pylint: disable=unused-argument
def smodels(
    root: str, runspec: "runscript.Runspec", instance: "runscript.Benchmark.Instance"
) -> list[tuple[str, str, Any]]:
    """
    Extracts some smodels statistics.
    (This function was tested with smodels-2.33.)

    Attributes:
        root (str):                    The folder with results.
        runspec (Runspec):             The run specification of the benchmark.
        instance (Benchmark.Instance): The benchmark instance.
    """
    result: list[tuple[str, str, Any]] = []
    status = None
    timeout = runspec.project.job.timeout
    time: int | float = timeout

    # parse smodels output
    with open(os.path.join(root, "runsolver.solver"), encoding="utf8") as f:
        for line in f:
            m = smodels_status.match(line)
            if m:
                status = m.group(1)
            m = smodels_choices.match(line)
            if m:
                result.append(("choices", "float", float(m.group(1))))

    # parse runsolver output
    with open(os.path.join(root, "runsolver.watcher"), encoding="utf8") as f:
        for line in f:
            m = smodels_time.match(line)
            if m:
                time = float(m.group(1))

    if status is None or time >= timeout:
        time = timeout
        result.append(("timeout", "float", 1))
    else:
        result.append(("timeout", "float", 0))

    if status == "True":
        status = "SATISFIABLE"
    elif status == "False":
        status = "UNSATISFIABLE"
    else:
        status = "UNKNOWN"

    result.append(("status", "string", status))
    result.append(("time", "float", time))

    return result
