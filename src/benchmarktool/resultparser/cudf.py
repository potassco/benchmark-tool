import os
import re
import sys

real_time   = re.compile(r"^Real time \(s\): (?P<val>[0-9]+\.[0-9]+)$")
status      = re.compile(r"^[ ]*Optimum[ ]+:[ ]+(?P<val>unknown|yes)$")
optimum     = re.compile(r"^Optimization: (?P<val>([0-9]+[ ]*)*)$")

def cudf(root, runspec, instance):
    """
    Extracts some cudf statistics.
    (This function was tested with the latest cudf trunk)
    """
    result       = []
    timeout      = time = runspec.project.job.timeout # timeout is hardcoded for now
    clasp_status = None
    opt          = None
        
    # parse runsolver output
    for line in open(os.path.join(root, "runsolver.watcher"), "rb"):
        m = real_time.match(line.decode('utf8', 'ignore'))
        if m: time = float(m.group("val"))

    for line in open(os.path.join(root, "runsolver.solver"), "rt"):
        m = status.match(line)
        if m:
            clasp_status = m.group("val")
            result.append(("status", "string", clasp_status))
        m = optimum.match(line)
        if m: opt = m.group("val")
    
    # count suspicious stuff as timeout
    if time >= timeout or clasp_status != "yes":
        time = timeout
        result.append(("timeout", "float", 1))
    else:
        result.append(("timeout", "float", 0))
    result.append(("time", "float", time))
    if opt != None:
        result.append(("optimum", "string", opt.strip()))

    return result

