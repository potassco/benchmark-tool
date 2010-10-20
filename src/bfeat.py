'''
Created on Jan 13, 2010

@author: Roland Kaminski, Marius Schneider

ToDo:
	- handles only one run
'''

from benchmarktool.result.parser import Parser
import optparse
import sys

def printFeat(results,labels=False,instname=False,status=""):
	'''
	 results: instance of Result
	 return insTime: dictionary of instance.name -> runtime
	 return insSAT: dictionary of instance.name -> status	
	 return insSAT: dictionary of instance.name -> features	
	'''
	for v in results.projects.values():
		for r in v.runspecs:
			print("---")
			print(r.setting.cmdline) # print configuration
			for cr in r.classresults:
				for ir in cr.instresults:
					for irr in ir.runs:
						if (status == "") or (status == irr.measures['status'][1]):
							out = ""
							if (labels == True):
								out += irr.measures["time"][1]+","
							out += irr.measures['features'][1]
							if (instname == True):
								out += ","+ir.instance.name
							print(out)
	
if __name__ == '__main__':
    usage  = "usage: %prog [options] [resultfile]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--ylabels", dest="label", action="store_true", default=False, help="first coloumn: print run time")
    parser.add_option("--inames", dest="iname", action="store_true", default=False, help="last coloumn: print instance name")
    parser.add_option("--status", dest="status", action="store", default="", help="print only 'SATISFIABLE', 'UNSATISFIABLE' or 'UNKNOWN instances")
    
    opts, files = parser.parse_args(sys.argv[1:])
    
    if (opts.status != "") and (opts.status != "SATISFIABLE") and (opts.status != "UNSATISFIABLE") and (opts.status != "UNKNOWN"):
    	parser.error("Status has 3 options: SATISFIABLE, UNSATISFIABLE or UNKNOWN")
    
    if len(files) == 0:
        inFile = sys.stdin
    elif len(files) == 1:
        inFile = open(files[0])
    else:
        parser.error("Exactly on file has to be given")
    
    p = Parser()
    results = p.parse(inFile)
    printFeat(results,opts.label,opts.iname,opts.status)