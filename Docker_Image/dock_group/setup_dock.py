import sys
import os
import operator
import csv
import time
from lightdock.constants import REC_PATH, LIG_PATH, DEFAULT_SWARM_FOLDER  

#Number of swamrs
swarm=sys.argv[1]
#Number of glowworms per swarms
glow=sys.argv[2]
#Rest of the args
args_setup=(" ".join(str(e) for e in sys.argv[3:]))

args_setup+=" "	

os.system("../prog/bin/lightdock_setup %s%s %s %s %s"%(args_setup, REC_PATH+".pdb", LIG_PATH+".pdb", swarm, glow))
	
for i in range(int(swarm)):
	saving_path = "%s%d" % (DEFAULT_SWARM_FOLDER, i)
	with open(os.path.join(saving_path, 'init.txt'), 'w'):
	    	pass


