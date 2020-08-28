#!/bin/python

'''
Created on Jan 13, 2010

@author: Roland Kaminski, Marius Schneider

example call: ./beval runscripts/claspfolio-1.0.x.xml | ./bfeat --normalize minmax --printArith --ylabels --status=0 --libSVM --logLabel

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
import random

def printFeat(results,labels=False,instname=False,status="",libSVM=True,flab="Features",su=False,maxF=83,norm="",log=True,pA=False,hyper=False,ff="",wpf=False,to=600):
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
		log: log-transformation of labels
		pA: print min, max, mean, std
		hyper: latin hyper cube design
		ff: other parsed input for features 
	'''
	conf_id = 0
	status_min = ["SAT","UNSAT","UNK"]
	status_max = ["SATISFIABLE","UNSATISFIABLE","UNKNOWN"]
	if status != "":
		status = int(status)
	else:
		status = -1

	states = {} 
	
	alpha = to / 2
	beta = alpha / 6
	
	var_results = ""
	if (ff != ""):
		var_results = ff
	else:
		var_results = results
	# first search for features
	dic_name_features = {}
	for v in var_results.projects.values():
		for r in v.runspecs:
			if (r.setting.name.count(flab) != 0):
				for cr in r.classresults:
					for ir in cr.instresults:
						for irr in ir.runs:
							try:
								dic_name_features[cr.benchclass.name+"/"+ir.instance.name] = irr.measures['features'][1]
							except KeyError: # if instance hasn't any features measures it will be skipped
								pass
							
							if (irr.measures.get('status') != None):
								try:
									states[irr.measures['status']] = states[irr.measures['status']] + 1
								except KeyError: # if instance hasn't any features measures it will be skipped
									states[irr.measures['status']] = 1
	print("States : "+str(states))
	#print(dic_name_features)

	# normalize features
	portfolio=""
	[dic_name_features,arith] = normalize(dic_name_features, norm, maxF,pA)
	portfolio += "@means:"+(",".join(convertListSD(arith['mean'])))+"\n"
	portfolio += "@stds:"+(",".join(convertListSD(arith['std'])))+"\n"
		
	if (hyper == True):
		latin_hyper(dic_name_features,maxF)
		return
	
	if (libSVM == True):
		dic_name_features = libSVMFormat(dic_name_features,maxF)
		
	if (labels == False):
		for k,v in dic_name_features.items():
                      if (instname == True):
                           print(k+","+v)
                      else:
                           print(features)
		return

	dic_name_su = get_su(results,flab)
	
	if (su == False):
		for v in results.projects.values():
			for r in v.runspecs:
				if (r.setting.name.count(flab) == 0):
					filtered_set = r.setting.cmdline.replace("--stats","")
					filtered_set = r.setting.cmdline.replace("--q","")
					filtered_setting = r.setting.name.replace("-n1","").replace("-","")
					portfolio+="["+filtered_setting+"]: "+filtered_set+"\n"
					print("write file model"+status_min[status]+str(filtered_setting)+".feat"+" with "+r.setting.cmdline+" [" +filtered_setting+ "]") # print configuration
					outfile = open("model"+status_min[status]+str(filtered_setting)+".feat","w")
					for cr in r.classresults:
						for ir in cr.instresults:
							for irr in ir.runs:
								if (dic_name_su.get(cr.benchclass.name+"/"+ir.instance.name) != None):
									if (status == -1) or (status_max[status] == dic_name_su[cr.benchclass.name+"/"+ir.instance.name]):
										try:							
											#print(dic_name_su[cr.benchclass.name+"/"+ir.instance.name] +" : "+irr.measures["status"][1])
											out = ""
											if (labels == True):
												time = float(irr.measures["time"][1])
												#print("#"+status_max[2]+"#"+irr.measures['status'][1])
												if (irr.measures.get('error')[1] != "0") or (status_max[2] == irr.measures['status'][1]):
													time  = time * 10
													#print(str(math.log(time+1)))
												if (log == True):
													#out += str(math.log(time+1))+" "
												   y = 1 / (1 + math.exp(-1*(time-alpha)/beta))
												   #y = -y + 1
												   out += str(y)+" "
												else:
													out += str(time)+" "
											out += dic_name_features[cr.benchclass.name+"/"+ir.instance.name]
											if (instname == True):
												out += " "+ir.instance.name
											outfile.write(out+"\n")
										except KeyError: # if instance hasn't any features measures it will be skipped
											pass
					outfile.close()
		if (wpf == True):			
			print("write portfolio file: portfolio.txt")
			outfile = open("portfolio.txt","w")
			outfile.write(portfolio)
			outfile.close()
	else:
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
		
def get_su(results,flab):
	''' collect status (SAT|UNSAT) of all instances) '''
	dic_name_su = {}
	for v in results.projects.values():
		for r in v.runspecs:
			if (r.setting.name != flab):
				for cr in r.classresults:
					for ir in cr.instresults:
						for irr in ir.runs:
							if (irr.measures.get('status') != None):
								dic_name_su[cr.benchclass.name+"/"+ir.instance.name] = irr.measures['status'][1]
	return 	dic_name_su

def convertListSD(list):
	ret = []
	for l in list:
		ret.append(str(l))
	return ret
				
def latin_hyper (features,maxF):
	''' cut feature space in #cut section for each feature
		for each section in the feature space n samples will be generated
		'''
	local = cut(features, maxF)
	n = 1
	#print(len(local))
	#print(len(features))
	for i in range(0,n):
		for l in local:
			keys = list(l.keys())
			s = len(keys)
			#print(s)
			k = random.randint(0,s-1)
			print(keys[k])
		
def cut(features,maxF):
	cuts = [-1.0,-0.5,0.0,0.5,1.01] # assumption minmax normalization on [-1.0,1.0]
	local = [features]
	for index in range(0,maxF):
		newlocal = []
		for loc in local:
			for cut_index in range(0,len(cuts)-1):
				newloc = {}
				for inst,feat in loc.items():
					current = float(feat.split(",")[index])
					if((cuts[cut_index] <= current) and (current < cuts[cut_index+1])):
						newloc[inst] = feat
				if (len(newloc) != 0):
					newlocal.append(newloc)
		local = newlocal
	return local
				
def normalize(features_dic,mode,maxF,pA):
	dfeatures = divide_features(features_dic,maxF) 
	arr = build_feature_arr(dfeatures)
	arith = arithmetics(arr)
	defeatures = dfeatures
	if (mode == "minmax"):
		defeatures = min_max(dfeatures, arith)
	if (mode == "zscore"):
		defeatures = zscore(dfeatures, arith)
	if (mode == "log"):
		defeatures = nlog(dfeatures, arith)
	if (pA == True):
		print("min: "+str(arith["min"]))
		print("max: "+str(arith["max"]))
		print("mean: "+str(arith["mean"]))
		print("std: "+str(arith["std"]))
	return [ori_format(defeatures),arith]

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
	mean = arith["mean"]
	std = arith["std"]
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

def nlog(dfeatures,arith):
	nfeatures = {}
	for inst,feat in dfeatures.items():
		nfeat = []
		for f in feat:
			if (float(f) > 0):
				n = math.log(1+math.log(1+float(f))) 
			else:
				n = 0
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
		std += math.fabs(l - mean) * math.fabs(l - mean)
	std = std / (len(list) - 1)
	if std != 0:
		std = math.sqrt(std)
	return std

def divide_features(features,maxF):
	''' Input: dictionary: inst_name -> feature_string
		Output: dictionary: inst_name -> feature_list
	'''
	co = {}
	dfeatures = {}
	for inst,feat in features.items():
		df = feat.split(",")
		
		###
		l = len(df)
		try:
			co[l] = co[l] +1 
		except KeyError:
			co[l] = 1
		###
		if (maxF == len(df)):
			dfeatures[inst] = df
	print(co)
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
	parser.add_option("--FeatureLabel", dest="flab", action="store", default="Features", help="name of setting which were generating features")
	parser.add_option("--SATUNSAT", dest="su", action="store_true", default=False, help="print features in libSVM format with classification between SAT and UNSAT")
	parser.add_option("--maxFeatures", dest="maxF", action="store", default=86, help="print only datas with <arg> features")
	parser.add_option("--normalize", dest="norm", action="store", default="", help="normalize Features [minmax|zscore|log]")
	parser.add_option("--logLabel", dest="log", action="store_true", default=False, help="sigmoid function of labels")
	parser.add_option("--printArith", dest="pA", action="store_true", default=False, help="print min, max, mean, std of features")
	parser.add_option("--latinHyperCube", dest="hyper", action="store_true", default=False, help="select instances based on latin hyper cube")
	parser.add_option("--featurefile", dest="ff", action="store", default="", help="feature xml-file")
	parser.add_option("--writepfile", dest="wpf", action="store_true", default=False, help="write portfolio file for clasp")
	parser.add_option("--to", dest="to", action="store", type="int", default=600, help="timeout of clasp")
	
	opts, files = parser.parse_args(sys.argv[1:])
	
	if(opts.hyper == True):
		opts.norm = "minmax"
	
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
	
	results2 = ""
	if (opts.ff != ""):
		secondIn = open(opts.ff)
		p2 = Parser()
		results2 = p.parse(secondIn)
		
	printFeat(results,opts.label,opts.iname,opts.status,opts.libSVM,opts.flab,opts.su,int(opts.maxF),opts.norm,opts.log,opts.pA, opts.hyper,results2,opts.wpf,opts.to)
