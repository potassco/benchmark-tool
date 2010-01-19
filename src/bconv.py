'''
Created on Jan 13, 2010

@author: Roland Kaminski
'''

from benchmarktool.result.parser import Parser
import optparse
import sys

if __name__ == '__main__':
    usage  = "usage: %prog [options] [resultfile]"
    parser = optparse.OptionParser(usage=usage)
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
    
    p = Parser()
    res = p.parse(inFile)
    #res.genScripts()
