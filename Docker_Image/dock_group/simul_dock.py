import sys
import os
import operator
import csv
import time
from lightdock.constants import REC_PATH, LIG_PATH, SWARM_ID, DEFAULT_SWARM_FOLDER, DEFAULT_OUTPATH

#Number of swarms
swarm=sys.argv[1]
#Number of glowworms per swarms
glow=sys.argv[2]
#Number of steps in simulation
steps = int(sys.argv[3])
#Rest of the args
args_simul=(" ".join(str(e) for e in sys.argv[4:]))

args_simul+=" "
		
#simulation
os.system("../prog/bin/lightdock %s%ssetup.json %d"%(args_simul, DEFAULT_OUTPATH, steps))

step=[]
for i in range(steps):
	if i%10==0:
		step.append(i)

if(not steps%10==0):
	step.append(steps)

for i in range(int(swarm)):
		for pas in step:	
			os.system("python ../prog/bin/post/lgd_generate_conformations.py "+REC_PATH+".pdb"+" "+LIG_PATH+".pdb"+" "+DEFAULT_SWARM_FOLDER+str(i)+"/gso_"+str(pas)+".out "+str(glow))
			os.system("python ../prog/bin/post/lgd_cluster_bsas.py "+" "+DEFAULT_SWARM_FOLDER+str(i)+"/gso_"+str(pas)+".out")

