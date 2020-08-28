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

def print_csv(input,ev,ke,ign,sat,df,scatter):
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
    filtered_num = 0        
    if (sat != "0"):
        filtered_times = []
        for k,v in dic_name_k.items():
            if (sat == "1" or sat == "-1"): # filter SAT or UNSAT
                if(dic_name_sat.get(k) != None and sat==dic_name_sat[k]):
                    filtered_times.append(v)
                else:
                    filtered_num += 1
            if (sat == "2"): #filter instances which aren't solvable at all
                if(dic_name_sat.get(k) != None):
                    filtered_times.append(v)
                else:
                    filtered_num += 1
        print("Filtered Instances : "+str(filtered_num))
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
    if (scatter == False):
        for index,avg in sortedAvgs:
            c = sets[index]
            d = d_c[c]
            set_row.append(c)
            for data in d:
                fp.write(data+"\n")
            fp.write("\n")
            fp.write("\n")
    else:
        for inst,times in dic_name_k.items():
            fp.write(" ".join(times)+"\n")
        set_row = sets
    fp.close()
      
    return df,set_row,d_c,dic_name_k,sets

    
def writeGnuplot(df,set_row,ev):
    colored = True
    
    fp = open("./"+df+".gpl","w")
    #fp.write("set term postscript eps enhanced color 8\n")
    fp.write("set term postscript eps enhanced 28\n")
    fp.write("set output \""+df+".eps\"\n")
    
    fp.write("set title 'SCD-Plot-"+df+"'\n")
    fp.write("set yrange [0:1]\n")
    fp.write("set xrange [1:"+ev+"]\n")
    fp.write("set xlabel 't in sec'\n")
    fp.write("set ylabel 'p(x<=t)'\n")
    fp.write("set ytics 0.1\n")
    #fp.write("set key right bottom\n")
    fp.write("set key below\n")
    #fp.write("set origin 0.4,0.4\n")
    fp.write("set logscale x\n")
    fp.write("set grid\n")
    fp.write("set size ratio 1\n")
    fp.write("set xtics nomirror\n")
    fp.write("set ytics nomirror\n")
    fp.write("set pointsize 2\n")
    

    index = 0
    white = 256 # 0xFF    
    colors = ["FF0000"] # first color red
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
    print("CALL: "+" ".join(cmd))
    p = Popen(cmd)
    p.communicate()
    cmd = ["ps2pdf","-dEPSCrop",epsFile]
    print("CALL: "+" ".join(cmd))
    p = Popen(cmd)
    p.communicate()
    
    
def writeScatter(df,set_row,ev,s1,s2):
    index = 0
    index1 = -1
    index2 = -1
    for s in set_row:
        if (s1 in s):
            index1 = index
        if (s2 in s):
            index2 = index
        index += 1
    if (index1 == -1):
        sys.stderr.write("ERROR: first solver for scatter plot not found!\n")
        sys.stderr.write(str(set_row)+"\n")
        sys.exit(1)
    if (index2 == -1):
        sys.stderr.write("ERROR: second solver for scatter plot not found!\n")
        sys.stderr.write(str(set_row)+"\n")
        sys.exit(1)
    print(str(index1)+ " : "+set_row[index1])
    print(str(index2)+ " : "+set_row[index2])
    
    fp = open("./"+df+".gpl","w")
    #fp.write("set term postscript eps enhanced color 8\n")
    fp.write("set term postscript eps enhanced 28\n")
    fp.write("set output \""+df+".eps\"\n")
    
    fp.write("set title 'Scatter-Plot-"+df+"'\n")
    fp.write("set size ratio 1\n")
    fp.write("set yrange [1:"+ev+"]\n")
    fp.write("set xrange [1:"+ev+"]\n")
    fp.write("set xlabel 't in sec ("+set_row[index1]+")'\n")
    fp.write("set ylabel 't in sec ("+set_row[index2]+")'\n")
    #fp.write("set key right bottom\n")
    #fp.write("set key outside\n")
    #fp.write("set origin 0.4,0.4\n")
    fp.write("set logscale x\n")
    fp.write("set logscale y\n")
    fp.write("set grid\n")
    fp.write("set xtics nomirror\n")
    fp.write("set ytics nomirror\n")
    fp.write("set pointsize 2\n")
    fp.write("plot '"+df+".data' using "+str(index1+1)+":"+str(index2+1)+" ti '', x ti '' \n")
    
def checkDominace(d_c,set_row,s1,s2):
    index1,index2 = findSolver(s1,s2,set_row)
    
    data1 = d_c[set_row[index1]]
    data2 = d_c[set_row[index2]]
    
    j1 = 0
    j2 = 0
    dominant = 1
    while (j1+1 < len(data1) and j2+1 < len(data2)):
        point1 = data1[j1]
        point1 = point1.split(" ")
        y1 = float(point1[0])
        x1 = float(point1[1])
        point2 = data2[j2]
        point2 = point2.split(" ")
        y2 = float(point2[0])
        x2 = float(point2[1])
        
        #print(str(x1)+" : "+str(y1)+" vs. "+str(x2)+" : "+str(y2))
        
        if (y2 > y1):
            if (dominant != 2):
                print(">>>>>>>>> Change Dominance to 2!")
                dominant = 2
                print(str(x1)+" : "+str(y1)+" vs. "+str(x2)+" : "+str(y2))
        else:
            if (dominant != 1):
                print(">>>>>>>>> Change Dominance to 1!")
                dominant = 1
                print(str(x1)+" : "+str(y1)+" vs. "+str(x2)+" : "+str(y2))
        
        point1N = data1[j1+1]
        point1N = point1N.split(" ")
        x1N = float(point1N[1])
        point2N = data2[j2+1]
        point2N = point2N.split(" ")
        x2N = float(point2N[1])
        if (x1N > x2N):
            j2 += 1
        if (x2N > x1N):
            j1 += 1
        if (x2N == x2N):
            j1 += 1
            j2 += 1
        
def checkBetter(dic_name_k,osets,s1,s2,noise,ev,df,dPlot):
    index1,index2 = findSolver(s1,s2,osets)
    
    better = 0
    equal = 0
    worse = 0
    diffs = []
    quots = []
    
    usedFilter = 0
    usedFilterSpd = 0
    
    for inst,times in dic_name_k.items():
      #  print(str(inst) + " : "+str(times[index1]) + " - "+str(times[index2]))
        t1 = float(times[index1])
        t2 = float(times[index2])
        if (t1 != ev or t2 != ev):
            if (noise > 0):
                delta = math.sqrt(noise/2) * math.sqrt((t1+t2)/2)  
                avgI = (t1+t2)/2
                if (abs(delta) > abs(avgI-t1)):
                    #print(str(t1)+" : "+str(t2))
                    t1 = t2
                    usedFilter += 1
            if (t1 < t2):
                better += 1
            if (t1 > t2):
                worse += 1
            if (t1 == t2):
                equal += 1
        if (t1 != ev or t2 != ev):
            diffs.append(float(times[index2])-float(times[index1]))
            quots.append(float(times[index2])/float(times[index1]))
            usedFilterSpd += 1
    print("Filtered Speedup : "+str(usedFilterSpd))
    
    print("better:\t"+str(better))
    print("equal:\t"+str(equal))
    print("worse:\t"+str(worse))
    
    index = 1
    l = len(diffs)
    fp = open(df+"-speedupcdf.data","w")
    sortedQuots = sorted(quots)
    for d in sortedQuots:
        #print(d)
        fp.write(str(index/l)+" "+str(d)+"\n")
        index +=1

    index = 1
    l = len(diffs)
    fp = open(df+"-diffcdf.data","w")
    sortedDiffs = sorted(diffs)
    for d in sortedDiffs:
        #print(d)
        fp.write(str(index/l)+" "+str(d)+"\n")
        index +=1
    
    print("Average speedup: "+str(sum(quots)/len(quots)))
    print("Median speedup: "+str(sortedQuots[int(len(sortedQuots)/2)]))
    print("Geometric Average speedup: "+str(geoAverage(quots)))

    print("Average diffs: "+str(sum(diffs)/len(diffs)))
    print("Median diffs: "+str(sortedDiffs[int(len(sortedDiffs)/2)]))
    #print("Geometric Average diffs: "+str(geoAverage(diffs)))

    if (dPlot == False):
        suffix = "speedupcdf"
        xrange = str(sortedDiffs[len(diffs)-1])
        fp = writeCDFs(suffix,df,"0.1",xrange,"speedup",True)
        callGnuplot(df+"-"+suffix)
        
        suffix = "diffcdf"
        xrange = str(sortedDiffs[len(diffs)-1])
        fp = writeCDFs(suffix,df,"1",xrange,"difference",True)
        callGnuplot(df+"-"+suffix)
    
def writeCDFs(suffix,df,xrangeBeg,xrangeEnd,xlabel,logScale):
    fp = open("./"+df+"-"+suffix+".gpl","w")

    fp.write("set term postscript eps enhanced 18\n")
    fp.write("set output \""+df+"-"+suffix+".eps\"\n")
    
   # fp.write("set title 'CDF-Plot-"+df+"'\n")
    fp.write("set yrange [0:1]\n")
    fp.write("set xrange ["+xrangeBeg+":"+xrangeEnd+"]\n")
    fp.write("set xlabel '"+xlabel+"'\n")
    fp.write("set ylabel 'p(x<=s)'\n")
    fp.write("set ytics 0.1\n")
    #fp.write("set key right bottom\n")
    fp.write("set key below\n")
    fp.write("set size ratio 1\n")
    #fp.write("set origin 0.4,0.4\n")
    if (logScale == True):
        fp.write("set logscale x\n")
    fp.write("set grid\n")
    fp.write("set xtics nomirror\n")
    fp.write("set ytics nomirror\n")
    fp.write("set pointsize 2\n")
    fp.write("plot '"+df+"-"+suffix+".data' using 2:1 title '"+xlabel+" CDF' with steps lw 4\n")
    fp.flush()
    fp.close()
    return fp
    
def geoAverage(list):
    logSum = 0
    for l in list:
        logSum += math.log(l)
    logSum = logSum * (1/len(list))
    return math.exp(logSum) 
    
    
def findSolver(s1,s2,sets):
    index1 = -1
    index2 = -1
    index = 0
    for c in sets:
        if (s1 in c):
            index1 = index
        if (s2 in c):
            index2 = index
        index += 1

    if (index1 == -1):
        sys.stderr.write("ERROR: first solver for scatter plot not found!\n")
        sys.stderr.write(str(sets)+"\n")
        sys.exit(1)
    if (index2 == -1):
        sys.stderr.write("ERROR: second solver for scatter plot not found!\n")
        sys.stderr.write(str(sets)+"\n")
        sys.exit(1)
    print("Solver 1: "+str(index1)+ " : "+sets[index1])
    print("Solver 2: "+str(index2)+ " : "+sets[index2])
    
    return index1,index2
    
if __name__ == '__main__':
    usage  = "usage: %prog [options] [xml-file]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--key", dest="key", action="store", default="time", help="key to extract")
    parser.add_option("--evalue", dest="ev", action="store", default="-1", help="value in case of error or timeout")
    parser.add_option("--ignore", dest="ign", action="store_true", default=False, help="ignore timeout filter")
    parser.add_option("--sat", dest="sat", action="store", default="0", help="-1:UNSAT 1:SAT 2:OracleFilter")
    parser.add_option("--fname", dest="dF", action="store", default="", help="output file to print datas and gnuplot script")
    parser.add_option("--scatter", dest="scatter", action="store_true", default=False, help="generate a scatter plot")
    parser.add_option("--s1", dest="s1", action="store", default="", help="name of first solver for scatter plot")
    parser.add_option("--s2", dest="s2", action="store", default="", help="name of second solver for scatter plot")
    parser.add_option("--checkDom", dest="cDom", action="store_true", default=False, help="check stochastic dominance of s1 against s2")
    parser.add_option("--better", dest="better", action="store_true", default=False, help="check how often s1 is better than s2")
    parser.add_option("--noise", dest="noise", action="store", default="-1", help="set noise filter (>0)")
    parser.add_option("--dontPlot", dest="dPlot", action="store_true", default=False, help="don't plot!")

    opts, files = parser.parse_args(sys.argv[1:])
    
    if(os.path.isfile("./"+opts.dF+".pdf") == True and opts.dPlot == False):
        print("df.pdf exists - EXIT")
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
    
    df,set_row,d_c,dic_name_k,osets = print_csv(results, opts.ev,opts.key,opts.ign,opts.sat,opts.dF,opts.scatter)
    
    if (opts.scatter == True):
        writeScatter(df,set_row,opts.ev,opts.s1,opts.s2)
        if (opts.dPlot == False):
            callGnuplot(opts.dF)
    else:
        writeGnuplot(df,set_row,opts.ev)
        if (opts.dPlot == False):
            callGnuplot(opts.dF)
    
    if (opts.cDom == True):
        checkDominace(d_c,set_row,opts.s1,opts.s2)
        
    if (opts.better == True):
        checkBetter(dic_name_k,osets,opts.s1,opts.s2,float(opts.noise),float(opts.ev),opts.dF,opts.dPlot)
