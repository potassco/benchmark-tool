"""
Created on Oct 8, 2026

@author: Tom Schmidt
"""

import json
import sys
from typing import TYPE_CHECKING, Any

from . import open_results, parse_watcher

if TYPE_CHECKING:
    from benchmarktool.runscript import runscript  # nocoverage


def _get(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


# pylint: disable=too-many-branches, too-many-statements
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
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                # error in JSON decoding
                data = {}
    except FileNotFoundError:
        file_name = "runsolver.solver"
        sys.stderr.write(
            f"*** WARNING: Result file '{file_name}' or '{file_name}.gz' not found for run {run} "
            f"of instance '{instance.name}' "
            f"for system '{runspec.system.name}-{runspec.system.version}'! ({path})\n"
        )
        data = {}

    float_stats = {
        "models": ("Models", "Number"),
        "choices": ("Stats", "Core", "Choices"),
        "conflicts": ("Stats", "Core", "Conflicts"),
        "restarts": ("Stats", "Core", "Restarts"),
        "variables": ("Stats", "Problem", "Variables"),
        "constraints": ("Stats", "Problem", "Constraints", "Sum"),
    }
    for key, keys in float_stats.items():
        value = _get(data, *keys)
        if value is not None:
            res[key] = ("float", float(value))

    multi_stats = (
        ("rules", ("Stats", "LP", "Rules")),
        ("choice_rules", ("Stats", "LP", "Choice")),
        ("atoms", ("Stats", "LP", "Atoms")),
        ("bodies", ("Stats", "LP", "Bodies")),
        ("count", ("Stats", "LP", "Bodies", "Count")),
        ("sum", ("Stats", "LP", "Equivalences", "Sum")),
    )
    for measure, keys in multi_stats:
        stats = _get(data, *keys)
        if isinstance(stats, dict):
            values = (("f", "Final"), ("o", "Original"))
            for suffix, key in values:
                value = stats.get(key)
                if value is not None:
                    res[f"{measure}_{suffix}"] = ("float", float(value))
        elif stats is not None:
            res[f"{measure}_f"] = ("float", float(stats))

    if (status := _get(data, "Result")) is not None:
        res["status"] = ("string", status)
    if _get(data, "INTERRUPTED"):
        res["interrupted"] = ("string", "INTERRUPTED")
    if (tight := _get(data, "Stats", "LP", "Tight")) is not None:
        res["tight"] = ("string", "Yes" if str(tight).lower() == "yes" else "No")
    if isinstance((costs := _get(data, "Models", "Costs")), list) and costs:
        res["optimum"] = ("string", " ".join(str(cost) for cost in costs))

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
    if "optimum" in res and " " not in res["optimum"][1]:
        result["optimum"] = ("float", float(res["optimum"][1]))
    if "tight" in res:
        result["tight"] = ("float", 1.0 if res["tight"][1] == "Yes" else 0.0)
    for measure, _ in multi_stats:
        if f"{measure}_f" in res:
            res.setdefault(f"{measure}_o", res[f"{measure}_f"])
    for key, value in res.items():
        if key not in {"error", "interrupted", "tight", "optimum"}:
            result[key] = value

    return result
