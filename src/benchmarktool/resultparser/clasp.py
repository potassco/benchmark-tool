"""
Created on Jan 17, 2010

@author: Roland Kaminski
"""

import codecs
import os
import re
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from benchmarktool.runscript import runscript  # nocoverage

clasp_re = {
    "models": ("float", re.compile(r"^(c )?Models[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "choices": ("float", re.compile(r"^(c )?Choices[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "time": ("float", re.compile(r"^\[runlim\] real:\s*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "conflicts": ("float", re.compile(r"^(c )?Conflicts[ ]*:[ ]*(?P<val>[0-9]+)\+?.*$")),
    "restarts": ("float", re.compile(r"^(c )?Restarts[ ]*:[ ]*(?P<val>[0-9]+)\+?.*$")),
    "optimum": ("string", re.compile(r"^(c )?Optimization[ ]*:[ ]*(?P<val>(-?[0-9]+)( -?[0-9]+)*)[ ]*$")),
    "status": ("string", re.compile(r"^(s )?(?P<val>SATISFIABLE|UNSATISFIABLE|UNKNOWN|OPTIMUM FOUND)[ ]*$")),
    "interrupted": ("string", re.compile(r"(c )?(?P<val>INTERRUPTED)")),
    "error": ("string", re.compile(r"^\*\*\* clasp ERROR: (?P<val>.*)$")),
    "rstatus": ("string", re.compile(r"^\[runlim\] status:\s*(?P<val>.*)$")),
    "mem": ("float", re.compile(r"^\[runlim\] space:\s*(?P<val>[0-9]+(\.[0-9]+)?) MB")),
}

# penalized-average-runtime score constant
PAR = 2


# pylint: disable=unused-argument
def parse(
    root: str, runspec: "runscript.Runspec", instance: "runscript.Benchmark.Instance"
) -> dict[str, tuple[str, Any]]:
    """
    Extracts some clasp statistics.

    Attributes:
        root (str):                    The folder with results.
        runspec (Runspec):             The run specification of the benchmark.
        instance (Benchmark.Instance): The benchmark instance.
    """
    timeout = runspec.project.job.timeout
    res: dict[str, tuple[str, Any]] = {"time": ("float", timeout)}
    for f in ["runsolver.solver", "runsolver.watcher"]:
        if sys.version_info >= (3, 14):  # nocoverage
            open_func = open
        else:  # nocoverage
            open_func = codecs.open
        with open_func(os.path.join(root, f), errors="ignore", encoding="utf-8") as file:
            for line in file:
                for val, reg in clasp_re.items():
                    m = reg[1].match(line)
                    if m:
                        res[val] = (reg[0], float(m.group("val")) if reg[0] == "float" else m.group("val"))

    if "rstatus" in res and res["rstatus"][1] == "out of memory":
        res["error"] = ("string", "std::bad_alloc")
        res["status"] = ("string", "UNKNOWN")
    result: dict[str, tuple[str, Any]] = {}
    error = "status" not in res or ("error" in res and res["error"][1] != "std::bad_alloc")
    memout = "error" in res and res["error"][1] == "std::bad_alloc"
    status = res["status"][1] if "status" in res else None
    timedout = (
        memout
        or error
        or status == "UNKNOWN"
        or (status == "SATISFIABLE" and "optimum" in res)
        or res["time"][1] >= timeout
        or "interrupted" in res
    )
    if timedout:
        res["time"] = ("float", timeout)
    if error:
        sys.stderr.write("*** ERROR: Run {0} failed with unrecognized status or error!\n".format(root))
    result["error"] = ("float", int(error))
    result["timeout"] = ("float", int(timedout))
    result["memout"] = ("float", int(memout))

    if "optimum" in res and not " " in res["optimum"][1]:
        result["optimum"] = ("float", float(res["optimum"][1]))
        del res["optimum"]
    if "interrupted" in res:
        del res["interrupted"]
    if "error" in res:
        del res["error"]
    for key, value in res.items():
        result[key] = (value[0], value[1])

    return result
