#!/usr/bin/env python
import sys
import os
import operator
import time
import shutil

###Setup arguments
print("** Setup arguments **")
#Path to receptor
rec_dir_path = raw_input("\tRelative path to receptor's directory :\n\t")
#Path to ligand
lig_dir_path = raw_input("\tRelative path to ligand's directory :\n\t")
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
list_rec_pdb = os.popen("ls "+rec_dir_path).read().split("\n")[:-1]
#List of all files in the ligand directory
list_lig_pdb = os.popen("ls "+lig_dir_path).read().split("\n")[:-1]

list_rec=[]
list_lig=[]
for rec in list_rec_pdb:
	list_rec.append(rec.split(".")[0])
for lig in list_lig_pdb:
	list_lig.append(lig.split(".")[0])

LIGHTDOCK_HOME = os.environ.get('LIGHTDOCK_HOME') 

def creation_files(rec, lig):
	if(not(os.path.exists(LIGHTDOCK_HOME+"/dock_"+rec+"_"+"vs_"+lig))):
		os.mkdir(LIGHTDOCK_HOME+"/dock_"+rec+"_"+"vs_"+lig)
	shutil.copyfile(rec_dir_path+"/"+rec+".pdb", LIGHTDOCK_HOME + "/dock_"+rec+"_"+"vs_"+lig+"/"+rec+".pdb")
	shutil.copyfile(lig_dir_path+"/"+lig+".pdb", LIGHTDOCK_HOME + "/dock_"+rec+"_"+"vs_"+lig+"/"+lig+".pdb")

for rec in list_rec:
	for lig in list_lig:
		with open("lig.index", "w+")as file:
			file.write(rec+"\n")
			file.write(lig+"\n")
		creation_files(rec, lig)
		os.system("python"+" ${LIGHTDOCK_HOME}/setup_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+args_setup)
		os.system("python"+" ${LIGHTDOCK_HOME}/simul_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+str(steps)+" "+args_simul)


print("### End of Qarnot Docking ###")

