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
    parser.add_option("-p", "--projects", dest="projects", default=[], help="restrict to the given projects")
    parser.add_option("-m", "--instance-measures", dest="instMeasures", default=[], help="measures to display on the per-instance spreadsheet")
    parser.add_option("-M", "--class-measures", dest="classMeasures", default=[], help="measures to display on the per-class spreadsheet")
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
    
    if opts.projects != []:      opts.projects      = set(opts.projects.split(","))
    if opts.instMeasures != []:  opts.instMeasures  = opts.instMeasures.split(",")
    if opts.classMeasures != []: opts.classMeasures = opts.classMeasures.split(",")
    
    p = Parser()
    res = p.parse(inFile)
    res.genOffice(sys.stdout, opts.projects, opts.instMeasures, opts.classMeasures)