"""
Created on Jan 17, 2010

@author: Roland Kaminski
"""

import re
import sys
from typing import TYPE_CHECKING, Any

from . import open_results, parse_watcher

if TYPE_CHECKING:
    from benchmarktool.runscript import runscript  # nocoverage

multi = ("rules", "choice_rules", "atoms", "bodies", "count", "sum")
capture_suffix = {"val": "", "final": "_f", "original": "_o"}

clasp_re = {
    "models": ("float", re.compile(r"^(c )?Models[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "choices": ("float", re.compile(r"^(c )?Choices[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "conflicts": ("float", re.compile(r"^(c )?Conflicts[ ]*:[ ]*(?P<val>[0-9]+)\+?.*$")),
    "restarts": ("float", re.compile(r"^(c )?Restarts[ ]*:[ ]*(?P<val>[0-9]+)\+?.*$")),
    "optimum": ("string", re.compile(r"^(c )?Optimization[ ]*:[ ]*(?P<val>(-?[0-9]+)( -?[0-9]+)*)[ ]*$")),
    "status": ("string", re.compile(r"^(s )?(?P<val>SATISFIABLE|UNSATISFIABLE|UNKNOWN|OPTIMUM FOUND)[ ]*$")),
    "interrupted": ("string", re.compile(r"(c )?(?P<val>INTERRUPTED)")),
    "error": ("string", re.compile(r"^\*\*\* clasp ERROR: (?P<val>.*)$")),
    "rules": (
        "float",
        re.compile(r"^(c )?Rules[ ]*:[ ]*(?P<final>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "choice_rules": (
        "float",
        re.compile(r"^(c )?[ ]*Choice[ ]*:[ ]*(?P<final>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "atoms": (
        "float",
        re.compile(r"^(c )?Atoms[ ]*:[ ]*(?P<final>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "bodies": (
        "float",
        re.compile(r"^(c )?Bodies[ ]*:[ ]*(?P<final>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "count": (
        "float",
        re.compile(r"^(c )?[ ]*Count[ ]*:[ ]*(?P<final>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
    ),
    "sum": (
        "float",
        re.compile(r"^(c )?[ ]*Sum[ ]*:[ ]*(?P<final>[0-9]+)\+?[ ]*(\(Original:[ ]*(?P<original>[0-9]+)\+?\))?.*$"),
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
    try:
        with open_results(path, "runsolver.solver") as file:
            for line in file:
                for val, reg in clasp_re.items():
                    m = reg[1].match(line)
                    if m:
                        for group, value in m.groupdict().items():
                            if value is not None:
                                res[f"{val}{capture_suffix[group]}"] = (
                                    reg[0],
                                    float(value) if reg[0] == "float" else value,
                                )
                        break
    except FileNotFoundError:
        file_name = "runsolver.solver"
        sys.stderr.write(
            f"*** WARNING: Result file '{file_name}' or '{file_name}.gz' not found for run {run} "
            f"of instance '{instance.name}' "
            f"for system '{runspec.system.name}-{runspec.system.version}'! ({path})\n"
        )
    try:
        res.update(parse_watcher(path))
    except FileNotFoundError:
        file_name = "runsolver.watcher"
        sys.stderr.write(
            f"*** WARNING: Result file '{file_name}' or '{file_name}.gz' not found for run {run} "
            f"of instance '{instance.name}' "
            f"for system '{runspec.system.name}-{runspec.system.version}'! ({path})\n"
        )

    if "rstatus" in res and res["rstatus"][1] == "out of memory":
        res["error"] = ("string", "std::bad_alloc")
        res["status"] = ("string", "UNKNOWN")
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

    result: dict[str, tuple[str, Any]] = {
        "error": ("float", int(error)),
        "timeout": ("float", int(timedout)),
        "memout": ("float", int(memout)),
    }
    if "optimum" in res and not " " in res["optimum"][1]:
        result["optimum"] = ("float", float(res["optimum"][1]))
    if "tight" in res:
        result["tight"] = ("float", 1.0 if res["tight"][1] == "Yes" else 0.0)
    for measure in multi:
        if f"{measure}_f" in res:
            res.setdefault(f"{measure}_o", res[f"{measure}_f"])
    for key, value in res.items():
        if key not in {"error", "interrupted", "tight", "optimum"}:
            result[key] = value

    return result
