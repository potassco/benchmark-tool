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
import math

def printFeat(results,labels=False,instname=False,status="",libSVM=True,flab="Features",su=False,maxF=83,norm="",log=False,pA=False):
	'''
		print features of claspre
		results: parsing of xml-file
		labels bool: print run time of each instance (first coloumn)
		instname bool: print name of each instance (last coloumn) 
		status string: print only instances with spezified status
		libSVM: change features to libSVM format (side effect: maxF will be used)
		flab: Label of Feature setting 
		su: print classification problem: SAT/UNSAT
		maxF: exact number of Features which are printed (only in libSVM mode or usage of normalization
		norm: normalization (side effect: maxF will be used)
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
								dic_name_features[cr.benchclass.name+ir.instance.name] = irr.measures['features'][1]
							except KeyError: # if instance hasn't any features measures it will be skipped
								pass

	# normalize features
	if (norm != ""):
		dic_name_features = normalize(dic_name_features, norm, maxF,pA)
	
	if (libSVM == True):
		dic_name_features = libSVMFormat(dic_name_features,maxF)

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
											if (log == True):
												out += str(math.log(float(irr.measures["time"][1])))+" "
											else:
												out += irr.measures["time"][1]+" "
										out += dic_name_features[cr.benchclass.name+ir.instance.name]
										if (instname == True):
											out += " "+ir.instance.name
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
		for k,v in dic_name_features.items():
			try:
				status_k = dic_name_su[k]
				value = 0
				if (status_k == status_max[0]): # SAT
					value = 1
				if (status_k == status_max[1]): #UNSAT
					value = -1
				if (status_k == status_max[2]): #unknown
					continue
				outfile.write(str(value)+" "+v+"\n")
			except KeyError:
				pass
		outfile.close()
				
def normalize(features_dic,mode,maxF,pA):
	dfeatures = divide_features(features_dic,maxF) 
	arr = build_feature_arr(dfeatures)
	arith = arithmetics(arr)
	defeatures = {}
	if (mode == "minmax"):
		defeatures = min_max(dfeatures, arith)
	else: 
		if (mode == "zscore"):
			defeatures = zscore(dfeatures, arith)
	if (pA == True):
		print("min: "+str(arith["min"]))
		print("max: "+str(arith["max"]))
		print("mean: "+str(arith["mean"]))
		print("std: "+str(arith["std"]))
	return ori_format(defeatures)

def ori_format(features):
	''' Input: dictionary: inst_name -> feature_list
		Output: dictionary: inst_name -> feature_string
	'''
	dic = {}
	for k,v in features.items():
		dic[k] = ",".join(v)
	return dic
	
	
def min_max(dfeatures,arith):
	nfeatures = {}
	maxNorm = 1.0
	minNorm = -1.0
	minv = arith["min"]
	maxv = arith["max"]
	for inst,feat in dfeatures.items():
		nfeat = []
		i = 0
		for f in feat:
			n = 0.0
			f = float(f)
			if (minv[i] != maxv[i]):
				n = ((f - minv[i]) * ( maxNorm - minNorm ) / (maxv[i] - minv[i])) + minNorm
			i += 1
			nfeat.append(str(n))
		nfeatures[inst] = nfeat
	return nfeatures

def zscore(dfeatures,arith):
	nfeatures = {}
	mean = arith["min"]
	std = arith["max"]
	for inst,feat in dfeatures.items():
		nfeat = []
		i = 0
		for f in feat:
			if (std[i] != 0):
				n = (float(f) - mean[i]) / std[i]
			else:
				n = 0
			i += 1
			nfeat.append(str(n))
		nfeatures[inst] = nfeat
	return nfeatures
	
def build_feature_arr(features):
	''' Input: dictionary: inst_name -> feature_list
		Output: 2-dim feature matrix
	'''
	featuresV = list(features.values())
	arr_features = []
	for feat in range(0,len(featuresV[1])):  #assumption: all vector have the same size
		arr_features.append([])
	for feat in featuresV:
		i = 0
		for f in feat:
			arr_features[i].append(float(f))
			i = i + 1
	return arr_features

def arithmetics(arr_features):
	''' Input: 2-dim feature matrix'''
	mini = []
	maxi = []
	avi = []
	stdi = []
	i = 0
	for vector in arr_features:
		mini.append( min(vector) )
		maxi.append( max(vector) )
		avi.append( sum(vector) / len(vector))
		stdi.append( standard_deviation(vector,avi[i] ))
		i += 1
	return {"max":maxi,"min":mini,"mean":avi,"std":stdi}
		
def standard_deviation(list, mean):
	std = 0
	for l in list:
		std += math.fabs(l - mean)
	std = std / (len(list) - 1)
	if std != 0:
		std = math.sqrt(std)
	return std

def divide_features(features,maxF):
	''' Input: dictionary: inst_name -> feature_string
		Output: dictionary: inst_name -> feature_list
	'''
	dfeatures = {}
	for inst,feat in features.items():
		df = feat.split(",")
		if (maxF == len(df)):
			dfeatures[inst] = df
	return dfeatures
		
def libSVMFormat (featuresD,maxF):	
	dic = {}
	for inst, features in featuresD.items():
		
		if (len(features) > 0):
			sp_feat = features.split(",")
			svm_form = []
			id = 1
			for feat in sp_feat:
				svm_form.append(str(id)+":"+feat)
				id = id +1
			if (id == maxF+1):
				dic[inst]  = " ".join(svm_form)
	return dic
			
	
if __name__ == '__main__':
	usage  = "usage: %prog [options] [xml-file]"
	parser = optparse.OptionParser(usage=usage)
	parser.add_option("--ylabels", dest="label", action="store_true", default=False, help="first coloumn: print run time")
	parser.add_option("--inames", dest="iname", action="store_true", default=False, help="last coloumn: print instance name")
	parser.add_option("--status", dest="status", action="store", default="", help="print only 0:'SATISFIABLE', 1:'UNSATISFIABLE' or 2:'UNKNOWN instances")
	parser.add_option("--libSVM", dest="libSVM", action="store_true", default=False, help="print features in libSVM format (id:value)")
	parser.add_option("--FeatureLabel", dest="flab", action="store", default="Features", help="name of setting which generates features")
	parser.add_option("--SATUNSAT", dest="su", action="store_true", default=False, help="print features in libSVM format with classification between SAT and UNSAT")
	parser.add_option("--maxFeatures", dest="maxF", action="store", default=86, help="print only datas with <arg> features")
	parser.add_option("--normalize", dest="norm", action="store", default="", help="normalize Features [minmax|zscore]")
	parser.add_option("--logLabel", dest="log", action="store_true", default=False, help="log-shrinking of labels")
	parser.add_option("--printArith", dest="pA", action="store_true", default=False, help="print min, max, mean, std of features")
	
	
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
	printFeat(results,opts.label,opts.iname,opts.status,opts.libSVM,opts.flab,opts.su,opts.maxF,opts.norm,opts.log,opts.pA)