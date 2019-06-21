#!/usr/bin/env python
import sys
import qarnot
import os
import operator
import time
from threading import Thread

#Create and execute a task on Qarnot plateforme
def askingQarnot(task_name, bucket, nb_instances, cmd):
	
	error_happened=False
	
	try:
		task = conn.create_task(task_name, "docker-batch", nb_instances)
		task.resources.append(bucket)
		task.results=bucket
		task.constants['DOCKER_REPO'] = "erwanmunera/docking"
		task.constants['DOCKER_TAG'] = "dock_group"
		task.constants['DOCKER_CMD'] = cmd
		print("** Submitting %s..." % task.name)

		task.submit()

		done_setup=False
		while not done_setup:
			# Wait for the task to complete, with a timeout of 2 seconds.
			# This will return True as soon as the task is complete, or False
			# after the timeout.        
			done_setup = task.wait(0)
			
			# Display fresh stdout / stderr
			sys.stdout.write(task.fresh_stdout())
			sys.stderr.write(task.fresh_stderr())

		if task.state == "Failure":
			print("** %s >>> Errors: %s" % (task.name, task.errors[0]))
		    	error_happened = True	
	finally:
		if error_happened:
        		sys.exit(1)
 
# Create a connection, from which all other objects will be derived
conn = qarnot.Connection('samples.conf')

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

#Create a bucket on Qarnot plateform
def creation_bucket(mol):
	output_bucket = conn.create_bucket("dock_group")
	output_bucket.add_file(dir_path+"/"+mol+"_r.pdb")
	output_bucket.add_file(dir_path+"/"+mol+"_l.pdb")
	output_bucket.add_file("lig.index")
	return output_bucket

exe_time=[]

for pdb in liste:
	with open("lig.index", "w+")as file:
		file.write(pdb+"\n")
	nb=0
	if(swarm%16 !=0 ):
		nb+=1
	nb+=swarm/16
	start_time=time.time()
	askingQarnot("setup_group_"+pdb, creation_bucket(pdb), 1, "python"+" ../prog/setup_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+args_setup)
	askingQarnot("dock_group_"+pdb, conn.create_bucket("dock_group"), nb, "python"+" ../prog/simul_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+str(steps)+" "+args_simul)
	total_time=time.time()-start_time
	exe_time.append(total_time)

with open("temps_exe_group.result", "w+")as file:
	for pos in range(len(exe_time)):
		file.write(str(exe_time[pos])+"\t"+liste[pos]+"\n")

print("### End of Qarnot Docking ###")
print("Download the output file on https://console.qarnot.com/app/buckets/")
