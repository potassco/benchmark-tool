#!/usr/bin/env python


#!/bin/python

'''
converting xml to scd-plot datas

Created on March 21, 2011

@author: Marius Schneider
'''

from benchmarktool.result.parser import Parser
import optparse
import sys
import math
import random
import os
from subprocess import Popen, PIPE
from operator import itemgetter

def print_csv(input,ev,ke,ign,sat,df):
    dic_name_k = {}
    dic_name_sat = {}
    errors = 0
    timeouts = 0
    sets = []
    for v in input.projects.values():
        for r in v.runspecs:
            sets.append(r.system.name+"/"+r.setting.name)
            for cr in r.classresults:
                for ir in cr.instresults:
                    for irr in ir.runs:
                        key = cr.benchclass.name+"/"+ir.instance.name
                        if not( key in dic_name_k):
                            dic_name_k[key] = []
                        if (irr.measures["error"][1] != "0"):
                            errors += 1
                        if (irr.measures['timeout'][1] != '0'):
                            timeouts += 1
                        if (irr.measures["error"][1] == "0" and (irr.measures['timeout'][1] == '0' or ign == True)):
                           dic_name_k[key].append(irr.measures[ke][1])
                           dic_name_sat[key] =irr.measures["status"][1]
                        else:
                           dic_name_k[key].append(ev)
    
    #print(dic_name_sat)                       
    if (sat != "0"):
        filtered_times = []
        for k,v in dic_name_k.items():
            if(dic_name_sat.get(k) != None and sat==dic_name_sat[k]):
                filtered_times.append(v)
    else: 
        filtered_times = list(dic_name_k.values())


    trans_time = transpose(filtered_times)
    d_c = {}
    
    avgs = {}
    index = 0
    for ts in trans_time:
        ts = strlistTodoublelist(ts)
        avg = sum(ts)/len(ts)
        avgs[index] = avg 
        index += 1
    
    print(avgs)
    sortedAvgs = list(sortedDictValues1(avgs))
    print(sortedAvgs)
    for index,avg in sortedAvgs:
        ts = trans_time[index]
        ts = strlistTodoublelist(ts)
        ts.sort()
        setting = sets[index]
        print(setting)
        d = []
        #index += 1
        counter_t = 0
        row = 0
        s = len(ts)
        old_t = ts[0]
        for t in ts:
            if (old_t == t):    # not very likely
                row += 1
            else:
                counter_t += row
                row = 1
                d.append(str(counter_t/s)+" "+str(old_t))
            old_t = t
        #d.append("1 "+str(old_t))
        d_c[setting] = d

    #print("\n".join(list(d_c.keys()))+"\n\n")  
    set_row = []      
    fp = open("./"+df+".data","w")
    #for c,d in d_c.items():
    for index,avg in sortedAvgs:
        c = sets[index]
        d = d_c[c]
        set_row.append(c)
        for data in d:
            fp.write(data+"\n")
        fp.write("\n")
        fp.write("\n")
    fp.close()


    colored = True
    
    fp = open("./"+df+".gpl","w")
    #fp.write("set term postscript eps enhanced color 8\n")
    fp.write("set term postscript eps enhanced\n")
    fp.write("set output \""+df+".eps\"\n")
    
    fp.write("set title 'SCD-Plot-"+df+"'\n")
    fp.write("set yrange [0:1]\n")
    fp.write("set xrange [1:"+ev+"]\n")
    fp.write("set xlabel 't in sec'\n")
    fp.write("set ylabel 'p(x<=t)'\n")
    #fp.write("set key right bottom\n")
    fp.write("set key outside\n")
    #fp.write("set origin 0.4,0.4\n")
    fp.write("set logscale x\n")
    fp.write("set grid\n")
    fp.write("set xtics nomirror\n")
    fp.write("set ytics nomirror\n")
    fp.write("set pointsize 2\n")
    

    index = 0
    white = 256 # 0xFF    
    colors = []
    splits = int(math.pow(len(set_row),1/3)+1)
    for indexR in range(0,splits):
        R = hex(int(white * ((indexR+2)/(splits+2))))
        for indexG in range(0,splits):
            G = hex(int(white * ((indexG+2)/(splits+2))))
            for indexB in range(0,splits):
                B = hex(int(white * ((indexB+2)/(splits+2))))
                colors.append(str(R)[2:]+str(G)[2:]+str(B)[2:])
    #print(len(colors))
    
    if colored == True:            
        for c in set_row:
            #color = hex(int(white * ((index+2)/(len(set_row)+2))))
            #fp.write("set style line "+str(index+1)+" lc rgb '#"+str("FF")+str(color[2:])+str("FF")+"' lt 1 lw 4\n")
            fp.write("set style line "+str(index+1)+" lc rgb '#"+colors[index]+"' lt 1 lw 4\n")
            index += 1
    fp.write("plot \\\n")
    index = 0
    first = True
    for c in set_row:
        if first == True:
            fp.write("'"+df+".data' index "+str(index)+" using 2:1 title '"+c+"' with steps ls "+str(index+1))
            first = False
        else:
            fp.write(",\\\n'"+df+".data' index "+str(index)+" using 2:1 title '"+c+"' with steps ls "+str(index+1))
        index += 1
    fp.close()
    

def sortedDictValues1(adict):
    return sorted(adict.items(), key=itemgetter(1))
        
def transpose(dlist):
    outer = []
    for i in dlist[0]: #assumption: all list have the same size
        outer.append([])
    for o in dlist:
        index = 0
        for i in o:
            outer[index].append(i)
            index += 1
    return outer

def strlistTodoublelist(list):
    ret = []
    for l in list:
         ret.append(float(l))
    return ret

def doublelistTostrlist(list):
    ret = []
    for l in list:
         ret.append(str(l))
    return ret

def callGnuplot(df):
    gnuplotFile = "./"+df+".gpl"
    epsFile = "./"+df+".eps"
    cmd = ["gnuplot",gnuplotFile]
    p = Popen(cmd)
    p.communicate()
    cmd = ["ps2pdf","-dEPSCrop",epsFile]
    p = Popen(cmd)
    p.communicate()
    
    
if __name__ == '__main__':
    usage  = "usage: %prog [options] [xml-file]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--key", dest="key", action="store", default="time", help="key to extract")
    parser.add_option("--evalue", dest="ev", action="store", default="-1", help="value in case of error or timeout")
    parser.add_option("--ignore", dest="ign", action="store_true", default=False, help="ignore timeout filter")
    parser.add_option("--sat", dest="sat", action="store", default="0", help="-1:UNSAT 1:SAT")
    parser.add_option("--fname", dest="dF", action="store", default="", help="output file to print datas and gnuplot script")
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if(os.path.isfile("./"+opts.dF+".data") == True):
        print("df exists - EXIT")
        sys.exit(-1)
    if(os.path.isfile("./"+opts.dF+".gpl") == True):
        print("gG exists - EXIT")
        sys.exit(-1)
    
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
    
    print_csv(results, opts.ev,opts.key,opts.ign,opts.sat,opts.dF)
    callGnuplot(opts.dF)
    

