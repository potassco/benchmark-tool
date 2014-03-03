#!/bin/python

'''
converting xml to (simple) csv

Created on March 21, 2011

@author: Marius Schneider
'''

import optparse
import sys
import os
import math
import random
import json

from benchmarktool.result.parser import Parser
from random import choice
#from sets import Set 

def median(list_,evalue):
    if len(list_) == 1:
        return list_[0]
    l = len(list_)
    sorted_list = sorted(list(map(float,list_replace(list_,"?",evalue))))
    sorted_list = list_replace(sorted_list,evalue,"?")
    if l % 2 == 1:
        return sorted_list[int(( (l+1)/2 )) -1]
    else:
        lower = sorted_list[(l/2) -1]
        upper = sorted_list[l/2]
        return float(lower + upper)/2

def print_arff_features(opts, input):
    
    cutoff = list(input.jobs.values())[0].timeout # assumption: only one job defined
    
    fp = open(opts.feat_json, "r")
    group_dict = json.load(fp)
    fp.close()
    
    # prepare description file
    step_list = ["Static"]
    feature_steps = {"Static" : group_dict["Static"]}
    f_steps_dict_wo_deps = {"Static" : group_dict["Static"]}
    features = group_dict["Static"]
    n_feats = opts.feat_mode
    n_dynamic = 1
    while len(features) < n_feats:
        next_features = list(map(lambda x: x+"-"+str(n_dynamic), group_dict["Dynamic"]))
        feature_steps["Dynamic-"+str(n_dynamic)] = next_features
        f_steps_dict_wo_deps["Dynamic-"+str(n_dynamic)] = next_features
        step_list.append("Dynamic-"+str(n_dynamic))
        for i in range(1,n_dynamic):
            feature_steps["Dynamic-"+str(i)].extend(next_features)
        features.extend(next_features)
        print(len(features))
        n_dynamic += 1
    if len(features) != n_feats:
        sys.stderr.write("Feature list (%d) and given feature number (%d) are not equal.\n" %(len(features), n_feats))
        
    fp = open(os.path.join(opts.dir_,"description.txt"), "w")        
    fp.write("task_id: \n")
    fp.write("performance_measures: runtime\n")
    fp.write("maximize: false\n")
    fp.write("performance_type: runtime\n")
    fp.write("algorithm_cutoff_time: \n")
    fp.write("algorithm_cutoff_memory: ?\n")
    fp.write("features_cutoff_time: \n")
    fp.write("features_cutoff_memory: ?\n")
    fp.write("features_deterministic: %s\n" %(",".join(features)))
    fp.write("features_stochastic: \n")
    fp.write("algorithms_deterministic: \n")
    fp.write("algorithms_stochastic: \n")
    fp.write("number_of_feature_steps: %d\n" %(len(feature_steps)))
    for step,features_s in feature_steps.items():
        fp.write("feature_step %s: %s\n" %(step, ",".join(features_s)))
    fp.close()
    
    # prepare feature file
    fp_feat = open(os.path.join(opts.dir_,"feature_values.arff"), "w")
    fp_feat.write("@RELATION \"features\"\n")
    fp_feat.write("\n")
    fp_feat.write("@ATTRIBUTE instance_id STRING\n")
    fp_feat.write("@ATTRIBUTE repetition NUMERIC\n")
    for f in features:
        fp_feat.write("@ATTRIBUTE %s NUMERIC\n" %(f))
    fp_feat.write("\n")
    
    # prepare feature status file
    fp_status = open(os.path.join(opts.dir_,"feature_runstatus.arff"), "w")
    fp_status.write("@RELATION \"features_status\"\n")
    fp_status.write("\n")
    fp_status.write("@ATTRIBUTE instance_id STRING\n")
    fp_status.write("@ATTRIBUTE repetition NUMERIC\n")
    for f in step_list:
        fp_status.write("@ATTRIBUTE %s {ok,timeout,memout,crash,presolved,other}\n" %(f))
    fp_status.write("\n")
  
    # prepare feature cost file
    fp_cost = open(os.path.join(opts.dir_,"feature_costs.arff"), "w")
    fp_cost.write("@RELATION \"features_cost\"\n")
    fp_cost.write("\n")
    fp_cost.write("@ATTRIBUTE instance_id STRING\n")
    fp_cost.write("@ATTRIBUTE repetition NUMERIC\n")
    for step in step_list:
        fp_cost.write("@ATTRIBUTE %s NUMERIC\n" %(step))
    fp_cost.write("\n")
    
    for v in input.projects.values(): # iterate over all projects
        for r in v.runspecs: # iterate over all solvers
            
            solver = r.system.name+"/"+r.system.version+"/"+r.setting.name # remember solver name 

            if not opts.feature_setting in solver: # only one solver can be responsible for feature extraction, ignore all others
                continue

            for cr in r.classresults: # iterate over problem classes
                for ir in cr.instresults: # iterate over instances in problem class

                    inst_ = cr.benchclass.benchmark.name+"/"+cr.benchclass.name+"/"+ir.instance.name # instance name
                    
                    repetition = 1
                    for irr in ir.runs: # iterate over repetitions
                       
                        status = irr.measures.get("status")
                        if status:
                            status = status.lower()
                        cost = irr.measures.get("featuretimes")
                        if cost:
                            cost = list(map(float,cost[1].split(",")))
                        else:
                            cost = [irr.measures["time"][1]] * (len(feature_steps))
                        
                        if (( irr.measures["error"][1] == "0" or opts.ignore_error) ): # check whether error occured
                            features = irr.measures.get("features", None)
                            if features:
                                features = features[1]
                            else:
                                features = ",".join(["?"]*opts.feat_mode) # missing values
                                cost = ["?"] * (len(feature_steps))
                                status = "other"
                        else:
                           features = ",".join(["?"]*opts.feat_mode) # missing values
                           cost = ["?"] * (len(feature_steps))
                           status = "other"
                        
                        feature_vect = features.split(",")
                        
                        ok_steps = 0
                        used_feats = 0
                        encountered_features = len(feature_vect)
                        for step in step_list:
                            n_feat_in_step = len(f_steps_dict_wo_deps[step])
                            if encountered_features - used_feats >= n_feat_in_step:
                                used_feats += n_feat_in_step
                                ok_steps += 1
                        
                        if status:
                            status = status[1].upper()
                        else:
                            sys.stderr.write("[WARNING]: %s has no status in setting %s! \n"%(inst_ ,solver))
                            status = ["other"]

                        if len(feature_vect) < opts.feat_mode:
                            feature_vect.extend(["?"]*(opts.feat_mode - encountered_features)) # missing values
                            features = ",".join(feature_vect) 
                        
                        if len(feature_vect) > opts.feat_mode:
                            features = ",".join(feature_vect[0:opts.feat_mode])
                            sys.stderr.write("[WARNING]: Truncate features (%d -> %d) of %s\n" %(len(feature_vect),opts.feat_mode,inst_))
                        
                        status_list = [status] * len(feature_steps)
                        if status in ["SATISFIABLE", "UNSATISFIABLE", "ANSWER", "INCONSISTENT", "OPTIMUM FOUND"]:
                            status_list = ["ok"] * ok_steps
                            status_list.extend(["presolved"]*(len(feature_steps) - ok_steps))
                            status = "presolved"
                            
                        if not status in ["ok","timeout","memout","crash","presolved","other"]:
                            status_list = ["other"] * len(feature_steps)
                            features = ",".join(["?"]*opts.feat_mode) # missing values
                            cost = ["?"] * (len(feature_steps))
                            
                        if len(cost) != len(feature_steps):
                            cost.extend(["?"] * (len(feature_steps)-len(cost))) # if e.g., presolved, cost list is not complete

                        fp_feat.write("%s,%d,%s\n" %(inst_,repetition,features))
                        fp_status.write("%s,%d,%s\n"  %(inst_,repetition,",".join(status_list)) )
                        fp_cost.write("%s,%d,%s\n" %(inst_,repetition,",".join(map(str,cost))))
                        repetition += 1
            # feature extraction can be only performed once!
            break
    fp_feat.close()
    fp_status.close()
    fp_cost.close()
    
def print_flat_arff_performance(opts, input):
    
    cutoff = list(input.jobs.values())[0].timeout # assumption: only one job defined
    
    fp = open(os.path.join(opts.dir_,"algorithm_runs.arff"), "w")
    fp.write("@RELATION \"runtime\"\n")
    fp.write("")
    fp.write("@ATTRIBUTE id STRING\n")
    fp.write("@ATTRIBUTE repetition NUMERIC\n")
    fp.write("@ATTRIBUTE algorithm STRING\n")
    fp.write("@ATTRIBUTE runtime NUMERIC\n")
    fp.write("@ATTRIBUTE runstatus {ok, timeout, memout, crash, not_applicable, other}\n")

    fp.write("")

    for v in input.projects.values(): # iterate over all projects
        for r in v.runspecs: # iterate over all solvers
            
            solver = r.system.name+"/"+r.system.version+"/"+r.setting.name # remember solver name 

            for cr in r.classresults: # iterate over problem classes
                for ir in cr.instresults: # iterate over instances in problem class

                    inst_ = cr.benchclass.benchmark.name+"/"+cr.benchclass.name+"/"+ir.instance.name # instance name
                    
                    repetition = 1
                    for irr in ir.runs: # iterate over repetitions
                        
                        if ((irr.measures["error"][1] == "0" or opts.ignore_error) ): # check whether error occured
                            time = irr.measures.get("time", None)
                            if time:
                                time = time[1]
                            else:
                                time = "?"
                        else:
                           time = "?" # missing value

                        status = irr.measures.get("status")
                        if status:
                            status = status[1] 
                        else:
                            #sys.stderr.write("[WARNING]: %s has no status in setting %s! \n"%(inst_ ,solver))
                            status = "timeout"
                        
                        status = status.upper()
                        if  status in ["OPTIMUM FOUND", "SATISFIABLE", "UNSATISFIABLE", "ANSWER", "INCONSISTENT", "OK", "SAT", "UNSAT", "INCUMBENT SOLUTION", "No integer feasible solution exists.".upper()] and time != "?" and float(time) < cutoff:
                                status = "ok"
                        else:
                            status = "timeout"
                            time = "?"
                        
                        fp.write("%s,%d,%s,%s,%s\n" %(inst_,repetition,solver,time,status))
                        repetition += 1
                        
                        if status == "timeout" and irr.measures["timeout"][1] == "0":# and irr.measures["error"][1] == 0:
                            print(status)
                            print(irr.measures["timeout"][1])
                            print(irr.measures.get("status"))
                            
    fp.close()
    

def list_replace(list_,element,replacement):
    return list(map(lambda x: replacement if x == element else x, list_))

def print_status_arff(instances, dic_name_sat):
    print("@RELATION \"status (SAT(1)/UNSAT(-1)\"")
    print("")
    print("@ATTRIBUTE id string")
    print("@ATTRIBUTE status {-1,1}")
    print("")
    print("@DATA")
    print_status_csv(instances, dic_name_sat)

def print_status_csv(instances, dic_name_sat):
    mapping = {"SATISFIABLE" : "1", "SAT": "1", "UNSAT": "-1", "UNSATISFIABLE" : "-1"}
    for inst in sorted(instances):
        status = dic_name_sat.get(inst)
        if status:
            print("%s,%s" %(inst, mapping[status]))
        else:
            print("%s,?" %(inst))

def filter_instances(dic_name_sat, sat_filter):
    instances = []
    for inst,status in sorted(dic_name_sat.keys()):
        status = dic_name_sat[inst]
        if sat_filter == 1 and status == "SATISFIABLE":
            instances.append(inst)
        if sat_filter == -1 and status == "UNSATISFIABLE":
            instances.append(inst)
    return instances

if __name__ == '__main__':
    usage  = "usage: %prog [options] [xml-file]"
    parser = optparse.OptionParser(usage=usage)
    
    parser.add_option("--dir", dest="dir_", action="store", default=None, help="directory to generate output files")
    parser.add_option("--feature-mode", dest="feat_mode", action="store", default=-1, type=int, help="feature output mode - arg: number of features")
    parser.add_option("--feature-json", dest="feat_json", action="store", type=None, help="json file with feature step naming list")
   # parser.add_option("--feature-cutoff", dest="feat_cutoff", action="store", default=-1, type=int, help="feature computation runtime cutoff")
    parser.add_option("--time-mode", dest="time_mode", action="store", default=-1, type=int, help="time output mode - arg: cutoff")
    #parser.add_option("--conf-mode", dest="conf_mode", action="store_true", default=False, help="configuration output mode")
    #parser.add_option("--status-mode", dest="status_mode", action="store_true", default=False, help="print only sat(1) or unsat(-1) status")
    
    #parser.add_option("--key", dest="key", action="store", default="time", help="key to extract")
    #parser.add_option("--evalue", dest="error_value", action="store", default="-1", help="value in case of error or timeout")
    parser.add_option("--ignoreE", dest="ignore_error", action="store_true", default=False, help="ignore error filter")
    #parser.add_option("--sat", dest="sat_filter", action="store", default=0, type=int, help="only -1: UNSAT or 1:SAT")
   # parser.add_option("--class", dest="cl", action="store_true", default=False, help="transform instance names to classes (format: class/name)")
    #parser.add_option("--filtDir", dest="filtered_dir", action="store_true", default=False, help="filter director name in instance name")
    parser.add_option("--feature-setting", dest="feature_setting", action="store", default="features", help="setting name for feature extraction")
    #parser.add_option("--outputmode", dest="outmode", action="store", default="arff", choices=["csv","arff"], help="output in csv or arff mode")
    
    parser.add_option("--truncate", dest="trunc", action="store_true", default=False, help="truncate feature vector if it is too long")
    #parser.add_option("--median", dest="median", action="store_true", default=False, help="severals runs will be aggregated by median (number necessary)")
    #parser.add_option("--filter", dest="filter", action="append", default=[], help="use only the list of given systems")
    
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if opts.dir_ is None:
        sys.stderr.write("[ERROR]: --dir <path> is a required option.")
        sys.exit(1)
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
    
    p = Parser()
    results = p.parse(inFile)
    
    if not os.path.isdir(opts.dir_):
        print("mkdir %s" %(opts.dir_))
        os.makedirs(opts.dir_)
    
    #if opts.conf_mode:
    #    collect_configurations(results)
    #    sys.exit(0)
    
    if opts.feat_mode > -1:
        print_arff_features(opts, results)
        sys.exit(0)
        
    if opts.time_mode > -1:
        print_flat_arff_performance(opts, results)
        sys.exit(0)
    
    

