'''
Created on Jan 17, 2010

@author: Roland Kaminski
'''

import os
import re
import sys

#TODO: some helper methods could be provided ... 
clasp_models      = re.compile(r"^Models[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_choices     = re.compile(r"^Choices[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_time        = re.compile(r"^Real time \(s\): ([0-9]+\.[0-9]+)$")
clasp_conflicts   = re.compile(r"^Conflicts[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_restarts    = re.compile(r"^Restarts[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_status      = re.compile(r"^(SATISFIABLE|UNSATISFIABLE|UNKNOWN)[ ]*$")
clasp_interrupted = re.compile(r"^Interrupted[ ]*:[ ]*(1)[ ]*$")

def clasp(root, runspec, instance):
    """
    Extracts some clasp statistics.
    (This function was tested with clasp-1.3.2.)   
    """
    result      = []
    interrupted = 0
    status      = None
    timeout     = time = runspec.project.job.timeout
    # parse some of clasp's stats
    for line in open(os.path.join(root, "runsolver.solver")):
        m = clasp_models.match(line)
        if m: result.append(("models", "float", m.group(1)))
        
        m = clasp_choices.match(line)
        if m: result.append(("choices", "float", m.group(1)))
        
        m = clasp_conflicts.match(line)
        if m: result.append(("conflicts", "float", m.group(1)))
        
        m = clasp_restarts.match(line)
        if m: result.append(("restarts", "float", m.group(1)))
        
        m = clasp_status.match(line)
        if m: status =  m.group(1)
        
        m = clasp_interrupted.match(line)
        if m: interrupted = 1
    
    # parse runsolver output
    for line in open(os.path.join(root, "runsolver.watcher")):
        m = clasp_time.match(line)
        if m: time = float(m.group(1))
    
    # count suspicious stuff as timeout
    if status == None:
        result.append(("error", "float", 1))
        print >> sys.stderr, "*** ERROR: Run {0}/{1} failed with unrecognized status!".format(instance.classname, instance.instance)
    else:
        result.append(("error", "float", 0))

    if (status != "SATISFIABLE" and status != "UNSATISFIABLE") or time >= timeout:
        time = timeout
        result.append(("timeout", "float", 1))
    else:
        result.append(("timeout", "float", 0))
    result.append(("status", "string", status))
    result.append(("time", "float", time))
    result.append(("interrupted", "float", interrupted))
    return result

smodels_status  = re.compile(r"^(True|False)")
smodels_choices = re.compile(r"^Number of choice points: ([0-9]+)")
smodels_time    = re.compile(r"^Real time \(s\): ([0-9]+\.[0-9]+)$")

def smodels(root, runspec, instance):
    """
    Extracts some smodels statistics.
    (This function was tested with smodels-2.33.)   
    """
    result  = []
    status  = None
    timeout = time = runspec.project.job.timeout

    # parse smodels output
    for line in open(os.path.join(root, "runsolver.solver")):
        m = smodels_status.match(line)
        if m: status = m.group(1)
        m = smodels_choices.match(line)
        if m: result.append(("choices", "float", float(m.group(1))))

    # parse runsolver output
    for line in open(os.path.join(root, "runsolver.watcher")):
        m = smodels_time.match(line)
        if m: time = float(m.group(1))
    
    if status == None or time >= timeout:
        time = timeout
        result.append(("timeout", "float", 1))
    else:
        result.append(("timeout", "float", 0))

    if status == "True": status = "SATISFIABLE"
    elif status == "False": status = "UNSATISFIABLE"
    else: status = "UNKNOWN"

    result.append(("status", "string", status))
    result.append(("time", "float", time))

    return result

