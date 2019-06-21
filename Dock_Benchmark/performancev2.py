import json

time_c = bool(int(input("0: WallTime \n1: ExecutionTime\nChoix : ")))

proc_dict={'Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz':11173, 'Intel(R) Core(TM) i7-4770K CPU @ 3.50GHz':10077, 'Intel(R) Core(TM) i7-3770K CPU @ 3.50GHz':9508, 'AMD Ryzen 7 1700X Eight-Core Processor':14677, 'AMD Ryzen 7 2700X Eight-Core Processor':16982, 'Intel(R) Core(TM) i7-4790 CPU @ 3.60GHz':9987 }

ghz_dict={'Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz':4, 'Intel(R) Core(TM) i7-4770K CPU @ 3.50GHz':3.5, 'Intel(R) Core(TM) i7-3770K CPU @ 3.50GHz':3.5, 'AMD Ryzen 7 1700X Eight-Core Processor':3.4, 'AMD Ryzen 7 2700X Eight-Core Processor':3.7, 'Intel(R) Core(TM) i7-4790 CPU @ 3.60GHz':3.6 }

#Pour chaque coupe recepteur/ligand, pour chaque plateforme utilisee, on souhaite calculer une estimation de l'exe ramnene au score benchmark => un ordi avec des meilleur score, aura fait un meilleur temps pas a cause des capacites de ces processeurs 

def recup_ls_tps(fichier, parm="result"):
	temps_exe = []
	temps_setup = []
	if(parm == "result"):
		with open(fichier, 'r') as file:
			for line in file:
				temps_exe.append(float(line.split("\t")[0]))#*proc_dict["Intel(R) Core(TM) i7-4770K CPU @ 3.50GHz"]
	else:
		with open(fichier, "r") as file:
			data=file.read()
		dict_tasks=json.loads(data)
		for i,task in enumerate(dict_tasks):
			mesure=0
			for proc in task['status']['executionTimeByCpuModel']:
				if(time_c):
					mesure+=int(proc["time"])#*proc_dict[proc["model"]]
				else:
					mesure+=int(task['status']["wallTimeSec"])#*proc_dict[proc["model"]]
			if(i%2==0):	
				temps_exe.append(mesure)
				temps_setup.append(mesure)
			else:
				temps_exe[-1]+=mesure

	return(temps_exe,temps_setup)

tps_exe_s, tps_setup_s=recup_ls_tps("results_cloud_single.json", "json")
tps_exe_o, tps_setup_o=recup_ls_tps("results_cloud_local.json", "json")
tps_exe_g, tps_setup_g=recup_ls_tps("results_cloud_grouped.json", "json")
tps_exe_l=recup_ls_tps("temps_exe_local.result")[0]

pos_erreurs=[4, 40]

#Calcul d'un ratio, temps setup/temps exe
rat_set_exe=0
gbl_o=0
gbl_s=0
gbl_g=0
gbl_l=0

for i,v in enumerate(tps_exe_l):
	if v/3.5<100:
		pos_erreurs.append(i)

for i in range(len(tps_exe_s)):
	if i not in pos_erreurs:
		rat_set_exe+=tps_setup_s[i]/tps_exe_s[i]+tps_setup_g[i]/tps_exe_g[i]
		gbl_o+=tps_exe_o[i]
		gbl_s+=tps_exe_s[i]
		gbl_g+=tps_exe_g[i]
		gbl_l+=tps_exe_l[i]

rat_set_exe=rat_set_exe/len(tps_exe_s+tps_exe_g)

moy_o=gbl_o/(len(tps_exe_o)-len(pos_erreurs))
moy_s=gbl_s/(len(tps_exe_s)-len(pos_erreurs))
moy_g=gbl_g/(len(tps_exe_g)-len(pos_erreurs))
moy_l=gbl_l/(len(tps_exe_l)-len(pos_erreurs))

acc_o=gbl_l/gbl_o
acc_s=gbl_l/gbl_s
acc_g=gbl_l/gbl_g

print("\nRésulats de performance d'instance de Lightdock, avec pour paramètres les 50 premiers couples de la protein-protein benchmark, 64 swarms et 80 glowworms")
print("\nExecution locale\n\tTemps global (sec): "+str(gbl_l)+"\tTemps global (h): "+str(gbl_l/3600)+"\n\tTemps moyen (sec): "+str(moy_l)+"\tTemps moyen (min): "+str(moy_l/60))
print("Execution qarnot\n\tTemps global (sec): "+str(gbl_o)+"\tTemps global (h): "+str(gbl_o/3600)+"\n\tTemps moyen (sec): "+str(moy_o)+"\tTemps moyen (min): "+str(moy_o/60))
print("Execution solo\n\tTemps global (sec): "+str(gbl_s)+"\tTemps global (h): "+str(gbl_s/3600)+"\n\tTemps moyen (sec): "+str(moy_s)+"\tTemps moyen (min): "+str(moy_s/60))
print("Execution grouped\n\tTemps global (sec): "+str(gbl_g)+"\tTemps global (h): "+str(gbl_g/3600)+"\n\tTemps moyen (sec): "+str(moy_g)+"\tTemps moyen (min): "+str(moy_g/60))

print("\nAcceleration en executant le meme decoupage en cloud: "+str(acc_o))
print("Acceleration en executant decoupage une swarm un processeur: "+str(acc_s))
print("Acceleration par un decoupage d'un groupe de nuées par processeur: "+str(acc_g))


