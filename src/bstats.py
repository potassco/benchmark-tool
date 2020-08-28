#!/bin/python

'''
Created on Jan 8, 2011

@author: Marius Schneider

example call: ./beval runscripts/claspfolio-1.0.x.xml | ./bfeat --normalize minmax --printArith --ylabels --status=0 --libSVM --logLabel

precondition:
    - one setting has a name like in --FeatureLabel defined

ToDo:
    - handles only one run
    - don't overwrite careless files
'''
from benchmarktool.result.parser import Parser
import optparse
import sys
import math
import random

def printStats(results,ff=""):
    '''
        print stats
        results: parsing of xml-file
        ff: other parsed input for features 
    '''
    conf_id = 0
    status_min = ["SAT","UNSAT","UNK"]
    status_max = ["SATISFIABLE","UNSATISFIABLE","UNKNOWN"]
  #  if status != "":
  #      status = int(status)
  #  else:
  #      status = -1

    states = {} 
    
    var_results = ""
    if (ff != ""):
        var_results = ff
    else:
        var_results = results
        
    # first search for features
    dic_name_conf = {}
    for v in var_results.projects.values():
        for r in v.runspecs:
            for cr in r.classresults:
                 for ir in cr.instresults:
                    for irr in ir.runs:
                        try:
                            conf = irr.measures['configuration'][1]
                            try:
                                 dic_name_conf[conf] += 1
                            except KeyError: # if instance hasn't any choosen configuration it will be skipped
                                dic_name_conf[conf] = 1
                        except KeyError:
                            try:
                                if (irr.measures['status'][1] != status_max[2]):
                                    if (dic_name_conf.get("presolved") != None and irr.measures.get('configuration')==None) :
                                        dic_name_conf["presolved"] = dic_name_conf["presolved"] + 1
                                    else:
                                        dic_name_conf["presolved"] = 1
                            except KeyError:
                                pass
    print("Configurations:")
    for k,v in dic_name_conf.items():
        print(str(k)+ " : "+str(v))
                    


if __name__ == '__main__':
    usage  = "usage: %prog [options] [xml-file]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--status", dest="status", action="store", default="", help="print only 0:'SATISFIABLE', 1:'UNSATISFIABLE' or 2:'UNKNOWN instances")
    parser.add_option("--featurefile", dest="ff", action="store", default="", help="feature xml-file")
    
    opts, files = parser.parse_args(sys.argv[1:])
       
    if (opts.status != "") and (opts.status != "0") and (opts.status != "1") and (opts.status != "2"):
        parser.error("Status has three possible values: 0, 1 or 2")
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
    
    p = Parser()
    results = p.parse(inFile)
    
    results2 = ""
    if (opts.ff != ""):
        secondIn = open(opts.ff)
        p2 = Parser()
        results2 = p.parse(secondIn)
        
    printStats(results,results2)