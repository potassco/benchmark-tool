'''
Created on Jan 17, 2010

Edit from clasp.py

@author: Tobias Rabener 

Change:

function in clasp, but not in claspD implemented:

1. "status"      : ("string", re.compile(r"^(s )?(?P<val>SATISFIABLE|UNSATISFIABLE|UNKNOWN|OPTIMUM FOUND)[ ]*$")),

2. remove "not "status" in res" from error


'''

import os
import re
import sys
import codecs

clasp_re = {
    "models"      : ("float", re.compile(r"^(c )?Models[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "choices"     : ("float", re.compile(r"^(c )?Choices[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "time"        : ("float", re.compile(r"^Real time \(s\): (?P<val>[0-9]+(\.[0-9]+)?)$")),
    "conflicts"   : ("float", re.compile(r"^(c )?Conflicts[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "restarts"    : ("float", re.compile(r"^(c )?Restarts[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")),
    "optimum"     : ("string", re.compile(r"^(c )?Optimization[ ]*:[ ]*(?P<val>(-?[0-9]+)( -?[0-9]+)*)[ ]*$")),
    "interrupted" : ("string", re.compile(r"(c )?(?P<val>INTERRUPTED!)")),
    "error"       : ("string", re.compile(r"^\*\*\* clasp ERROR: (?P<val>.*)$")),
    "memerror"    : ("string", re.compile(r"^Maximum VSize (?P<val>exceeded): sending SIGTERM then SIGKILL")),



}

def claspD(root, runspec, instance):
    """
    Extracts some claspD statistics.
    """

    timeout = runspec.project.job.timeout
    res     = { "time": ("float", timeout) }
    for f in ["runsolver.solver", "runsolver.watcher"]:
        for line in codecs.open(os.path.join(root, f), errors='ignore', encoding='utf-8'):
            for val, reg in clasp_re.items():
                m = reg[1].match(line)
                if m: res[val] = (reg[0], float(m.group("val")) if reg[0] == "float" else m.group("val"))

    if "memerror" in res:
        res["error"]  = ("string", "std::bad_alloc")
        res["status"] = ("string", "UNKNOWN")
        del res["memerror"]
    result   = []
    
    error    = ("error" in res and res["error"][1] != "std::bad_alloc")
    memout   = "error" in res and res["error"][1] == "std::bad_alloc"
    status   = res["status"][1] if "status" in res else None
    timedout = memout or error or status == "UNKNOWN" or (status == "SATISFIABLE" and "optimum" in res) or res["time"][1] >= timeout or "interrupted" in res;
    if timedout: res["time"] = ("float", timeout)
    if error: sys.stderr.write("*** ERROR: Run {0} failed with unrecognized status or error!\n".format(root))
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
