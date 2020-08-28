import os
import re
import sys

claspar_models    = re.compile(r"^(c[ ]+)?Models[ ]*:[ ]*(?P<val>[0-9]+)\+?[ ]*$")
claspar_choices   = re.compile(r"^(c[ ]+)?Choices[ ]*:[ ]*(?P<val>[0-9]+)[ ]*$")
claspar_time      = re.compile(r"^Real time \(s\): (?P<val>[0-9]+\.[0-9]+)$")
claspar_conflicts = re.compile(r"^(c[ ]+)?Conflicts[ ]*:[ ]*(?P<val>[0-9]+)[ ]*$")
claspar_restarts  = re.compile(r"^(c[ ]+)?Restarts[ ]*:[ ]*(?P<val>[0-9]+)[ ]*$")
claspar_optimum   = re.compile(r"^(c[ ]+)?Optimization[ ]*: (?P<val>[0-9]+)[ ]*$")

def claspar(root, runspec, instance):
    """
    Extracts some claspar statistics.
    (This function was tested with the latest claspar trunk)
    """
    result      = []
    timeout     = time = runspec.project.job.timeout
    sanityCheck = False
    optimum     = None
    # parse some of claspar's stats
    for line in open(os.path.join(root, "runsolver.solver")):
        m = claspar_models.match(line)
        if m: result.append(("models", "float", m.group("val")))
        
        m = claspar_choices.match(line)
        if m: result.append(("choices", "float", m.group("val")))
        
        m = claspar_conflicts.match(line)
        if m: 
            sanityCheck = True
            result.append(("conflicts", "float", m.group("val")))
        
        m = claspar_restarts.match(line)
        if m: result.append(("restarts", "float", m.group("val")))

        m = claspar_optimum.match(line)
        if m: optimum = m.group("val")
        
    if optimum != None: result.append(("optimum", "float", optimum))
    else: sys.stderr.write("Warning: no optimum in: " + root + "\n")
        
    # parse runsolver output
    for line in open(os.path.join(root, "runsolver.watcher")):
        m = claspar_time.match(line)
        if m: time = float(m.group("val"))
    
    # TODO: remove that!!!
    sanityCheck = True
    # count suspicious stuff as timeout
    if time >= timeout:
        time        = timeout
        sanityCheck = True
        result.append(("timeout", "float", 1))
    else:
        result.append(("timeout", "float", 0))
    result.append(("time", "float", time))

    if not sanityCheck:
        sys.stderr.write("Warning: unexpected result in: " + root)

    return result
