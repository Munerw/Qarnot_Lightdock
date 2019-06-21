# -*- coding: utf-8 -*-
"""This module defines TCL file for VMD program.
Questions/Problems: karolami@pitt.edu
"""

__all__ = ['writeVMDstiffness', 'writeDeformProfile', 'calcChainsNormDistFluct']

import os
from os.path import abspath, join, split, splitext

import numpy as np

from prody import LOGGER, SETTINGS, PY3K
from prody.atomic import AtomGroup, sliceAtoms
from prody.utilities import openFile, isExecutable, which, PLATFORM, addext, checkCoords
from prody.proteins import writePDB

from .nma import NMA
from .anm import ANM
from .gnm import GNM, ZERO
from .pca import PCA
from .mode import Vector, Mode
from .modeset import ModeSet
from .nmdfile import viewNMDinVMD, pathVMD, getVMDpath, setVMDpath

def writeVMDstiffness(stiffness, pdb, indices, k_range, filename='vmd_out', \
                      select='protein and name CA', loadToVMD=False):
   
    """
    Returns three files starting with the provided filename and having 
    their own extensions:

    (1) A PDB file that can be used in the TCL script. 

    (2) TCL file containing vmd commands for loading PDB file with accurate 	
    vmd representation. Pair of residues with selected *k_range* of 
    effective spring constant are shown in VMD respresentation with 
    solid line between them. If more than one residue is selected in 
    *indices*, different pair for each residue will be colored in the 
    different colors.

    (3) TXT file containing pair of residues with effective spring constant 
    in selected range *k_range*.    

    .. note::

       #. This function skips modes with zero eigenvalues.
       #. If a :class:`.Vector` instance is given, it will be normalized
          before it is written. It's length before normalization will be
          written as the scaling factor of the vector.
          

    :arg stiffness: mechanical stiffness profile calculated with 
        :func:`.calcMechStiff`
    :type stiffness: :class:`~numpy.ndarray`

    :arg pdb: a coordinate set or an object with ``getCoords`` method
    :type pdb: :class:`~numpy.ndarray`, :class:`.Atomic` 

    :arg indices: an amino acid number or a pair of amino acid numbers
    :type indices: list

    :arg k_range: effective force constant value or range of values
    :type k_range: int, float, list
    
    :arg select: a selection or selection string
        default is 'protein and name CA'
    :type select: :class:`.Select`, str

    :arg loadToVMD: whether to load VMD and run the tcl file
        default is False
    :type loadToVMD: bool 

    """
    if not isinstance(filename, str):
        raise TypeError('filename should be a string')

    try:
        _, coords_sel = sliceAtoms(pdb, select)
        resnum_list = coords_sel.getResnums()
        coords = (coords_sel._getCoords() if hasattr(coords_sel, '_getCoords') else
                  coords_sel.getCoords())
    except AttributeError:
        try:
            checkCoords(coords_sel)
        except TypeError:
            raise TypeError('pdb must be a Numpy array or an object '
                            'with `getCoords` method')
    
    if len(indices) == 0:
        raise ValueError('indices cannot be an empty array')

    if len(indices) == 1:
        indices0 = indices[0] - resnum_list[0]
        indices1 = indices[0] - resnum_list[0]
    elif len(indices) == 2:
        indices0 = indices[0] - resnum_list[0]
        indices1 = indices[1] - resnum_list[0]

    out = openFile(addext(filename, '.tcl'), 'w')
    out_txt = openFile(addext(filename,'.txt'), 'w')
    writePDB(filename + '.pdb', pdb)

    LOGGER.info('Creating VMD file.')
    
    out.write('display rendermode GLSL \n')
    out.write('display projection orthographic\n')
    out.write('color Display Background white\n')
    out.write('display shadows on\n')
    out.write('display depthcue off\n')
    out.write('axes location off\n')
    out.write('stage location off\n')
    out.write('light 0 on\n')
    out.write('light 1 on\n')
    out.write('light 2 off\n')
    out.write('light 3 on\n')
    out.write('mol addrep 0\n')
    out.write('display resetview\n')
    out.write('mol new {./'+str(filename)+'.pdb} type {pdb} first 0 last -1 step 1 waitfor 1\n')
    out.write('mol modselect 0 0 protein\n')
    out.write('mol modstyle 0 0 NewCartoon 0.300000 10.000000 4.100000 0\n')
    out.write('mol modcolor 0 0 Structure\n')
    out.write('mol color Structure\n')
    out.write('mol representation NewCartoon 0.300000 10.000000 4.100000 0\n')
    out.write('mol selection protein\n')
    out.write('mol material Opaque\n')

    colors = ['blue', 'red', 'gray', 'orange','yellow', 'tan','silver', 'green', \
    'white', 'pink', 'cyan', 'purple', 'lime', 'mauve', 'ochre', 'iceblue', 'black', \
    'yellow2','yellow3','green2','green3','cyan2','cyan3','blue2','blue3','violet', \
    'violet2','magenta','magenta2','red2','red3','orange2','orange3']*50
    
    color_nr = 1 # starting from red color in VMD
    ResCounter = []
    for r in range(indices0, indices1 + 1):
        baza_col = [] # Value of Kij is here for each residue
        nr_baza_col = [] # Resid of aa are here
        out.write("draw color "+str(colors[color_nr])+"\n")
            
        for nr_i, i in enumerate(stiffness[r]):
            if k_range[0] < float(i) < k_range[1]:
                baza_col.append(i)
                nr_baza_col.append(nr_i+resnum_list[0])
                resid_r = str(coords_sel.getResnames()[r])+str(r+resnum_list[0])
                resid_r2 = str(coords_sel.getResnames()[nr_i])+str(nr_i+resnum_list[0])
                    
                if len(baza_col) == 0: # if base is empty then it will not change the color
                    color_nr = 0
                else:
                    out.write("draw line "+'{'+str(coords[r])[1:-1]+'} {'+\
                       str(coords[nr_i])[1:-1]+'} width 3 style solid \n')
                    out_txt.write(resid_r + '\t' + resid_r2 + '\t' + str(i) + '\n')
                    ResCounter.append(len(baza_col))
                        
            else: pass
        
        if len(baza_col) != 0:
            out.write('mol addrep 0\n')
            out.write('mol modselect '+str(color_nr+1)+' 0 protein and name CA and resid '+ \
                       str(r+resnum_list[0])+' '+str(nr_baza_col)[1:-1].replace(',','')+'\n')
            out.write('mol modcolor '+str(color_nr+1)+' 0 ColorID '+str(color_nr)+'\n')
            out.write('mol modstyle '+str(color_nr+1)+' 0 VDW 0.600000 12.000000\n')
            out.write('mol color ColorID '+str(color_nr)+'\n')
            out.write('mol representation VDW 1.000000 12.000000 \n')
            out.write('mol selection protein and name CA and resid '+ \
            str(r+resnum_list[0])+' '+str(nr_baza_col)[1:-1].replace(',','')+'\n')
            
            out.write('mol material Opaque \n')
            color_nr = color_nr + 1
                
    out.write('mol addrep 0\n')
    out.close()
    out_txt.close()

    if loadToVMD:
        from prody import pathVMD
        LOGGER.info('File will be loaded to VMD program.')
        os.system(pathVMD()+" -e "+str(filename)+".tcl")
                                        
    if len(ResCounter) > 0:
        return out
    elif len(ResCounter) == 0:
        LOGGER.info('There is no residue pair in this Kij range.')
        return 'None'   


def writeDeformProfile(stiffness, pdb, filename='dp_out', \
                       select='protein and name CA', \
                       pdb_selstr='protein', loadToVMD=False):

    """Calculate deformability (plasticity) profile of molecule based on mechanical
    stiffness matrix (see [EB08]_).

    :arg model: this is an 3-dimensional NMA instance from a :class:`.ANM
        calculations
    :type model: :class:`.ANM`

    :arg pdb: a coordinate set or an object with ``getCoords`` method
    :type pdb: :class:`numpy.ndarray`    
    
    Note: selection can be done using ``select`` and ``pdb_selstr``. 
    ``select`` defines ``model`` selection (used for building :class:`.ANM` model) 
    and ``pdb_selstr`` will be used in VMD program for visualization. 
    
    By default files are saved as *filename* and loaded to VMD program. To change 
    it use ``loadToVMD=False``.
     
    Mean value of mechanical stiffness for molecule can be found in occupancy column
    in PDB file.

    """
    
    _, pdb = sliceAtoms(pdb, pdb_selstr)
    _, coords = sliceAtoms(pdb, select)
    meanStiff = np.mean(stiffness, axis=0)
    
    out_mean = open(filename+'_mean.txt','w')   # mean value of Kij for each residue
    for nr_i, i in enumerate(meanStiff):
        out_mean.write("{} {}\n".format(nr_i, i))
    out_mean.close()
    
    from collections import Counter
    aa_counter = Counter(pdb.getResindices()) 
    
    meanStiff_all = []        
    for i in range(coords.numAtoms()):
        meanStiff_all.extend(list(aa_counter.values())[i]*[round(meanStiff[i], 2)])
        
    writePDB(filename, pdb, occupancy=meanStiff_all)                
    LOGGER.info('PDB file with deformability profile has been saved.')
    LOGGER.info('Creating TCL file.')
    out_tcl = open(filename+'.tcl','w')
    out_tcl.write('display resetview \nmol addrep 0 \ndisplay resetview \n')
    out_tcl.write('mol new {./'+filename+'.pdb} type {pdb} first 0 last -1 step 1 waitfor 1 \n')
    out_tcl.write('animate style Loop \ndisplay projection Orthographic \n')
    out_tcl.write('display depthcue off \ndisplay rendermode GLSL \naxes location Off \n')
    out_tcl.write('color Display Background white \n')
    out_tcl.write('mol modstyle 0 0 NewCartoon 0.300000 10.000000 4.100000 0 \n')
    out_tcl.write('mol modmaterial 0 0 Diffuse \nmol modcolor 0 0 Occupancy \n')
    out_tcl.write('menu colorscalebar on \n')
    out_tcl.close()

    if loadToVMD:
        from prody import pathVMD
        LOGGER.info('File will be loaded to VMD program.')
        os.system(pathVMD()+" -e "+str(filename)+".tcl")


def calcChainsNormDistFluct(coords, ch1, ch2, cutoff=10., percent=5, rangeAng=5, \
                                        filename='ch_ndf_out', loadToVMD=False):

    '''Calculate protein-protein interaction using getNormDistFluct() from 
    :class:`.GNM` model. It is assigned to protein complex.
    
    :arg coords: a coordinate set or an object with ``getCoords`` method. 
    :type coords: :class:`numpy.ndarray`.

    :arg ch1: first chain name
    :type ch1: 'A' or other letter as a string

    :arg ch2: second chain name 
    :type ch2: string

    :arg cutoff: cutoff distance (Å) for pairwise interactions
        in Kirchhoff matrix, default is 10.0 Å
    :type cutoff: float

    :arg percent: percent of the highest and lowest results displayed in _VMD
        program, default is 5% 
    :type percent: int or float

    :arg rangeAng: cutoff range of protein-protein interactions, default is 5 Å
    :type rangeAng: int or float

    :arg filename: name of tcl file from _VMD program
    :type filename: str
    
    By default files are saved as *filename* and loaded to VMD program. 
    To change it use ``loadToVMD=False``. 
    
    UNDER PREPARATION.. problems with not complete structures
    '''
    
    sele1 = coords.select('name CA and same residue as exwithin '+str(rangeAng) \
                                                        +' of chain '+str(ch1))
    sele2 = coords.select('name CA and same residue as exwithin '+str(rangeAng) \
                                                        +' of chain '+str(ch2))
    num1 = len(list(set(sele1.getResnums())))    
    num2 = len(list(set(sele2.getResnums())))

    LOGGER.info('Analized chains: {0}, {1}'.format(ch1, ch2))
    LOGGER.info('Number of selected amino acids: chain {0}-{1}aa, chain {2}-{3}aa'
                            .format(ch1, num2, ch2, num1))
                            
    seleALL = sele1 + sele2 
    seleALL_ca = seleALL.select('protein and name CA')

    from .gnm import GNM
    model = GNM('prot analysis')
    model.buildKirchhoff(seleALL_ca, cutoff)
    model.calcModes()
    ndf_matrix0 = model.getNormDistFluct(seleALL_ca)
    ndf_c1 = np.delete(ndf_matrix0, np.s_[0:num1], axis=0)  # rows
    ndf_matrix = np.delete(ndf_c1, np.s_[num1:(num1+num2)], axis=1) 
    
    perc = (np.amax(ndf_matrix)-np.min(ndf_matrix))*percent*0.01
    maxRange = np.amax(ndf_matrix)-perc
    minRange = np.min(ndf_matrix)+perc
    
    writePDB(filename, coords)                
    out_tcl = open(filename+'.tcl','w')
    out_tcl.write('display resetview \nmol addrep 0 \ndisplay resetview \n')
    out_tcl.write('mol new {./'+filename+'.pdb} type {pdb} first 0 last -1 step 1 waitfor 1 \n')
    out_tcl.write('animate style Loop \ndisplay projection Orthographic \n')
    out_tcl.write('display depthcue off \ndisplay rendermode GLSL \naxes location Off \n')
    out_tcl.write('color Display Background white \n')
    out_tcl.write('mol modstyle 0 0 NewCartoon 0.300000 10.000000 4.100000 0 \n') 
    out_tcl.write('mol modselect 0 0 protein \nmol modcolor 0 0 Chain \n')
    out_tcl.write('mol modmaterial 0 0 BrushedMetal\n')
    out_tcl.write('m')

    mmRange = {'minRange':minRange,'maxRange':maxRange}
    ch = [ch2, ch1]
    color = ['1','7'] # red-maxRange, red-minRange
    out_pairs = open(filename+'_pairs.txt','w')
    for nr_j,j in enumerate(mmRange):
        if j == 'minRange':
            x,y = np.where(ndf_matrix < mmRange[j])
            out_pairs.write(j+' (< '+str(mmRange[j])+') \n')
        elif j == 'maxRange':
            x,y = np.where(ndf_matrix > mmRange[j])
            out_pairs.write(j+' (> '+str(mmRange[j])+') \n')
        vmd_ch_list = [[],[]]
        for i in range(len(x)):
            out_pairs.write("{}{}  {}{}  {}\n".format(sele1.select('protein and name \
            CA').getResnames()[y[i]], sele1.select('protein and name CA').getResnums()[y[i]], \
            sele2.select('protein and name CA').getResnames()[x[i]], sele2.select('protein and \
            name CA').getResnums()[x[i]], ndf_matrix[x[i],y[i]]))
            vmd_ch_list[0].append(sele1.select('protein and name CA').getResnums()[y[i]])
            vmd_ch_list[1].append(sele2.select('protein and name CA').getResnums()[x[i]])
        out_pairs.write('\n')
        for k in range(len(vmd_ch_list)):
            out_tcl.write('mol addrep 0\n')
            out_tcl.write('mol modselect '+color[nr_j]+' 0 protein and name chain '+ch[k]+\
                 ' and resid '+str(list(set(vmd_ch_list[k]))).replace(',','')[1:-1]+'\n')
            out_tcl.write('mol modcolor '+color[nr_j]+' 0 ColorID '+color[nr_j]+'\n')
            out_tcl.write('mol modstyle '+color[nr_j]+' 0 CPK 1.000000 0.300000 12.000000 12.000000\n')
            out_tcl.write('mol color ColorID '+color[nr_j]+'\n')
            out_tcl.write('mol representation CPK 1.000000 0.300000 12.000000 12.000000\n')
            out_tcl.write('mol selection protein and chain '+ch[k]+' and resid '\
                              +str(list(set(vmd_ch_list[k]))).replace(',','')[1:-1]+'\n')
            out_tcl.write('mol material Opaque \n')
            #out_tcl.write('mol addrep 0\n')
        
        LOGGER.info('Finded residues in {0}: {1}'.format(mmRange.keys()[nr_j],\
                    len(list(set(vmd_ch_list[1])))+len(list(set(vmd_ch_list[0])))))
        LOGGER.info('chain {0} and resid {1}'.format(ch[0], \
                       str(list(set(vmd_ch_list[0]))).replace(',','')[1:-1]))
        LOGGER.info('chain {0} and resid {1}'.format(ch[1], \
                       str(list(set(vmd_ch_list[1]))).replace(',','')[1:-1]))
    out_tcl.write('mol addrep 0\n')
    LOGGER.info('Created TCL file.')
    out_tcl.close()
    out_pairs.close()

    if loadToVMD:
        from prody import pathVMD
        LOGGER.info('File will be loaded to VMD program.')
        os.system(pathVMD()+" -e "+str(filename)+".tcl")

    return ndf_matrix

