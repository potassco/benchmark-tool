'''
Created on Jan 17, 2010

@author: Roland Kaminski
'''

import os
import re

#TODO: some helper methods could be provided ... 
clasp_models      = re.compile(r"^Models[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_choices     = re.compile(r"^Choices[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_time        = re.compile(r"^Time[ ]*:[ ]*([0-9]+\.[0-9]+)s[ ]*\(")
clasp_conflicts   = re.compile(r"^Conflicts[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_restarts    = re.compile(r"^Restarts[ ]*:[ ]*([0-9]+)\+?[ ]*$")
clasp_status      = re.compile(r"^(SATISFIABLE|UNSATISFIABLE|UNKNOWN)[ ]*$")
clasp_interrupted = re.compile(r"^Interrupted[ ]*:[ ]*(1)[ ]*$")

def clasp(root, runspec):
    result      = []
    interrupted = 0
    status      = None
    time        = runspec.project.job.timeout
    for line in open(os.path.join(root, "runsolver.solver")):
        m = clasp_models.match(line)
        if m: result.append(("models", "float", m.group(1)))
        
        m = clasp_choices.match(line)
        if m: result.append(("choices", "float", m.group(1)))
        
        m = clasp_time.match(line)
        if m: time = m.group(1)
        
        m = clasp_conflicts.match(line)
        if m: result.append(("conflicts", "float", m.group(1)))
        
        m = clasp_restarts.match(line)
        if m: result.append(("restarts", "float", m.group(1)))
        
        m = clasp_status.match(line)
        if m: status =  m.group(1)
        
        m = clasp_interrupted.match(line)
        if m: interrupted = 1
    
    result.append(("time", "float", time))
    result.append(("status", "string", status))
    
    if status != "SATISFIABLE" and status != "UNSATISFIABLE":
        result.append(("timeout", "float", 1))
    else:
        result.append(("timeout", "float", 0))
    result.append(("interrupted", "float", interrupted))
    return result
        