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

def clasp(root):
    result = []
    interrupted = 0
    for line in open(os.path.join(root, "runsolver.solver")):
        m = clasp_models.match(line)
        if m: result.append(("models", "int", m.group(1)))
        
        m = clasp_choices.match(line)
        if m: result.append(("choices", "int", m.group(1)))
        
        m = clasp_time.match(line)
        if m: result.append(("time", "float", m.group(1)))
        
        m = clasp_conflicts.match(line)
        if m: result.append(("conflicts", "int", m.group(1)))
        
        m = clasp_restarts.match(line)
        if m: result.append(("restarts", "int", m.group(1)))
        
        m = clasp_status.match(line)
        if m: result.append(("status", "string", m.group(1)))
        
        m = clasp_interrupted.match(line)
        if m: interrupted = 1
        
    result.append(("interrupted", "int", interrupted))
    return result
        