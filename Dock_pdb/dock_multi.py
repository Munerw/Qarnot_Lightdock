#!/usr/bin/env python
import sys
import qarnot
import os
import operator

#Create and execute a task on Qarnot plateforme
def askingQarnot(task_name, rec, bucket, nb_instances, cmd):
	
	error_happened=False
	
	try:
		task = conn.create_task(task_name+rec, "docker-batch", nb_instances)
		task.resources.append(bucket)
		task.results=bucket
		task.constants['DOCKER_REPO'] = "erwanmunera/docking"
		task.constants['DOCKER_TAG'] = "dock_anyfile"
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

#Create a bucket on Qarnot plateform
def creation_bucket(rec, list_lig):
	output_bucket = conn.create_bucket("dock_anyfile")
	output_bucket.add_file(rec_dir_path+"/"+rec+".pdb")
	for lig in list_lig:
		output_bucket.add_file(lig_dir_path+"/"+lig+".pdb")
	output_bucket.add_file("lig.index")
	return output_bucket

for rec in list_rec:
	with open("lig.index", "w+")as f:
		f.write(rec+"\n")
		for lig in list_lig:
			f.write(lig+"\n")
		f.write("\n")

	askingQarnot("setup_", rec, creation_bucket(rec, list_lig), len(list_lig), "python"+" ../prog/setup_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+args_setup)
	askingQarnot("dock_", rec, conn.create_bucket("dock_anyfile"), len(list_lig)*swarm, "python"+" ../prog/simul_dock.py " +" "+ str(swarm)+ " "+str(glow)+" "+str(steps)+" "+args_simul)

#Download the output file on https://console.qarnot.com/app/buckets/
