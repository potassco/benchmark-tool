#!/bin/python

'''
ranking of solvers based on permutation test (one sided p-value)
following the description of: Ensemble-based Prediction of RNA Secondary Structures (Nima Aghaeepour and Holger H. Hoos)

Created on Dez 2, 2011

@author: Marius Schneider

Input: csv file
'''

import sys
import os 
import math
import csv
import argparse
#import random
#import functools
import itertools
import permutationtest
import scc

def readIn(file,deli):
    Reader = csv.reader(open(file, 'r'), delimiter=deli)
    matrix = []
    first = True
    names = []
    for row in Reader:
        i = 0
        for data in row:
            if(len(matrix) < i+1):
                matrix.append([])
            try:
                matrix[i].append(float(data))
            except:
                if (first == True):
                    names.append(str(data))
                pass
            i += 1
        first = False
    i = 0
    for m in matrix:
        if (len(m) == 0):
            matrix.pop(i)
            i -= 1
        i += 1
    if (len(names) == len(matrix) +1):
        names = names[1:len(names)]
    if (len(names) != len(matrix)):
        names = []
        for i in range(0,len(matrix)):
            names.append(str(i))
    #print(names)
    return [matrix,names]

def getConstVec(size,Const):
    nullVec = []
    for v in range(0,size):
        nullVec.append(Const)
    return nullVec

def compareAll(Matrix,alpha,permutations,noise):
    ''' returns tabel graph: 1 (solver i is better than j), 0 (uncomparable), -1 (i better than j)'''
    l = len(Matrix)
    results = []
    for i in range(0,l):
        results.append(getConstVec(l,0))
    for i in range(0,l):
        for j in range(i+1,l):
            [r,s] = permutationtest.doTest(matrix[i],matrix[j],args.alpha,args.p,i,j,noise)
            results[i][j] = r*s
            results[j][i] = r*s*-1
    #print(results)
    return results
 
def getBest(Matrix,sccs,names):
    ''' extract best solver and delete it in Matrix '''
    index = 0
    found = False
    # get representative for each sccs
    scoreReps = {}
    for sc in sccs:
        s = sc[0]
        score = 0
        for sc2 in sccs:
            s2 = sc2[0]
            score += Matrix[s][s2]
        # rename nodes
        oriname = []
        for s in sc:
            oriname.append(names[s])
        scoreReps[str(oriname)] = score
    return sortDicValue(scoreReps)

def sortDicValue(mydict):
    return sorted(mydict.iteritems(), key=lambda (k,v): (v,k))


def getEdges(Matrix,bidirec):
    l = len(Matrix)
    edges = []
    for i in range(0,l):
            for j in range(i+1,l):
                if (Matrix[i][j] == 1):
                    edges.append((j,i))
                if (Matrix[i][j] == -1):
                    edges.append((i,j))
                if (bidirec == True and Matrix[i][j] == 0):
                    edges.append((i,j))
                    edges.append((j,i))
    #print(edges)
    return edges
def getRanking(results,names):
    #print(results)
    l = len(results)
    edges = getEdges(results,True)
    #print(edges)
    sccs = scc.scc(edges)
    #print(sccs)
    ranking = getBest(results,sccs,names)
    return ranking

def filterTransitionClosure(edges):
    vertices = set(v for v in itertools.chain(*edges))
    survivedEdges = []
    for v in vertices:
        for eX in edges:
            if (eX[0] == v):
                #print(eX)
                filter = False
                for eY in edges:
                    if (eY[0] == v and eX[1] != eY[1]):
                        #print("-"+str(eY))
                        if (edges.count((eY[1],eX[1])) != 0):
                            filter = True
                            break
                if (filter == False):
                    survivedEdges.append(eX)
    return survivedEdges

def checkTransitiveClosure(edges,names):
    print(">>>>>>> CHECK transitive Closure <<<<<<<<<<<<")
    vertices = set(v for v in itertools.chain(*edges))
    for v in vertices:
        for eY in edges:
            if (eY[0] == v):
                for eX in edges:
                    if (eY[1] == eX[0]):
                        if (edges.count((eY[0],eX[1])) == 0):
                            sys.stderr.write("WARNING: Edge is missing between "+str(names[eY[0]])+" and "+str(names[eX[1]]))
                            break
    print(">>>>>>>> END OF CHECK <<<<<<<<<<<<<<<<<<<<<")

def printDot(edges,names):
    print("DOT FORMAT")
    vertices = set(v for v in itertools.chain(*edges))
    sys.stderr.write("digraph {\n")
    for v in vertices:
        sys.stderr.write(str(v)+"[label=\""+str(names[v])+"\", shape=ellipse, color=green]\n")
    for e in edges:
        sys.stderr.write(str(e[0]) + " -> " + str(e[1])+"\n")
    sys.stderr.write("}")

def egdeEvaluation(results,names):
    edges = getEdges(results,False)
    print(edges)
    checkTransitiveClosure(edges,names)
    sEdges = filterTransitionClosure(edges)
    print(sEdges)
    printDot(sEdges,names)
    
if __name__ == '__main__':

    description  = "usage: python -O permutationtest.py --csv=[file]  [options]"
    parser = argparse.ArgumentParser(prog="master.py",usage=description)
    req_group = parser.add_argument_group("Required Options")
    req_group.add_argument('--csv', dest='csv', action='store', default="", required=True,  help='csv file with instance in rows and configurations as columns')    
    req_group.add_argument('--alpha', dest='alpha', action='store', default=0.05, required=True, type=float,  help='confidence level')    
    
    opt_group = parser.add_argument_group("Misc Options")
    opt_group.add_argument('--delimeter', dest='deli', action='store', default=",", help='delimeter')
    opt_group.add_argument('--perm', dest='p', action='store', default=10000, type=int, help='number of permutations')
    opt_group.add_argument('--scc', dest='doScc', action='store_true', default=False, help='do scc evaluation')
    opt_group.add_argument('--noise', dest='noise', action='store', default=None, help='noise filter')
    
    args = parser.parse_args() 
    
    if (os.path.isfile(args.csv) == False):
        sys.stderr.write("ERROR: CSV File was not found!\n")
        sys.exit()
    
    [matrix,names] = readIn(args.csv,args.deli)
    results = compareAll(matrix,args.alpha,args.p,args.noise)
    if (args.doScc):
        ranking = getRanking(results,names)
        print(">>> SCC Evaluation:")
        print(ranking)
    else:
        egdeEvaluation(results,names)