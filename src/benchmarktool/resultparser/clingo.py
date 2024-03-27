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
    #"time"        : ("float",  re.compile(r"^Real time \(s\): (?P<val>[0-9]+(\.[0-9]+)?)$")),
    "time"        : ("float",  re.compile(r"\[runlim\] real:[\t]*(?P<val>[0-9]+(\.[0-9]+)?) seconds")),
    "conflicts"   : ("float",  re.compile(r"^(c )?Conflicts[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "ctime"       : ("float",  re.compile(r"^(c )?Time[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "csolve"      : ("float",  re.compile(r"^(c )?Time[ ]*:[ ]*[0-9]+(\.[0-9]+)?s[ ]*\(Solving:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "domain"      : ("float",  re.compile(r"^(c )?Choices[ ]*:[ ]*[0-9]+[ ]*\(Domain:[ ]*(?P<val>[0-9]+)")),
    "vars"        : ("float",  re.compile(r"^(c )?Variables[ ]*:[ ]*(?P<val>[0-9]+)")),
    "cons"        : ("float",  re.compile(r"^(c )?Constraints[ ]*:[ ]*(?P<val>[0-9]+)")),
    "restarts"    : ("float",  re.compile(r"^(c )?Restarts[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "optimum"     : ("string", re.compile(r"^(c )?Optimization[ ]*:[ ]*(?P<val>(-?[0-9]+)( -?[0-9]+)*)[ ]*$")),
    "status"      : ("string", re.compile(r"^(s )?(?P<val>SATISFIABLE|UNSATISFIABLE|UNKNOWN|OPTIMUM FOUND)[ ]*$")),
    "interrupted" : ("string", re.compile(r"(c )?(?P<val>INTERRUPTED)")),
    "error"       : ("string", re.compile(r"^\*\*\* ERROR: (?P<val>.*)$")),
    #"memerror"    : ("string", re.compile(r"^Maximum VSize (?P<val>exceeded): sending SIGTERM then SIGKILL")),
    "memerror"    : ("string", re.compile(r"^\[runlim\] status:[\t]*(?P<val>out of memory)")),
    "memerror2"   : ("string", re.compile(r"^\*\*\* ERROR: \((?P<val>.*)\): std::bad_alloc")),
    #"mem"         : ("float",  re.compile(r"^Max\. virtual memory \(cumulated for all children\) \(KiB\): (?P<val>[0-9]+)")),
    "mem"         : ("float",  re.compile(r"^\[runlim\] space:[\t]*(?P<val>[0-9]+) MB")),
    "ground0"     : ("float",  re.compile(r"^(c )?First Ground[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "groundN"     : ("float",  re.compile(r"^(c )?Next Ground[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "max_length"  : ("float",  re.compile(r"^(c )?Max\. Length[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "sol_length"  : ("float",  re.compile(r"^(c )?Sol\. Length[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
    "calls"       : ("float",  re.compile(r"^(c )?Calls[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "ngadded"     : ("float",  re.compile(r"Nogoods added[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),

    "has_grounded": ("string",  re.compile(r"^(c )?(?P<val>Solving...)")),

    "time_init"   : ("float",  re.compile(r"Time to init prop[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "time_prop"   : ("float",  re.compile(r"Time for propagation[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "time_check"   : ("float",  re.compile(r"Time to check[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "time_ground"   : ("float",  re.compile(r"Time to ground[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "time_register"   : ("float",  re.compile(r"Time to register[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "time_until_solve"   : ("float",  re.compile(r"Time until solving[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),
    "time_undo"         : ("float", re.compile(r"Time to undo[ ]*:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)")),


    "calls_check"   : ("float",  re.compile(r"Calls to check[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "calls_prop"   : ("float",  re.compile(r"Calls to propagation[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "calls_undo"   : ("float",  re.compile(r"Calls to undo[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),

    "theory_cons"   : ("float",  re.compile("Theory constraints[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*")),
}


status_mapping = {"SATISFIABLE": 1, "UNSATISFIABLE": 0, "UNKNOWN": 2, "OPTIMUM FOUND": 3}


def clingo(root, runspec, instance):
    """
    Extracts some clingo statistics.
    """
    print("parse")
    timeout = runspec.project.job.timeout
    res     = { "time": ("float", timeout) }
    for f in ["runsolver.solver", "runsolver.watcher", "benchmark.txt"]:
        if f == "benchmark.txt":
            if "choices" in res or not os.path.isfile(os.path.join(root, f)):
                break
            res["status"] = ("string", "UNKNOWN")
        for line in codecs.open(os.path.join(root, f), errors='ignore', encoding='utf-8'):
            for val, reg in clingo_re.items():
                m = reg[1].search(line)
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
    if timedout:
        res["time"] = ("float", timeout)
        res["ctime"] = ("float", timeout)
        res["csolve"] = ("float", timeout)
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

    if "status" in res:
        status_val = res["status"][1]
        res["status"] = ("float", status_mapping[status_val])
    else:
       res["status"] = ("float", status_mapping["UNKNOWN"])

    if "ngadded" not in res:
        res["ngadded"] = ("float", 0)

    if "has_grounded" in res:
        res["has_grounded"] = ("float", 1)
    else:
        res["has_grounded"] = ("float", 0)

    if "csolve" in res and "time" in res:
        res["ground"] = ("float", res["time"][1] - res["csolve"][1]) 
    else:
        res["ground"] = ("float", res["time"][1])

    if "time_init" not in res:
        res["time_init"] = ("float", 0)

    if "time_prop" not in res:
        res["time_prop"] = ("float", 0)
    
    if "time" in res:
        res["time_no_prop"] = ("float", res["time"][1] - res["time_prop"][1])

    if "time_no_prop" not in res:
        res["time_no_prop"] = res["time"]
    
    if "time_undo" not in res:
        res["time_undo"] = ("float", 0)

    if "time_check" not in res:
        res["time_check"] = ("float", 0)
    
    if "calls_prop" not in res:
        res["calls_prop"] = ("float", 0)

    if "calls_undo" not in res:
        res["calls_undo"] = ("float", 0)

    if "calls_check" not in res:
        res["calls_check"] = ("float", 0)

    for key, val in res.items(): result.append((key, val[0], val[1]))

    return result
