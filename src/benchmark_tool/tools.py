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
