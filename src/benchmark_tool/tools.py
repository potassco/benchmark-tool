'''
Created on Jan 15, 2010

@author: Roland Kaminski
'''

import os

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