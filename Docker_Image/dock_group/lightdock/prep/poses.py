"""Module to prepare initial poses for docking"""

import os
import operator
import numpy as np
from lightdock.pdbutil.PDBIO import create_pdb_from_points
from lightdock.prep.starting_points import calculate_surface_points
from lightdock.prep.ftdock import FTDockCoordinatesParser, classify_ftdock_poses
from lightdock.mathutil.lrandom import MTGenerator, NormalGenerator
from lightdock.mathutil.cython.quaternion import Quaternion
from lightdock.mathutil.cython.cutil import distance as cdistance
from lightdock.constants import CLUSTERS_CENTERS_FILE,\
    DEFAULT_PDB_STARTING_PREFIX, DEFAULT_STARTING_PREFIX, DEFAULT_BILD_STARTING_PREFIX, DEFAULT_EXTENT_MU, \
    DEFAULT_EXTENT_SIGMA
from lightdock.prep.geometry import create_bild_file


def get_random_point_within_sphere(number_generator, radius):
    """Generates a random point within a sphere of given radius"""
    r2 = radius**2
    while True:
        x = (2 * number_generator() - 1) * radius
        y = (2 * number_generator() - 1) * radius
        z = (2 * number_generator() - 1) * radius
        if x**2 + y**2 + z**2 <= r2:
            return x, y, z


def normalize_vector(v):
    norm = np.linalg.norm(v)
    if norm < 0.00001: 
       return v
    return v / norm


def orthogonal(v):
    """Returns the orthogonal vector to v"""
    x = abs(v[0])
    y = abs(v[1])
    z = abs(v[2])
    if x < y:
        if x < z:
            other = np.array([1.0, 0.0, 0.0])
        else:
            other = np.array([0.0, 0.0, 1.0])
    else:
        if y < z:
            other = np.array([0.0, 1.0, 0.0])
        else:
            other = np.array([0.0, 0.0, 1.0])
    return np.cross(v, other)


def quaternion_from_vectors(a, b):
    """Calculate quaternion between two vectors a and b."""
    a = normalize_vector(a)
    b = normalize_vector(b)
    # Check for scenario where vectors are in the same direction
    if np.allclose(a, -b):
        o = orthogonal(a)
        return Quaternion(w=0., x=o[0], y=o[1], z=o[2])
    c = np.cross(a, b)
    d = np.dot(a, b)
    s = np.sqrt( (1+abs(d))*2 )
    invs = 1. / s
    x = c[0] * invs
    y = c[1] * invs
    z = c[2] * invs
    w = s * 0.5

    return Quaternion(w=w, x=x, y=y, z=z).normalize()


def get_quaternion_for_restraint(rec_residue, lig_residue, tx, ty, tz, rt, lt):
    """Calculates the quaternion required for orienting the ligand towards the restraint"""
    r_ca = rec_residue.get_calpha()
    l_ca = lig_residue.get_calpha()

    rx = r_ca.x + rt[0]
    ry = r_ca.y + rt[1]
    rz = r_ca.z + rt[2]

    lx = l_ca.x + lt[0]
    ly = l_ca.y + lt[1]
    lz = l_ca.z + lt[2]

    # Define restraints vectors
    a = np.array([lx, ly, lz])
    b = np.array([rx - tx, ry - ty, rz - tz])
    
    q = quaternion_from_vectors(a, b)

    return q


def populate_poses(to_generate, center, radius, number_generator, rec_translation, lig_translation,
                    rng_nm=None, rec_nm=0, lig_nm=0, receptor_restraints=None, ligand_restraints=None):
    """Creates new poses around a given center and a given radius"""
    new_poses = []

    # Calculate closer residue restraints
    closest_residues = []
    if receptor_restraints:
        distances = []
        for i, residue in enumerate(receptor_restraints):
            ca = residue.get_calpha()
            distances.append((i, cdistance(ca.x , ca.y , ca.z ,
                                            center[0], center[1], center[2])))
        distances.sort(key=lambda tup: tup[1])
        closest_residues = [x[0] for x in distances[:10]]

    for _ in xrange(to_generate):
        x, y, z = get_random_point_within_sphere(number_generator, radius)
        tx = center[0] + x
        ty = center[1] + y
        tz = center[2] + z
        if receptor_restraints and ligand_restraints:
            rec_residue = receptor_restraints[closest_residues[number_generator.randint(0, len(closest_residues)-1)]]
            lig_residue = ligand_restraints[number_generator.randint(0, len(ligand_restraints)-1)]
            q = get_quaternion_for_restraint(rec_residue, lig_residue, tx, ty, tz,
                                             rec_translation, lig_translation)
        else:
            q = Quaternion.random(number_generator)
        op_vector = [tx, ty, tz, q.w, q.x, q.y, q.z]
        if rng_nm:
            if rec_nm > 0:
                op_vector.extend([rng_nm() for _ in xrange(rec_nm)])
            if lig_nm > 0:
                op_vector.extend([rng_nm() for _ in xrange(lig_nm)])
        new_poses.append(op_vector)
    return new_poses


def create_file_from_poses(pos_file_name, poses):
    """Writes to file the initial poses"""
    positions_file = open(pos_file_name, 'w')
    for pose in poses:
        position = ' '.join(["{:.9f}".format(coord) for coord in pose])
        positions_file.write(position + os.linesep)
    positions_file.close()


def apply_restraints(swarm_centers, receptor_restraints, distance_cutoff, translation, 
                     is_membrane=False, swarms_per_restraint=10):
    
    closer_swarms = []
    for i, residue in enumerate(receptor_restraints):
        distances = {}
        ca = residue.get_calpha()
        for swarm_id, center in enumerate(swarm_centers):
            distances[swarm_id] = cdistance(ca.x + translation[0], ca.y + translation[1], ca.z + translation[2],
                                            center[0], center[1], center[2])
        sorted_distances = sorted(distances.items(), key=operator.itemgetter(1))
        swarms_considered = 0
        for swarm in sorted_distances:
            swarm_id, distance = swarm[0], swarm[1]
            if distance <= distance_cutoff:
                closer_swarms.append(swarm_id)
                swarms_considered += 1
            if swarms_considered == swarms_per_restraint:
                break
    closer_swarms = list(set(closer_swarms))
    if is_membrane:
        # Requieres the receptor to be aligned in the Z axis with the membrane
        min_z = min([residue.get_calpha().z for residue in receptor_restraints]) + translation[2]
        compatible = []
        for swarm_id, center in enumerate(swarm_centers):
            if swarm_id in closer_swarms:
                if center[2] >= min_z:
                    compatible.append(swarm_id)
        return compatible
    else:
        return closer_swarms


def calculate_initial_poses(receptor, ligand, num_clusters, num_glowworms,
                            seed, receptor_restraints, ligand_restraints, 
                            rec_translation, lig_translation,
                            dest_folder, ftdock_file='', nm_mode=False, nm_seed=0, rec_nm=0, lig_nm=0,
                            is_membrane=False):
    """Calculates the starting points for each of the glowworms using the center of swarms
    and FTDock poses.
    """
    # Random number generator for poses
    rng = MTGenerator(seed)

    # Random number generator for NM
    if nm_mode:
        rng_nm = NormalGenerator(nm_seed, mu=DEFAULT_EXTENT_MU, sigma=DEFAULT_EXTENT_SIGMA)
    else:
        rng_nm = None
    
    # Calculate swarm centers
    swarm_centers, receptor_diameter, ligand_diameter = calculate_surface_points(receptor, 
                                                                                   ligand, 
                                                                                   num_clusters,
                                                                                   distance_step=1.0)
    # Filter cluster centers far from the restraints
    if receptor_restraints:
        filtered_swarms = apply_restraints(swarm_centers, receptor_restraints, ligand_diameter / 2., 
                                           rec_translation, is_membrane=is_membrane)
        swarm_centers = [swarm_centers[i] for i in filtered_swarms]

    pdb_file_name = os.path.join(dest_folder, CLUSTERS_CENTERS_FILE)
    create_pdb_from_points(pdb_file_name, swarm_centers)

    ligand_center = ligand.center_of_coordinates()
    radius = 10.    # ligand_diameter / 2.
    positions_files = []

    # Populate the clusters using the FTDock poses
    if ftdock_file:
        if nm_mode:
            raise NotImplementedError('Using FTDock poses with NM is not supported')

        poses = FTDockCoordinatesParser.get_list_of_poses(ftdock_file, ligand_center)
        clusters = classify_ftdock_poses(poses, swarm_centers, radius)

        for cluster_id, ftdock_poses in clusters.iteritems():
            # Translate FTDock poses into lightdock poses
            poses = []
            for pose in ftdock_poses:
                poses.append([pose.translation[0],
                              pose.translation[1],
                              pose.translation[2],
                              pose.q.w,
                              pose.q.x,
                              pose.q.y,
                              pose.q.z])

            # Populate new poses if needed
            if len(poses) < num_glowworms:
                needed = num_glowworms - len(poses)
                poses.extend(populate_poses(needed, swarm_centers[cluster_id], radius, rng, rec_translation, lig_translation))

            # Save poses as pdb file
            pdb_file_name = os.path.join(dest_folder, '%s_%s.pdb' % (DEFAULT_PDB_STARTING_PREFIX, cluster_id))
            create_pdb_from_points(pdb_file_name, [[pose[0], pose[1], pose[2]] for pose in poses[:num_glowworms]])

            # Save poses as initial_positions file
            pos_file_name = os.path.join(dest_folder, '%s_%s.dat' % (DEFAULT_STARTING_PREFIX, cluster_id))
            bild_file_name = os.path.join(dest_folder, '%s_%s.bild' % (DEFAULT_BILD_STARTING_PREFIX, cluster_id))
            create_file_from_poses(pos_file_name, poses[:num_glowworms])
            positions_files.append(pos_file_name)
            create_bild_file(bild_file_name, poses)
    else:
        for cluster_id, cluster_center in enumerate(swarm_centers):
            poses = populate_poses(num_glowworms, cluster_center, radius, rng, rec_translation, lig_translation,
                                    rng_nm, rec_nm, lig_nm, receptor_restraints, ligand_restraints)
            # Save poses as pdb file
            pdb_file_name = os.path.join(dest_folder, '%s_%s.pdb' % (DEFAULT_PDB_STARTING_PREFIX, cluster_id))
            create_pdb_from_points(pdb_file_name, [[pose[0], pose[1], pose[2]] for pose in poses[:num_glowworms]])

            # Save poses as initial_positions file
            pos_file_name = os.path.join(dest_folder, '%s_%s.dat' % (DEFAULT_STARTING_PREFIX, cluster_id))
            bild_file_name = os.path.join(dest_folder, '%s_%s.bild' % (DEFAULT_BILD_STARTING_PREFIX, cluster_id))
            create_file_from_poses(pos_file_name, poses[:num_glowworms])
            positions_files.append(pos_file_name)
            create_bild_file(bild_file_name, poses)

    return positions_files
