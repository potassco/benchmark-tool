'''
Created on Jan 13, 2010

@author: Roland Kaminski
'''

from benchmarktool.runscript.parser import Parser
import optparse
import sys

if __name__ == '__main__':
    usage  = "usage: %prog [options] <runscript>"
    parser = optparse.OptionParser(usage=usage)
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if len(files) == 1:
        fileName = files[0]
    else:
        parser.error("Exactly on file has to be given")
    
    p = Parser()
    run = p.parse(fileName)
    run.genScripts()