#!/bin/python

'''
permutation test (one sided p-value)
following the description of: Ensemble-based Prediction of RNA Secondary Structures (Nima Aghaeepour and Holger H. Hoos)

Created on Dez 1, 2011

@author: Marius Schneider

Input: csv file
'''

import sys
import os 
import math
import csv
import argparse
import random
import functools

def readIn(file,c1,c2,deli):
    Matrix = csv.reader(open(file, 'r'), delimiter=deli)
    col1 = []
    col2 = []
    for row in Matrix:
        try:
            col1.append(float(row[c1-1]))
            col2.append(float(row[c2-1]))
        except:
            pass
    if(len(col1) != len(col2)):
        print("WARNING: data have not the same length!")
    if(len(col1) == 0):
        print("WARNING: no data found!")
    return [col1,col2]
    
def randomSwap(col1,col2):
    n = len(col1)
    sc1 = []
    sc2 = []
    for i in range(0,n):
        if (random.random() > 0.5):
            sc1.append(col2[i])
            sc2.append(col1[i])
        else:
            sc1.append(col1[i])
            sc2.append(col2[i])
    avg1 = avg(sc1)
    avg2 = avg(sc2)
    return avg1-avg2    # betrag?

def getPValue(col1,col2,p,avgS):
    avgs = [avgS]
    for i in range(0,p-1):
        avgs.append(randomSwap(col1,col2))
    print("AVG Start : " +str(avgS))
    print("min AVG : "+str(min(avgs)))
    print("max AVG : "+str(max(avgs)))
    v = percentile(avgs,avgS)
    print("Percentile : "+str(v))
    pValue = v / 100
    return pValue

def percentile(N, value):
    ''' returns percentile of value on list N '''
    N.sort()
    #print(N)
    first = N.index(value)
    count = N.count(value)
    #return float(first+count-1)*100/len(N)
    return float(first)*100/len(N)

def avg(N):
    return (float(sum(N)) / len(N))

def filter(col1,col2,noise):
    for i in range(0,len(col1)):
        delta = math.sqrt(noise/2) * math.sqrt((col1[i]+col2[i])/2)  
        avgI = (col1[i]+col2[i])/2
        #print("Delta : "+str(delta))
        #print("AVG : "+str(avgI))
        #print("cols :"+str(col1[i]) + " : "+str(col2[i]))
        if ((col1[i] < col2[i] and col1[i] >= (avgI-delta)) or (col2[i] <= col1[i] and col2[i] >= (avgI-delta))):
            col1[i] = col2[i]
            #print("Set equal")
    return [col1,col2]

def doTest(col1,col2,alpha,permutations,name1,name2,noise):
    if(noise != None):
        [col1,col2] = filter(col1,col2,float(noise))
    oriAVG = avg(col1) - avg(col2)
    switched = 1    # 1: not switched; -1: switched
    if (oriAVG > 0):
        print("Alternative Hypothesis: Coloumn "+str(name2) + " is better than Coloumn "+str(name1))
        tmp = col1
        col1 = col2
        col2 = tmp
        oriAVG *= -1
        switched = -1
    else:
        print("Alternative Hypothesis: Coloumn "+str(name1) + " is better than Coloumn "+str(name2))
    random.seed(1234)
    pValue = getPValue(col1,col2,permutations,oriAVG)
    if (pValue < alpha):
        print("Reject Null Hypothesis (p-value: "+str(pValue)+")")
        return [1,switched,pValue]
    else:
        print("Don't reject Null Hypothesis (p-value: "+str(pValue)+")")
        return [0,switched,pValue]
            
if __name__ == '__main__':

    description  = "usage: python -O permutationtest.py --csv=[file]  [options]"
    parser = argparse.ArgumentParser(prog="master.py",usage=description)
    req_group = parser.add_argument_group("Required Options")
    req_group.add_argument('--csv', dest='csv', action='store', default="", required=True,  help='csv file with instance in rows and configurations as columns')    
    req_group.add_argument('--alpha', dest='alpha', action='store', default=0.05, required=True, type=float,  help='confidence level')    
    
    opt_group = parser.add_argument_group("Misc Options")
    opt_group.add_argument('--coloumn1', dest='c1', action='store', default=1, type=int, help='coloumn 1')
    opt_group.add_argument('--coloumn2', dest='c2', action='store', default=2, type=int, help='coloumn 2')
    opt_group.add_argument('--delimeter', dest='deli', action='store', default=",", help='delimeter')
    opt_group.add_argument('--perm', dest='p', action='store', default=10000, type=int, help='number of permutations')
    opt_group.add_argument('--noise', dest='noise', action='store', default=None, help='noise to filter')

    args = parser.parse_args() 
    
    if (os.path.isfile(args.csv) == False):
        sys.stderr.write("ERROR: CSV File was not found!\n")
        sys.exit()
        
    [col1, col2] = readIn(args.csv,args.c1,args.c2,args.deli)
    doTest(col1,col2,args.alpha,args.p,args.c1,args.c2,args.noise)