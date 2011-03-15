import os
import re
import sys
from subprocess import Popen, PIPE

real_time   = re.compile(r"^Real time \(s\): (?P<val>[0-9]+\.[0-9]+)$")
enumerated  = re.compile(r"^Enumerated[ ]*:[ ]*(?P<val>[0-9]+)[ ]*$")
conflicts   = re.compile(r"^Conflicts[ ]*:[ ]*(?P<val>[0-9]+)[ ]*$")
fail        = re.compile(r"^FAIL$")

def cudf(root, runspec, instance):
    """
    Extracts some cudf statistics.
    (This function was tested with the latest cudf trunk)
    """
    result       = []
    timeout      = time = runspec.project.job.timeout

    # parse runsolver output
    for line in open(os.path.join(root, "runsolver.watcher"), "rb"):
        m = real_time.match(line.decode('utf8', 'ignore'))
        if m: time = float(m.group("val"))

    for line in open(os.path.join(root, "runsolver.solver"), "rt"):
        m = enumerated.match(line)
        if m: result.append(("enumerated", "float", float(m.group("val"))))
        m = conflicts.match(line)
        if m: result.append(("conflicts", "float", float(m.group("val"))))
    
    # count suspicious stuff as timeout
    if time >= timeout:
        time = timeout
        result.append(("timeout", "float", 1))
    else:
        result.append(("timeout", "float", 0))

    result.append(("time", "float", time))
    
    try:
        m = fail.match(open(root + "/solution.cudf").readline())
        if m == None:
            p1 = Popen(["bzcat", instance.path()], stdout=PIPE)
            p2 = Popen(["programs/mancoosie/cudf-sol-check-32", "-conf", "programs/mancoosie/conf.crit", "-cudf", "/dev/stdin", "-sol", root + "/solution.cudf", "-crit", "user3"], stdin=p1.stdout, stdout=PIPE)
            o  = p2.communicate()[0]
            if p2.returncode == 0:
                result.append(("optima", "string", o.decode("utf-8").replace('\n', '')))
            else:
                result.append(("optima", "string", "error"))
        else:
            result.append(("optima", "string", "unknown"))
    except:
        result.append(("optima", "string", "error"))

    return result

