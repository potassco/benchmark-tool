'''
Created on Jan 13, 2010

@author: Roland Kaminski, Marius Schneider

example call: ./beval runscripts/claspfolio-1.0.x.xml | ./bfeat --libSVM --ylabels --status=0

precondition:
	- one setting has a name like in --FeatureLabel defined

ToDo:
	- handles only one run
	- don't overwrite careless files
'''

from benchmarktool.result.parser import Parser
import optparse
import sys

def printFeat(results,labels=False,instname=False,status="",libSVM=True,flab="Features",su=False,maxF=83):
	'''
		print features of claspre
		results: parsing of xml-file
		labels bool: print run time of each instance (first coloumn)
		instname bool: print name of each instance (last coloumn) 
		status string: print only instances with spezified status
		libSVM: change features to libSVM format
		flab: Label of Feature setting 
	'''
	conf_id = 0
	status_min = ["SAT","UNSAT","UNK"]
	status_max = ["SATISFIABLE","UNSATISFIABLE","UNKNOWN"]
	if status != "":
		status = int(status)
	else:
		status = -1

	 
	# first search for features
	dic_name_features = {}
	for v in results.projects.values():
		for r in v.runspecs:
			if (r.setting.name.count(flab) != 0):
				for cr in r.classresults:
					for ir in cr.instresults:
						for irr in ir.runs:
							try:
								if (libSVM == True):
									svm_f = libSVMFormat(irr.measures['features'][1],maxF)
									if (svm_f != ""):
										dic_name_features[cr.benchclass.name+ir.instance.name] = svm_f
								else:										
									dic_name_features[cr.benchclass.name+ir.instance.name] = irr.measures['features'][1]
							except KeyError: # if instance hasn't any features measures it will be skipped
								pass


	if (su == False):
		for v in results.projects.values():
			for r in v.runspecs:
				if (r.setting.name.count(flab) == 0):
					print("write file model"+status_min[status]+str(conf_id)+".feat"+" with "+r.setting.cmdline) # print configuration
					outfile = open("model"+status_min[status]+str(conf_id)+".feat","w")
					conf_id = conf_id + 1
					for cr in r.classresults:
						for ir in cr.instresults:
							for irr in ir.runs:
								if (status == -1) or (status_max[status] == irr.measures['status'][1]):
									try:							
										out = ""
										if (labels == True):
											out += irr.measures["time"][1]+","
										out += dic_name_features[cr.benchclass.name+ir.instance.name]
										if (instname == True):
											out += ","+ir.instance.name
										outfile.write(out+"\n")
									except KeyError: # if instance hasn't any features measures it will be skipped
										pass
					outfile.close()
	else:
		dic_name_su = {}
		for v in results.projects.values():
			for r in v.runspecs:
				if (r.setting.name != flab):
					for cr in r.classresults:
						for ir in cr.instresults:
							for irr in ir.runs:
								dic_name_su[cr.benchclass.name+ir.instance.name] = irr.measures['status'][1]
		
		outfile = open("su.feat","w")
		for k,v in dic_name_features:
			try:
				status_k = dic_name_su(k)
				value = -1
				if (status_k == status_max[0]): # SAT
					value = 0
				if (status_k == status_max[1]): #UNSAT
					value = 1
				if (status_k == status_max[2]): #unknown
					continue
				out.write(str(status)+","+v+"\n")
			except KeyError:
				pass
		outfile.close()
				

		
def libSVMFormat (features,maxF):	
	if (len(features) > 0):
		sp_feat = features.split(",")
		svm_form = []
		id = 1
		for feat in sp_feat:
			svm_form.append(str(id)+":"+feat)
			id = id +1
		if (id != maxF+1):
			return ""
		else:
			return ",".join(svm_form)
			
	
if __name__ == '__main__':
	usage  = "usage: %prog [options] [xml-file]"
	parser = optparse.OptionParser(usage=usage)
	parser.add_option("--ylabels", dest="label", action="store_true", default=False, help="first coloumn: print run time")
	parser.add_option("--inames", dest="iname", action="store_true", default=False, help="last coloumn: print instance name")
	parser.add_option("--status", dest="status", action="store", default="", help="print only 0:'SATISFIABLE', 1:'UNSATISFIABLE' or 2:'UNKNOWN instances")
	parser.add_option("--libSVM", dest="libSVM", action="store_true", default=False, help="print features in libSVM format (id:value)")
	parser.add_option("--FeatureLabel", dest="flab", action="store", default="Features", help="name of setting which generates features")
	parser.add_option("--SATUNSAT", dest="su", action="store_true", default=False, help="print features in libSVM format with classification between SAT and UNSAT")
	parser.add_option("--maxFeatures", dest="maxF", action="store", default=83, help="print only datas with <arg> features")
	
	
	opts, files = parser.parse_args(sys.argv[1:])
	
	if (opts.status != "") and (opts.status != "0") and (opts.status != "1") and (opts.status != "2"):
		parser.error("Status has three possible values: 0, 1 or 2")
	
	if len(files) == 0:
		inFile = sys.stdin
	elif len(files) == 1:
		inFile = open(files[0])
	else:
		parser.error("Exactly on file has to be given")
	
	p = Parser()
	results = p.parse(inFile)
	printFeat(results,opts.label,opts.iname,opts.status,opts.libSVM,opts.flab,opts.su,opts.maxF)