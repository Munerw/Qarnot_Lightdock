#!/usr/bin/env python
import sys
import os
import operator
import time
import shutil

###Setup arguments
print("** Setup arguments **")

#Path to files
dir_path = raw_input("\tRelative path to file's directory :\n\t")

#Number of swarms
swarm = 0
while(swarm <1):
	swarm = input("\tNumber of swarms of the simulation : \n\t")
glow = 0
while(glow <1):
	glow = input("\tNumber of glowworms for each swarms : \n\t")
#Other options
args_setup= raw_input("\tOptions to add in the setup command: \n\t")

#Simulation arguments
print("** Simulation arguments **")
#Number of steps in a simulation
steps=input("\tNumber of steps in a simulation : \n\t")
#Other options
args_simul= raw_input("\tOptions to add in the simulation command: \n\t")
if(args_simul):
	args_simul+" "

#List of all files in the receptor directory
list_pdb = os.popen("ls "+dir_path).read().split("\n")[:-1]

liste=[]
for pdb in list_pdb:
	if("_r.pdb" in pdb):
		liste.append(pdb.split("_r.pdb")[0])

LIGHTDOCK_HOME = os.environ.get('LIGHTDOCK_HOME') 

#Create a bucket on Qarnot plateform
def creation_files(mol):
	if(not(os.path.exists(LIGHTDOCK_HOME+"/dock_"+mol))):
		os.mkdir(LIGHTDOCK_HOME+"/dock_"+mol)
	shutil.copyfile(dir_path+"/"+mol+"_r.pdb", LIGHTDOCK_HOME + "/dock_"+mol+"/"+mol+"_r.pdb")
	shutil.copyfile(dir_path+"/"+mol+"_l.pdb", LIGHTDOCK_HOME + "/dock_"+mol+"/"+mol+"_l.pdb")

exe_time=[]

for pdb in liste: 
	with open("lig.index", "w+")as file:
		file.write(pdb+"\n")
	start_time=time.time()
	creation_files(pdb)
	os.system("python"+" ${LIGHTDOCK_HOME}/setup_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+args_setup)
	os.system("python"+" ${LIGHTDOCK_HOME}/simul_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+str(steps)+" "+args_simul)
	total_time=time.time()-start_time
	exe_time.append(total_time)	

with open("temps_setup.result", "w+")as file:
	for pos in range(len(exe_time)):
		file.write(str(exe_time[pos])+"\t"+liste[pos]+"\n")

print("### End of Qarnot Docking ###")

