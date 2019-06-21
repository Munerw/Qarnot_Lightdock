"""Implementation of the lgscore scoring function.

C-implementation of the lgscore scoring function and using the freesasa library:
https://github.com/mittinatten/freesasa
"""

import numpy as np
import freesasa
from freesasa import Structure
from lightdock.scoring.functions import ScoringFunction, ModelAdapter
from lightdock.structure.model import DockingModel
import lightdock.scoring.lgscore.energy.c.clgscore as clgscore
import lightdock.scoring.lgscore.energy.parameters as parameters
import lightdock.scoring.lgscore.data.amber as amber
import lightdock.scoring.lgscore.data.vdw as vdw
import lightdock.scoring.lgscore.data.solvation as solvation
from lightdock.util.logger import LoggingManager


log = LoggingManager.get_logger('lgscore')
freesasa.setVerbosity(freesasa.silent)


class LgScoreModel(DockingModel):
    """Prepares the structure necessary for the C-implementation of the lgscore scoring function"""
    def __init__(self, objects, coordinates, restraints, charges, 
                 vdw_energy, vdw_radii, des_energy, sasa, desolvation, hydrogens,
                 reference_points=None, n_modes=None):
        super(LgScoreModel, self).__init__(objects, coordinates, restraints, reference_points)
        self.charges = charges
        self.vdw_energy = vdw_energy
        self.vdw_radii = vdw_radii
        self.des_energy = des_energy
        self.sasa = sasa
        self.desolvation = desolvation
        self.hydrogens = hydrogens
        self.n_modes = n_modes

    def clone(self):
        """Creates a copy of the current model"""
        return LgScoreModel(self.objects, self.coordinates.copy(), self.restraints,
                            self.charges, self.vdw_energy, self.vdw_radii,
                            self.des_energy, self.sasa, self.desolvation, self.hydrogens,
                            reference_points=self.reference_points.copy())


class LgScoreAdapter(ModelAdapter):
    """Adapts a given Complex to a DockingModel object suitable for this
    scoring function.
    """
    def _get_docking_model(self, molecule, restraints):
        atoms = molecule.atoms
        parsed_restraints = {}
        # Assign properties to atoms
        for atom_index, atom in enumerate(atoms):
            res_id = "%s.%s.%s" % (atom.chain_id, atom.residue_name, str(atom.residue_number))
            if restraints and res_id in restraints:
                try:
                    parsed_restraints[res_id].append(atom_index)
                except:
                    parsed_restraints[res_id] = [atom_index]
            res_name = atom.residue_name
            atom_name = atom.name
            if res_name == "HIS":
                res_name = 'HID'
            if atom_name in amber.translate:
                atom_name = amber.translate[atom.name]
            atom_id = "%s-%s" % (res_name, atom_name)
            atom.amber_type = amber.amber_types[atom_id]
            atom.charge = amber.charges[atom_id]
            atom.mass = amber.masses[atom.amber_type]
            atom.vdw_energy = vdw.vdw_energy[atom.amber_type]
            atom.vdw_radius = vdw.vdw_radii[atom.amber_type]

        # Prepare common model information
        elec_charges = np.array([atom.charge for atom in atoms])
        vdw_energies = np.array([atom.vdw_energy for atom in atoms])
        vdw_radii = np.array([atom.vdw_radius for atom in atoms])
        coordinates = molecule.copy_coordinates()
        des_energy = solvation.get_solvation(molecule)

        # Calculate desolvation reference energy
        log.info('Calculating reference SASA...')
        structure = Structure()
        for i, atom in enumerate(atoms):
            if not atom.is_hydrogen():
                structure.addAtom(atom.name, atom.residue_name, atom.residue_number, atom.chain_id,
                                  atom.x, atom.y, atom.z)
        sasa_result = freesasa.calc(structure)
        sasa = []
        j = 0
        for i, atom in enumerate(atoms):
            if not atom.is_hydrogen():
                sasa.append(sasa_result.atomArea(j))
                j += 1
            else:
                sasa.append(-1.0)
        sasa = np.array(sasa)
        hydrogens = np.array([0 if atom.is_hydrogen() else 1 for atom in atoms])
        log.info('Done.')

        desolvation = np.sum(sasa * des_energy)

        reference_points = ModelAdapter.load_reference_points(molecule)
        try:
            return LgScoreModel(atoms, coordinates, parsed_restraints, elec_charges, vdw_energies, vdw_radii, des_energy,
                                sasa, desolvation, hydrogens, reference_points=reference_points, n_modes=molecule.n_modes.copy())
        except AttributeError:
            return LgScoreModel(atoms, coordinates, parsed_restraints, elec_charges, vdw_energies, vdw_radii, des_energy,
                                sasa, desolvation, hydrogens, reference_points=reference_points)


class LgScore(ScoringFunction):
    def __init__(self, weight=1.0):
        super(LgScore, self).__init__(weight)
        self.scoring_vdw_weight = parameters.scoring_vdw_weight

    def __call__(self, receptor, receptor_coordinates, ligand, ligand_coordinates):
        """Computes the lgscore scoring energy using receptor and ligand which are
        instances of DockingModel.
        """
        elec, vdw, solv, interface_receptor, interface_ligand = clgscore.calculate_energy(receptor_coordinates, ligand_coordinates,
                                                                              receptor.charges, ligand.charges,
                                                                              receptor.vdw_energy, ligand.vdw_energy,
                                                                              receptor.vdw_radii, ligand.vdw_radii,
                                                                              receptor.hydrogens, ligand.hydrogens,
                                                                              receptor.sasa, ligand.sasa,
                                                                              receptor.des_energy, ligand.des_energy, 
                                                                              3.9)
        solvation = solv - (receptor.desolvation + ligand.desolvation)
        energy = (elec + parameters.scoring_vdw_weight * vdw + solvation)*-1.
        perc_receptor_restraints = ScoringFunction.restraints_satisfied(receptor.restraints, set(interface_receptor))
        perc_ligand_restraints = ScoringFunction.restraints_satisfied(ligand.restraints, set(interface_ligand))
        return energy + perc_receptor_restraints * energy + perc_ligand_restraints * energy


# Needed to dynamically load the scoring functions from command line
DefinedScoringFunction = LgScore
DefinedModelAdapter = LgScoreAdapter
