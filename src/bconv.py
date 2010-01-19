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
    parser.add_option("-p", "--projects", dest="projects", default="", help="projects to display")
    parser.add_option("-m", "--measures", dest="measures", default="time,timeout", help="measures to display")
    parser.add_option("-M", "--peaks",    dest="peaks",    default="time+,timeout-", help="peak values to highlight")
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
    
    if opts.projects != "":  opts.projects = set(opts.projects.split(","))
    if opts.measures != "":  opts.measures = opts.measures.split(",")
    
    p = Parser()
    res = p.parse(inFile)
    res.genOffice(sys.stdout, opts.projects, opts.measures)