#!/usr/bin/env python

import sys, inspect, importlib, os, numpy as np
from os.path import exists, join

def main(dir):
	#Loading data
	files = [f for f in os.listdir(dir) if ".nii" in f]

	#Cutting data
	cutOff = 5
	for i in range(cutOff-1, -1, -1):
		files.remove(files[i])
	
	#Finding reference frame index
	ref = int(round(len(files)/2.0) - 1)

	#Flirt options setup
	searchRange = "-5 5"
	options = " -searchrx " + searchRange + " -searchry " + searchRange + " -searchrz " + searchRange + " -dof 6"

	#Naming directories
	outDir = dir + "_OUT"
	omatDir = dir + "_OMAT"
	mDir = dir + "_MAT"
        # dir has form pathtodir/TP00, tail (TP00) used as a tag for filenames (JAB)
        tag  = os.path.split(dir)[1]

	#Making directories (check for pre-existing; JAB)
	if not exists(outDir):  os.mkdir(outDir)
	if not exists(omatDir): os.mkdir(omatDir)
	if not exists(mDir):    os.mkdir(mDir)

	#Registering reference
	identity = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        omat = join(omatDir,"%s_OMAT_%02d"%(tag,ref+cutOff)) # (JAB) Matrix written to directory omatDir
	np.savetxt(omat, np.array(identity))
	
	#Registering all other frames
	for i in range (1, len(files)):
		j = i
		#Chaining backwards from reference index
		if i <= ref:
			j = ref-i
			input = files[j + 1]
                        omat = join(omatDir,"%s_OMAT_%02d"%(tag,j+cutOff)) # (JAB)
		#Chaining forwards from reference index
		else:
			input = files[j - 1]
                        omat = join(omatDir,"%s_OMAT_%02d"%(tag,j+cutOff)) # (JAB)
		#(JAB) Address file in their respective subdirectories
		os.system("flirt -in " + dir + "/" + files[j] + " -ref " + dir + "/" + input + " -omat " + omat + options)

	#Loading matrix files
	omatFiles = [f for f in os.listdir(omatDir) if "OMAT" in f]

	#Storing matrix files into list 'm'
	m = []
	for f in omatFiles:
		#Opening file
		file = open(omatDir + "/" + f, "r") # (JAB)

		#Reading file
		content = [x.rstrip() for x in file.readlines()]

		#Storing file into list "m"
		m.append([([float(x) for x in line.split()]) for line in content])
	
	#Making resampled omatFiles by registering from parameter matrices in list 'm'
	target = 0
	for i in range(0, len(omatFiles)):
		m1 = identity
		
		#Matrix multiplication to the target frame
		for j in range(i, target, -1):
			m2 = np.array(m[j])

			if j <= ref:
				m2 = np.linalg.inv(np.array(m[j-1]))

			m1 = np.dot(m1, m2)
		
		#Writing matrix file	
		mFile = join(mDir,"%s_MAT_%02d"%(tag,i+cutOff)) # (JAB)
		np.savetxt(mFile, m1)

		#Creating resampled file
		out = join(outDir,"%s_OUT_%02d"%(tag,i+cutOff)) # (JAB)
		os.system("flirt -in " + dir + "/" + files[i] + " -ref " + dir + "/" + files[target] + " -applyxfm -init " + mFile + " -out " + out)


if __name__ == "__main__":
	#Passes parameters from command line
	args = inspect.getargspec(getattr(importlib.import_module("Flirt"), "main"))
   	z = len(args[0]) + 2
   	params=sys.argv[1:z]
   	main(*params)
