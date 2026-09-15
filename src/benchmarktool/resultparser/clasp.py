"""
Created on Jan 17, 2010

@author: Roland Kaminski
"""

import re
import sys
from typing import TYPE_CHECKING, Any

from . import open_results

if TYPE_CHECKING:
    from benchmarktool.runscript import runscript  # nocoverage

multi = ["rules", "choice_rules", "atoms", "bodies", "count", "sum"]

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
    "rules": (
        "float",
        re.compile(r"^(c )?Rules[ ]*:[ ]*(?P<simplified>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "choice_rules": (
        "float",
        re.compile(
            r"^(c )?[ ]*Choice[ ]*:[ ]*(?P<simplified>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"
        ),
    ),
    "atoms": (
        "float",
        re.compile(r"^(c )?Atoms[ ]*:[ ]*(?P<simplified>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "bodies": (
        "float",
        re.compile(r"^(c )?Bodies[ ]*:[ ]*(?P<simplified>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "count": (
        "float",
        re.compile(
            r"^(c )?[ ]*Count[ ]*:[ ]*(?P<simplified>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"
        ),
    ),
    "sum": (
        "float",
        re.compile(
            r"^(c )?[ ]*Sum[ ]*:[ ]*(?P<simplified>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"
        ),
    ),
    "tight": ("string", re.compile(r"^(c )?Tight[ ]*:[ ]*(?P<val>No|Yes)\+?.*$")),
    "variables": ("float", re.compile(r"^(c )?Variables[ ]*:[ ]*(?P<val>[0-9]+)\+?.*$")),
    "constraints": ("float", re.compile(r"^(c )?Constraints[ ]*:[ ]*(?P<val>[0-9]+)\+?.*$")),
}

# penalized-average-runtime score constant
PAR = 2


# pylint: disable=unused-argument, too-many-branches
def parse(
    path: str, runspec: "runscript.Runspec", instance: "runscript.Benchmark.Instance", run: int
) -> dict[str, tuple[str, Any]]:
    """
    Extracts some clasp statistics.

    Attributes:
        path (str):                    The path to the run directory.
        runspec (Runspec):             The run specification of the benchmark.
        instance (Benchmark.Instance): The benchmark instance.
        run (int):                     The run number.
    """
    timeout = runspec.project.job.timeout
    res: dict[str, tuple[str, Any]] = {"time": ("float", timeout)}
    for file_name in ["runsolver.solver", "runsolver.watcher"]:
        try:
            with open_results(path, file_name) as file:
                for line in file:
                    for val, reg in clasp_re.items():
                        m = reg[1].match(line)
                        if m:
                            if val in multi:
                                if m.group("simplified") is not None:
                                    res[f"{val}_s"] = ("float", float(m.group("simplified")))
                                if m.group("original") is not None:
                                    res[f"{val}_o"] = ("float", float(m.group("original")))
                            else:
                                res[val] = (reg[0], float(m.group("val")) if reg[0] == "float" else m.group("val"))
        except FileNotFoundError:
            sys.stderr.write(
                f"*** WARNING: Result file '{file_name}' or '{file_name}.gz' not found for run {run} "
                f"of instance '{instance.name}' "
                f"for system '{runspec.system.name}-{runspec.system.version}'! ({path})\n"
            )

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
        sys.stderr.write(
            f"*** WARNING: Run {run} of instance '{instance.name}' "
            f"for system '{runspec.system.name}-{runspec.system.version}' "
            f"failed with unrecognized status or error! ({path})\n"
        )
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
    if "tight" in res:
        result["tight"] = ("float", 1.0 if res["tight"][1] == "Yes" else 0.0)
        del res["tight"]
    for key in multi:
        if f"{key}_s" in res:
            result[f"{key}_s"] = res[f"{key}_s"]
            del res[f"{key}_s"]
            if f"{key}_o" in res:
                result[f"{key}_o"] = res[f"{key}_o"]
                del res[f"{key}_o"]
            else:
                result[f"{key}_o"] = result[f"{key}_s"]
    for key, value in res.items():
        result[key] = (value[0], value[1])

    return result
