#!/bin/python

'''
converting xml to (simple) csv

Created on March 21, 2011

@author: Marius Schneider
'''

from benchmarktool.result.parser import Parser
import optparse
import sys
import math
import random
#from sets import Set 

def print_csv(input,ev,ke,ign,sat,cl,fDir,filt1,filtAll):
    dic_name_k = {}
    dic_name_sat = {}
    errors = 0
    timeouts = 0
    #confs = []
    #forbiddenSettings = ['Threads4-n1','Threads4Lemma-n1','Portfolio4-n1','Portfolio4Lemma-n1','20m-n1','4Threads-n1']
    forbiddenSettings = []
    forbiddenSystem = ['ppfolio']
    dic_conf_instK = {}
    instances = []
    one_timeout = []
    for v in input.projects.values():
        for r in v.runspecs:
            if (forbiddenSettings.count(r.setting.name) != 0 or forbiddenSystem.count(r.setting.system.name) != 0):
                continue
            #confs.append(r.system.name+"/"+r.setting.name)
            prevSpec = dic_conf_instK.get(r.system.name+"/"+r.setting.name)
            if (prevSpec != None):
                dic_inst_k = prevSpec
            else:
                dic_inst_k = {}
            for cr in r.classresults:
                for ir in cr.instresults:
                    for irr in ir.runs:
                        if(fDir == False):
                            key = cr.benchclass.benchmark.name+"/"+cr.benchclass.name+"/"+ir.instance.name
                        else:
                            key = ir.instance.name
                        instances.append(key)

                        if (irr.measures["error"][1] != "0"):
                            errors += 1
                        if (irr.measures['timeout'][1] != '0'):
                            timeouts += 1
                            one_timeout.append(key)
                        if (irr.measures["error"][1] == "0" and (irr.measures['timeout'][1] == '0' or ign == True)):
                           if (irr.measures.get(ke) != None):
                               dic_inst_k[key]  = irr.measures[ke][1]
                           else:
                               print("WARNING: "+key+" has not the desired information!")
                           if (irr.measures.get("status") != None):
                               dic_name_sat[key] = irr.measures["status"][1]
                        else:
                           dic_inst_k[key] = ev
            dic_conf_instK[r.system.name+"/"+r.setting.name] = dic_inst_k
 
    set_one_to = set(one_timeout)
    #print(dic_name_sat)       
    #sat = 0
    #unsat = 0
    #for k,v in dic_name_sat.items():
    #    if (v == "SATISFIABLE"):
    #        sat += 1
    #    if (v == "UNSATISFIABLE"):
    #        unsat +=1
    #print(len(dic_name_sat))
    #print(len(dic_name_k))
    #print(str(sat)+ " : "+ str(unsat))
    instances = list(set(instances))
    dic_name_id = collect_classes(instances)
    confs = list(dic_conf_instK.keys())
    datas = 0
    print("Instances,"+",".join(confs))       
    for inst in instances:
        if ((filt1 == False or not(inst in set_one_to)) and (filtAll == False or dic_name_sat.get(inst) != None)):
            if(sat == "0" or (dic_name_sat.get(inst) != None and sat==dic_name_sat[inst])):
                line = inst
                if (cl == True):
                    line +=","+str(dic_name_id[inst])
                for c in confs:
                    t = dic_conf_instK[c].get(inst)
                    if (t != None):
                        line += ","+str(t)
                    else:
                        #line += ","+str(ev)
                        line += ",-1"
                print(line)
        else:
            inst = inst.replace("bz2","gz")
            inst = inst.split("/")
            inst = inst[len(inst)-1]
            sys.stderr.write(inst+"\n")
    
             
#    for k,v in dic_name_k.items():
#        if(sat == "0" or (dic_name_sat.get(k) != None and sat==dic_name_sat[k])):
#            if (cl == False):
#                print(k+","+",".join(v))
#            else:
#                print(k+","+str(dic_name_id[k])+","+",".join(v))
#            datas += 1
    #print(datas)

    #print("Timeouts: "+str(timeouts))
    #print("Errors: "+str(errors))
    
def collect_classes (names):
    dic_name_id = {}
    dic_class_id = {}
    ids = 1
    for n in names:
        c = n.split("/")[0]
        if(dic_class_id.get(c) == None):
            dic_class_id[c] = ids
            dic_name_id[n] = ids
            ids += 1
        else:
            dic_name_id[n] = dic_class_id[c]
    return dic_name_id
            

if __name__ == '__main__':
    usage  = "usage: %prog [options] [xml-file]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--key", dest="key", action="store", default="time", help="key to extract")
    parser.add_option("--evalue", dest="ev", action="store", default="-1", help="value in case of error or timeout")
    parser.add_option("--ignore", dest="ign", action="store_true", default=False, help="ignore timeout filter")
    parser.add_option("--sat", dest="sat", action="store", default="0", help="-1: UNSAT 1:SAT")
    parser.add_option("--class", dest="cl", action="store_true", default=False, help="transform instance names to classes (format: class/name)")
    parser.add_option("--filtDir", dest="fDir", action="store_true", default=False, help="filter director name in instance name")
    parser.add_option("--filt1TO", dest="filt1", action="store_true", default=False, help="filter all instances with at least one timeout")
    parser.add_option("--filtAllTO", dest="filtAll", action="store_true", default=False, help="filter all instances with complete timeouts")
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
        
    if (opts.sat=="1"):
        opts.sat = "SATISFIABLE"
    if(opts.sat=="-1"):
        opts.sat = "UNSATISFIABLE"
        
    p = Parser()
    results = p.parse(inFile)
    
    print_csv(results, opts.ev,opts.key,opts.ign,opts.sat,opts.cl,opts.fDir,opts.filt1,opts.filtAll)
    
    

