'''
Created on Jan 17, 2010

@author: Roland Kaminski

modified by: Javier
'''

import os
import re
import sys
import codecs

clingo_re = {
    "models"      : ("float",  re.compile(r"^(c )?Models[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "optimal"      : ("float",  re.compile(r"^(c )?[ ]*Optimal[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "choices"     : ("float",  re.compile(r"^(c )?Choices[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "time"        : ("float",  re.compile(r"^Real time \(s\): (?P<val>[0-9]+(\.[0-9]+)?)$")),
    "conflicts"   : ("float",  re.compile(r"^(c )?Conflicts[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "ctime"       : ("float",  re.compile(r"^(c )?Time[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "csolve"      : ("float",  re.compile(r"^(c )?Time[ ]*:[ ]*[0-9]+(\.[0-9]+)?s[ ]*\(Solving:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "domain"      : ("float",  re.compile(r"^(c )?Choices[ ]*:[ ]*[0-9]+[ ]*\(Domain:[ ]*(?P<val>[0-9]+)")),
    "vars"        : ("float",  re.compile(r"^(c )?Variables[ ]*:[ ]*(?P<val>[0-9]+)")),
    "cons"        : ("float",  re.compile(r"^(c )?Constraints[ ]*:[ ]*(?P<val>[0-9]+)")),
    "restarts"    : ("float",  re.compile(r"^(c )?Restarts[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "optimum"     : ("string", re.compile(r"^(c )?Optimization[ ]*:[ ]*(?P<val>(-?[0-9]+)( -?[0-9]+)*)[ ]*$")),
    "status"      : ("string", re.compile(r"^(s )?(?P<val>SATISFIABLE|UNSATISFIABLE|UNKNOWN|OPTIMUM FOUND)[ ]*$")),
    "interrupted" : ("string", re.compile(r"(c )?(?P<val>INTERRUPTED!)")),
    "error"       : ("string", re.compile(r"^\*\*\* ERROR: (?P<val>.*)$")),
    "memerror"    : ("string", re.compile(r"^Maximum VSize (?P<val>exceeded): sending SIGTERM then SIGKILL")),
    "memerror2"   : ("string", re.compile(r"^\*\*\* ERROR: \((?P<val>.*)\): std::bad_alloc")),
    "mem"         : ("float",  re.compile(r"^Max\. virtual memory \(cumulated for all children\) \(KiB\): (?P<val>[0-9]+)")),
    "ground0"     : ("float",  re.compile(r"^(c )?First Ground[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "groundN"     : ("float",  re.compile(r"^(c )?Next Ground[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "max_length"  : ("float",  re.compile(r"^(c )?Max\. Length[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "sol_length"  : ("float",  re.compile(r"^(c )?Sol\. Length[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
}

def clingo(root, runspec, instance):
    """
    Extracts some clingo statistics.
    """

    timeout = runspec.project.job.timeout
    res     = { "time": ("float", timeout) }
    for f in ["runsolver.solver", "runsolver.watcher", "benchmark.txt"]:
        if f == "benchmark.txt":
            if "choices" in res or not os.path.isfile(os.path.join(root, f)):
                break
            res["status"] = ("string", "UNKNOWN")
        for line in codecs.open(os.path.join(root, f), errors='ignore', encoding='utf-8'):
            for val, reg in clingo_re.items():
                m = reg[1].match(line)
                if m:
                    res[val] = (reg[0], float(m.group("val")) if reg[0] == "float" else m.group("val"))
    if "memerror" in res or "memerror2" in res:
        res["error"]  = ("string", "std::bad_alloc")
        res["status"] = ("string", "UNKNOWN")
        res.pop("memerror", None)
        res.pop("memerror2", None)
    if "status" in res and res["status"][1] == "OPTIMUM FOUND" and not "optimal" in res:
        res["optimal"] = ("float", float("1"))
    result   = []
    error    = not "status" in res or ("error" in res and res["error"][1] != "std::bad_alloc")
    memout   = "error" in res and res["error"][1] == "std::bad_alloc"
    status   = res["status"][1] if "status" in res else None
    if "models" in res and not "optimal" in res:
        res["optimal"] = ("float", float("0"))
    timedout = memout or error or status == "UNKNOWN" or (status == "SATISFIABLE" and "optimum" in res) or res["time"][1] >= timeout or "interrupted" in res;
    if timedout: res["time"] = ("float", timeout)
    if memout:
        sys.stderr.write("*** MEMOUT: Run {0} did a memout!\n".format(root))
    elif error: 
        sys.stderr.write("*** ERROR: Run {0} failed with unrecognized status or error!\n".format(root))
    result.append(("error", "float", int(error)))
    result.append(("timeout", "float", int(timedout)))
    result.append(("memout", "float", int(memout)))

    if "optimum" in res and not " " in res["optimum"][1]:
        result.append(("optimum", "float", float(res["optimum"][1])))
        del res["optimum"]
    if "interrupted" in res: del res["interrupted"]
    if "error" in res: del res["error"]
    for key, val in res.items(): result.append((key, val[0], val[1]))

    return result
