#!/usr/bin/env python

"""Generates the top N structures in PDB format given a ranking file"""

import argparse
import os
import numpy as np
from lightdock.mathutil.cython.quaternion import Quaternion
from lightdock.util.analysis import read_lightdock_output
from lightdock.util.logger import LoggingManager
from lightdock.constants import DEFAULT_NMODES_REC, DEFAULT_NMODES_LIG, DEFAULT_REC_NM_FILE, DEFAULT_LIG_NM_FILE
from lightdock.pdbutil.PDBIO import parse_complex_from_file, write_pdb_to_file
from lightdock.structure.complex import Complex
from lightdock.structure.nm import read_nmodes
from lightdock.util.parser import CommandLineParser, get_lightdock_structures


log = LoggingManager.get_logger('lightdock_top')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="conformer_conformations")
    # Receptor
    parser.add_argument("receptor_structures", help="receptor structures: PDB file or list of PDB files",
                        type=CommandLineParser.valid_file, metavar="receptor_structure")
    # Ligand
    parser.add_argument("ligand_structures", help="ligand structures: PDB file or list of PDB files",
                        type=CommandLineParser.valid_file, metavar="ligand_structure")
    # Ranking file
    parser.add_argument("lightdock_ranking_file", help="LightDock ranking file",
                        type=CommandLineParser.valid_file, metavar="lightdock_ranking_file")
    # Number of structures to generate
    parser.add_argument("top", help="number of structures to generate", type=CommandLineParser.valid_integer_number,
                        metavar="top")

    args = parser.parse_args()

    # Receptor
    structures = []
    for structure in get_lightdock_structures(args.receptor_structures):
        log.info("Reading %s receptor PDB file..." % structure)
        atoms, residues, chains = parse_complex_from_file(structure)
        structures.append({'atoms': atoms, 'residues': residues, 'chains': chains, 'file_name': structure})
        log.info("%s atoms, %s residues read." % (len(atoms), len(residues)))
    receptor = Complex.from_structures(structures)

    # Ligand
    structures = []
    for structure in get_lightdock_structures(args.ligand_structures):
        log.info("Reading %s ligand PDB file..." % structure)
        atoms, residues, chains = parse_complex_from_file(structure)
        structures.append({'atoms': atoms, 'residues': residues, 'chains': chains, 'file_name': structure})
        log.info("%s atoms, %s residues read." % (len(atoms), len(residues)))
    ligand = Complex.from_structures(structures)

    # Read ranking file
    glowworms = read_lightdock_output(args.lightdock_ranking_file, initial=1, final=args.top)

    # Destination path is the same as the lightdock output
    destination_path = os.path.dirname(args.lightdock_ranking_file)

    # If normal modes used, need to read them
    nmodes_rec = nmodes_lig = None
    nm_path = os.path.abspath(os.path.dirname(args.receptor_structures))
    # Check NM file for receptor
    nm_rec_file = os.path.join(nm_path, DEFAULT_REC_NM_FILE + '.npy')
    if os.path.exists(nm_rec_file):
        nmodes_rec = read_nmodes(nm_rec_file)
    # Check NM file for ligand
    nm_lig_file = os.path.join(nm_path, DEFAULT_LIG_NM_FILE + '.npy')
    if os.path.exists(nm_lig_file):
        nmodes_lig = read_nmodes(nm_lig_file)

    for i, glowworm in enumerate(glowworms):
        receptor_pose = receptor.atom_coordinates[glowworm.receptor_id].clone()
        ligand_pose = ligand.atom_coordinates[glowworm.ligand_id].clone()
        # Use normal modes if provided:
        if nmodes_rec.any():
            for nm in range(DEFAULT_NMODES_REC):
                rec_extent = np.array([float(x) for x in glowworm.pose[7:7 + DEFAULT_NMODES_REC]])
                receptor_pose.coordinates += nmodes_rec[nm] * rec_extent[nm]
        if nmodes_lig.any():
            for nm in range(DEFAULT_NMODES_LIG):
                lig_extent = np.array([float(x) for x in glowworm.pose[-DEFAULT_NMODES_LIG:]])
                ligand_pose.coordinates += nmodes_lig[nm] * lig_extent[nm]

        # We rotate first, ligand it's at initial position
        rotation = Quaternion(glowworm.pose[3], glowworm.pose[4], glowworm.pose[5], glowworm.pose[6])
        ligand_pose.rotate(rotation)
        ligand_pose.translate([glowworm.pose[0], glowworm.pose[1], glowworm.pose[2]])

        write_pdb_to_file(receptor, os.path.join(destination_path, 'top_%s.pdb' % str(i+1)), receptor_pose)
        write_pdb_to_file(ligand,  os.path.join(destination_path, 'top_%s.pdb' % str(i+1)), ligand_pose)
    log.info("Generated %d conformations" % args.top)
