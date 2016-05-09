'''
Created on Jan 17, 2010

@author: Roland Kaminski
'''

import os
import re
import sys
import codecs
import json

clingo_re = {
    "time"        : ("float", re.compile(r"^Real time \(s\): (?P<val>[0-9]+(\.[0-9]+)?)$")),
    "memerror"    : ("string", re.compile(r"^Maximum VSize (?P<val>exceeded): sending SIGTERM then SIGKILL")),
}

def clingo(root, runspec, instance):
    """
    Extracts some clingo statistics.
    """

    timeout = runspec.project.job.timeout
    res     = { "time": ("float", timeout) }
    # {{{1 parse runsolver data
    for f in ["runsolver.watcher"]:
        for line in codecs.open(os.path.join(root, f), errors='ignore', encoding='utf-8'):
            for val, reg in clingo_re.items():
                m = reg[1].match(line)
                if m: res[val] = (reg[0], float(m.group("val")) if reg[0] == "float" else m.group("val"))

    # {{{1 parse solver stdout
    # the runsolver combines both stderr and stdout
    # (should add an option to manually workaround this bizarre design decision)
    content = codecs.open(os.path.join(root, "runsolver.solver"), errors='ignore', encoding='utf-8').read()
    content = content.replace(",\n]", "\n]", 1)
    stats = json.loads(content)
    accu = { "conflicts": 0, "models": 0, "choices": 0, "restarts": 0, "steps": 0, "time_solve": 0, "time_total": 0 }
    for step in stats:
        accu["conflicts"] += step["solvers"]["conflicts"]
        accu["choices"] += step["solvers"]["choices"]
        accu["restarts"] += step["solvers"]["restarts"]
        accu["steps"] = step["step"] + 1
        accu["time_solve"] += step["time_solve"]
        accu["time_total"] += step["time_total"]
        accu["models"] += step["enumerated"]
    accu["time_ground"] = accu["time_total"] - accu["time_solve"]

    # {{{1 parse solver stdout
    content = open(os.path.join(root, "solver.err")).read()
    finished = content.find("FINISHED") >= 0
    if not finished:
        sys.stderr.write("instance " + root + " did not finish properly\n")

    # {{{1 output result
    memedout = False
    if "memerror" in res:
        memedout = True
        del res["memerror"]

    error = memedout or not finished
    timedout = res["time"][1] >= timeout or memedout or error
    res["timeout"] = ("float", int(timedout))
    res["memout"] = ("float", int(memedout))
    res["error"] = ("float", int(error))
    for key, val in accu.items():
        res[key] = ("float", val)
    return [(key, val[0], val[1]) for key, val in res.items()]
