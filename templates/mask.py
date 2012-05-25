#!/bin/python

'''
Created on Aug 16, 2011

@author: Marius Schneider

convert qstat -f $JOBID to bitmask for taskset
'''

import sys

def binary(n, digits=8):
    rep = bin(n)[2:]
    return ('0' * (digits - len(rep))) + rep

if __name__ == '__main__':

    try:
        input = sys.stdin
        start = False
        ressources = ""
        for line in input:
            if (start == True and line.find('exec_port') == -1):
                ressources += line.replace('\t','')
            if (start == True and line.find('exec_port') != -1):
                break
            if (line.find('exec_host') != -1):
                ressources = line.replace('    exec_host = ','').replace('\n','')
                start = True
            
        ressources = ressources.split("+")
        mask = 0
        for res in ressources:
            res = int(res.split("/")[1])
            if res != 0:
                mask += 2**res
        #print(mask)
        #print(binary(mask,8))
        print(hex(mask))
    except:
        print("0xfe")
        