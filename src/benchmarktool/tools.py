'''
Created on Jan 15, 2010

@author: Roland Kaminski
'''

import os
import random

def mkdir_p(path):
    """
    Simulates "mkdir -p" functionality.
    
    Keyword arguments:
    path -- a string holding the path to create    
    """
    if not os.path.exists(path): os.makedirs(path)

def xmlTime(strRep):
    timeout = strRep.split(":")
    seconds = int(timeout[-1])
    minutes = hours = 0
    if len(timeout) > 1: minutes = int(timeout[-2]) 
    if len(timeout) > 2: hours   = int(timeout[-3])
    return seconds + minutes * 60 + hours * 60 * 60

def medianSorted(sequence):
    if len(sequence) == 0:
        return 0
    middle = len(sequence) / 2
    value  = sequence[middle]
    if 2 * middle == len(sequence):
        value = (value + sequence[middle + 1]) / 2.0
    return value

def median(sequence):
    def partition(sequence, left, right):
        pivotIndex = random.randint(left, right)
        pivotValue = sequence[pivotIndex]
        sequence[pivotIndex], sequence[right] = sequence[right], sequence[pivotIndex]
        storeIndex = left
        for i in range(left, right):
            if sequence[i] < pivotValue:
                sequence[storeIndex], sequence[i] = sequence[i], sequence[storeIndex]
                storeIndex = storeIndex + 1
        sequence[right], sequence[storeIndex] = sequence[storeIndex], sequence[right]
        return storeIndex
    
    def select(sequence, left, right, k):
        pivotIndex = partition(sequence, left, right)
        if k == pivotIndex:
            return sequence[k]
        elif k < pivotIndex:
            return select(sequence, left, pivotIndex-1, k)
        else:
            return select(sequence, pivotIndex+1, right, k)
        
    if len(sequence) == 0:
        return 0
    middle = len(sequence) / 2
    select(sequence, 0, len(sequence) - 1, middle)
    value = sequence[middle]
    if 2 * middle == len(sequence):
        minimum = sequence[middle + 1]
        for x in sequence[middle + 2:]:
            if x < minimum:
                minimum = x
        value = (value + minimum) / 2.0
    return value

