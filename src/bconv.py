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
    parser.add_option("-m", "--measures", dest="measures", default="time:t,timeout:to", help="measures to display")
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
    
    if opts.projects != "":  opts.projects = set(opts.projects.split(","))
    if opts.measures != "":  
        measures = []
        for t in opts.measures.split(","):
            x = t.split(":", 1)
            if len(x) == 1:
                measures.append((x[0],None))
            else:
                measures.append(tuple(x))
        opts.measures = measures
    p = Parser()
    res = p.parse(inFile)
    res.genOffice(sys.stdout.buffer, opts.projects, opts.measures)
