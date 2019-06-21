#!/usr/bin/env python

"""Filter LightDock final swarm results depending on the percentage of restraints satisfied"""

from __future__ import print_function
import sys
import os
import argparse
import shutil
import re
from prody.measure.contacts import Contacts
from prody import parsePDB, confProDy
from lightdock.util.logger import LoggingManager
from lightdock.util.analysis import read_ranking_file


# Disable ProDy output
confProDy(verbosity='info')
filtered_folder = 'filtered'

log = LoggingManager.get_logger('lgd_filter_restraints')


def get_structures(ranking, base_path='.'):
    structures = []
    for rank in ranking:
        swarm_id = rank.id_cluster
        glowworm_id = rank.id_glowworm
        score = rank.scoring
        structures.append([os.path.join(base_path, 
                                       'swarm_{}'.format(swarm_id), 
                                       'lightdock_{}.pdb'.format(glowworm_id)), score])
    return structures


def get_restraints(restraints_file):
    restraints_receptor = set()
    restraints_ligand = set()
    with open(restraints_file) as handle:
        for line in handle:
            line = line.rstrip(os.linesep)
            if line:
                if line.startswith('R'):
                    restraints_receptor.add(line.split[1])
                if line.startswith('L'):
                    restraints_ligand.add(line.split[1])
    return restraints_receptor, restraints_ligand


def parse_command_line():
    """Parses command line arguments"""
    parser = argparse.ArgumentParser(prog='lgd_filter_restraints')

    parser.add_argument("ranking_file", help="Path of ranking to be used", metavar="ranking_file")
    parser.add_argument("restraints_file", help="File including restraints", metavar="restraints_file")
    parser.add_argument("receptor_chains", help="Chains on the receptor partner", metavar="receptor_chains")
    parser.add_argument("ligand_chains", help="Chains on the receptor partner", metavar="ligand_chains")
    parser.add_argument("--cutoff", "-cutoff", "-c", help="Interaction cutoff",
                            dest="cutoff", type=float, default=5.0)
    parser.add_argument("--fnat", "-fnat", "-f", help="Structures with at least this fraction of native contacts",
                            dest="fnat", type=float)

    return parser.parse_args()


if __name__ == '__main__':
 
    # Parse command line
    args = parse_command_line()

    log.info("Calculating interface at {:3.1f}A".format(args.cutoff))

    # Get ranking
    ranking = read_ranking_file(args.ranking_file)

    # Get all the PDB structures in a given directory
    base_path = os.path.abspath(os.path.dirname(args.ranking_file))
    structures = get_structures(ranking, base_path)

    restraints_receptor, restraints_ligand = get_restraints(args.restraints_file)

    # Total number of restraints to be satisfied
    total = float(len(restraints_receptor) + len(restraints_ligand))

    if os.path.exists(filtered_folder):
        raise SystemExit("Folder {} already exists".format(filtered_folder))
    else:
        os.makedirs(filtered_folder)

    filter_passed = {}
    percentages = {}
    for pdb_file in structures:
        try:
            contacts_receptor = set()
            contacts_ligand = set()

            pdb = pdb_file[0]
            swarm_id = int(re.findall(r'swarm_\d+', pdb)[0].split('_')[-1])
            glowworm_id = int(re.findall(r'lightdock_\d+', pdb)[0].split('_')[-1])
            score = float(pdb_file[-1])

            # Read molecule and split by receptor and ligand
            if score > 0.0:
                molecule = parsePDB(pdb)
                receptor = molecule.select('protein and chain {}'.format(args.receptor_chains))
                ligand = molecule.select('protein and chain {}'.format(args.ligand_chains))

                # Contacts on receptor side
                protein_contacts = Contacts(receptor)
                contacts = protein_contacts.select(args.cutoff, ligand)
                if contacts:
                    for contact in contacts:
                        contacts_receptor.add("{}.{}.{}".format(contact.getChid(), contact.getResname(), contact.getResnum()))

                # Contacts on ligand side
                protein_contacts = Contacts(ligand)
                contacts = protein_contacts.select(args.cutoff, receptor)
                if contacts:
                    for contact in contacts:
                        contacts_ligand.add("{}.{}.{}".format(contact.getChid(), contact.getResname(), contact.getResnum()))

                # Calculate percentage of satisfied restraints
                perc = (len(contacts_receptor & restraints_receptor) + len(contacts_ligand & restraints_ligand)) / total
                percentages[(swarm_id, glowworm_id)] = perc
                if args.fnat:
                    if perc >= args.fnat:
                        shutil.copyfile(pdb, os.path.join(filtered_folder, 'swarm_{}_{}.pdb'.format(swarm_id, glowworm_id)))
                        try:
                            filter_passed[swarm_id].append(glowworm_id)
                        except:
                            filter_passed[swarm_id] = [glowworm_id]
                print("{:40s}  {:5.3f}".format(pdb, perc))

        except Exception, e:
            log.error('Filtering has failed for structure {}. Please see error:'.format(pdb))
            log.error(str(e))


    #print(filter_passed)
    filtered_ranking = os.path.join(filtered_folder, 'rank_filtered.list')
    with open(filtered_ranking, 'w') as handle:
        for rank in ranking:
            #print(rank)
            if rank.id_cluster in filter_passed and rank.id_glowworm in filter_passed[rank.id_cluster]:
                handle.write('swarm_{}_{}.pdb   {:5.3f}  {:5.3f}'.format(rank.id_cluster, 
                    rank.id_glowworm, rank.scoring, percentages[(rank.id_cluster, rank.id_glowworm)]) + os.linesep)
