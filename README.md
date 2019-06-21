#### Table of Contents

- [1. Introduction](#1-introduction)
- [2. Installation](#2-installation)
- [3. Executing Lightdock](#3-executing-lightdock)
- [4. Documentation](#4-documentation)
- [5. External Links](#5-external-links)

## 1. Introduction
Lightdock is a docking framework written in Python (version 2.7) and prepared to scale in HPC architectures. More details about Lightdock functionalities can be found on [Lightdock's documentation page](https://brianjimenez.github.io/lightdock/) or on the [GitHub repository](https://github.com/brianjimenez/lightdock#1-introduction) of the project. Different implementations of Lightodck where made in an attempt to reduce the time needed to realize the docking of a group of receptor/ligand pair. To achieve this purpose, Lightdock was implemented to run on Qarnot's cloud computing framework: [QWare](https://computing.qarnot.com/).

## 2. Installation
### 2.1 Download
All scripts used to execute Ligthdock can be found either in the `Dock_Benchmark` or `Dock_pdb` directories. 
Depending on what you intend to do, downloading the main directory won't be useful. To a local use of Lightdock, an implementation of Lightdock on your computer, either `local_benchmark` or `local_anyfile`, and the script that is linked to them are needed: `dock_local.py` in `Dock_Benchmark` in order to execute the `local_benchmark` implementation and `dock_local_pdb.py` in `Dock_pdb` in order to execute `local_anyfile` implementation. But to run Ligthdock on Qarnot's computing service, only a script located in the `Dock_Benchmark` or `Dock_pdb` directories will be needed.

### 2.2 Ligthdock local implementation
#### 2.2.1 Dependencies
LightDock has the following dependencies:

* **Python 2.7.x**
* Nose (<http://nose.readthedocs.io/en/latest/>)
* NumPy (<http://www.numpy.org/>)
* Scipy (<http://www.scipy.org/>)
* Cython (<http://cython.org/>)
* BioPython (<http://biopython.org>)
* MPI4py (<http://pythonhosted.org/mpi4py/>)
* ProDy (<http://prody.csb.pitt.edu/>)
* Freesasa (only if `cpydock` scoring function is used and to run the complete test set, <http://freesasa.github.io/>)

To install all this packages, the directory containing Ligthdock local implementation must be made as the working directory. Then run this code :
```bash
export LIGHTDOCK_HOME=$(pwd)
export PATH=$PATH:$LIGHTDOCK_HOME/bin:$LIGHTDOCK_HOME/bin/post:$LIGHTDOCK_HOME/bin/support
export PYTHONPATH=$PYTHONPATH:$LIGHTDOCK_HOME
bash dependencies.sh
```

### 2.3 Ligthdock implementation using Qarnot's computing service
#### 2.3.1 Getting an API token
To execute Lightdock with Qarnot's computing, an API token is required.
To get one, register or log in to Qarnot's service, using this [link](https://account.qarnot.com/). Then, under the [compute link](https://account.qarnot.com/compute) your API token will be revealed.
Copy this token, and paste it in the `samples.conf` files that are located in the directories named `Dock_Benchmark` and `Dock_pdb`.

#### 2.3.2 Dependencies
As the Python script use Qarnot Python SDK, an installation of Qarnot package is required. It can easily be achieved with `pip`:
```bash
pip install qarnot
```

## 3. Executing Lightdock
### 3.1 Docking a group of receptors against a group of ligands.
#### 3.1.1 Locally
First, you will need to correctly install the `local_anyfile` implementation of Lightdock. Then run the script `dock_local_pdb.py` located in the `Dock_pdb` directory:
```bash
python dock_local_pdb.py
```
After setting all parameters, the script will realize the docking of one receptor at a time of the directory indicated against the group of ligands.

#### 3.1.2 With Qarnot's computing service
This can be done using the `dock_multi.py` script in the `Dock_pdb` directory. `dock_multi.py` use a docker container named `docker_anyfile` to execute the docking of a receptor or a group of receptor and a group of ligands using Qarnot's computing service. In order to achieve this, after running the script using:
```bash
python dock_multi.py
```
After setting all parameters, the script will realize the docking of one receptor at a time of the directory indicated against the group of ligands.
 
### 3.2 Docking a group of receptor/ligand 
In many case, a receptor and a ligand that form a complex will be integrated in a data bank as `complex_r` for the receptor and `complex_l` for the ligand. A good example of this can be found in the `Benchmark` directory that list a group of receptor and ligand pair known to bind and form a complex. Docking all the pair can be done using the following script.
#### 3.2.1 Locally
First, you will need to correctly install the `local_benchmark` implementation of Lightdock. Then run the script `dock_local.py` located in the `Dock_Benchmark` directory:
```bash
python dock_local.py
```
After setting all parameters, the script will realize the docking of one receptor and ligand pair at a time, located in the directory indicated.

#### 3.2.2 With Qarnot's computing service
All files in the `Dock_Benchmark` directory which are named `dock_cloud_*.py` will execute Lightdock on a group of receptor/ligand pair with qarnot's computing service. After modifying the `samples.conf` file, run a script with a python command:
```bash
python dock_cloud_*.py
```
Each script has a different task repartition and will perform differently. From worse to better:
* `dock_cloud_original.py` use the same task repartition as a local use. Everything is done in a single chunk and the docking of all the receptor/ligand pair is executed one at a time.
* `dock_cloud_single.py` create a chunk for each [swarm](https://brianjimenez.github.io/lightdock/#1-introduction). The docking of all the receptor/ligand pair is executed one at a time.
* `dock_cloud_group.py` divide all the swarm in group of 16 and create a chunk for each of this group. The docking of all the receptor/ligand pair is executed one at a time.
* `dock_cloud_multi_original.py` use the same task repartition as a local use and everything is done in a single chunk. The docking of all the receptor/ligand pair is executed simultaneously.

### 3.3 Modify a Lightdock implementation
Creating a different task repartition can be accomplished by modifying those files in a Ligthodck's implementation:
* `/setup_dock.py`
* `/simul_dock.py` can be modified to avoid generating the models and creating the clusters.
* `/lightdock/constants.py`
* `/bin/simulation/`
* `/lightdock/prep/simulation.py`

#### 3.3.1 Locally
Lightdock's local implementation are `local_anyfile` and `local_benchmark`.

#### 3.3.2 Qarnot's coputing service
All Docker container directories can be found in the `Docker_Image` directory. 

## 4. Documentation
[Qarnot's Python tutorial](https://computing.qarnot.com/developers/get-started/python-tutorial)
[Lightdock's complete documentation](https://brianjimenez.github.io/lightdock)

## 5. External Links
[Lightdock's documentation](https://brianjimenez.github.io/lightdock/)
[Lightdock's GitHub project page](https://github.com/brianjimenez/lightdock#1-introduction)
[Docker Hub](https://hub.docker.com/)
[Qarnot's computing service](https://computing.qarnot.com/developers/overview/qarnot-computing-home)
[Qarnot Python SDK](https://computing.qarnot.com/documentation/sdk-python/)

