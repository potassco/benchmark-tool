'''
Created on Jan 15, 2010

@author: Roland Kaminski
'''

import os
import datetime

def mkdir_p(path):
    """
    Simulates "mkdir -p" functionality.
    
    Keyword arguments:
    path -- a string holding the path to create    
    """
    if not os.path.exists(path): os.makedirs(path)

def timedelta(strRep):
    timeout = strRep.split(":")
    seconds = int(timeout[-1])
    minutes = hours = 0
    if len(timeout) > 1: minutes = int(timeout[-2]) 
    if len(timeout) > 2: hours   = int(timeout[-3])
    return datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours)