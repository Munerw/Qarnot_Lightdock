# -*- coding: utf-8 -*-
"""This module defines functions for calculating physical properties from normal
modes."""

import time

import numpy as np

from prody import LOGGER
from prody.proteins import parsePDB
from prody.atomic import AtomGroup
from prody.ensemble import Ensemble, Conformation
from prody.trajectory import TrajBase
from prody.utilities import importLA, checkCoords
from numpy import sqrt, arange, log, polyfit, array, arccos, dot

from .nma import NMA
from .modeset import ModeSet
from .mode import VectorBase, Mode, Vector
from .gnm import GNMBase
from .functions import calcENM

__all__ = ['calcCollectivity', 'calcCovariance', 'calcCrossCorr',
           'calcFractVariance', 'calcSqFlucts', 'calcTempFactors',
           'calcProjection', 'calcCrossProjection',
           'calcSpecDimension', 'calcPairDeformationDist',
           'calcDistFlucts']
           #'calcEntropyTransfer', 'calcOverallNetEntropyTransfer']

def calcCollectivity(mode, masses=None):
    """Returns collectivity of the mode.  This function implements collectivity
    as defined in equation 5 of [BR95]_.  If *masses* are provided, they will
    be incorporated in the calculation.  Otherwise, atoms are assumed to have
    uniform masses.

    .. [BR95] Bruschweiler R. Collective protein dynamics and nuclear
       spin relaxation. *J Chem Phys* **1995** 102:3396-3403.

    :arg mode: mode or vector
    :type mode: :class:`.Mode` or :class:`.Vector`

    :arg masses: atomic masses
    :type masses: :class:`numpy.ndarray`"""

    if not isinstance(mode, (Mode, ModeSet)):
        raise TypeError('mode must be a Mode or ModeSet instance')
    if isinstance(mode, Mode):
        mode = [mode]
    
    colls = []

    def log0(a):
        return log(a + np.finfo(float).eps)

    for m in mode:
        is3d = m.is3d()
        if masses is not None:
            if len(masses) != m.numAtoms():
                raise ValueError('length of masses must be equal to number of atoms')
            if is3d:
                u2in = (m.getArrayNx3() ** 2).sum(1) / masses
        else:
            if is3d:
                u2in = (m.getArrayNx3() ** 2).sum(1)
            else:
                u2in = (m.getArrayNx3() ** 2)
        u2in = u2in * (1 / u2in.sum() ** 0.5)
        coll = np.exp(-(u2in * log0(u2in)).sum()) / m.numAtoms()
        colls.append(coll)
    
    if len(mode) == 1:
        return coll
    else:
        return colls

def calcSpecDimension(mode):

    """
    :arg mode: mode or vector
    :type mode: :class:`.Mode` or :class:`.Vector`

    """
    # if not isinstance(mode, Mode):
    #     raise TypeError('mode must be a Mode instance')
    
    length = mode.shape[0]
    numbers = arange(2,length+1)
    ds,p=polyfit(log(sqrt(mode[0:int(length*0.25)])),log(numbers[0:int(length*0.25)]),1)
    
    return ds

def calcFracDimension(mode):
    """
    :arg mode: mode or vector
    :type mode: mode or vector """




def calcFractVariance(mode):
    """Returns fraction of variance explained by the *mode*.  Fraction of
    variance is the ratio of the variance along a mode to the trace of the
    covariance matrix of the model."""

    if isinstance(mode, Mode):
        var = mode.getVariance()
        trace = mode.getModel()._getTrace()
    elif isinstance(mode, (ModeSet, NMA)):
        var = mode.getVariances()
        if isinstance(mode, ModeSet):
            trace = mode.getModel()._getTrace()
        else:
            trace = mode._getTrace()
    else:
        raise TypeError('mode must be a Mode instance')
    if trace is None:
        raise ValueError('modes are not calculated')

    return var / trace


def calcProjection(ensemble, modes, rmsd=True, norm=True):
    """Returns projection of conformational deviations onto given modes.
    *ensemble* coordinates are used to calculate the deviations that are
    projected onto *modes*.  For K conformations and M modes, a (K,M)
    matrix is returned.

    :arg ensemble: an ensemble, trajectory or a conformation for which
        deviation(s) will be projected, or a deformation vector
    :type ensemble: :class:`.Ensemble`, :class:`.Conformation`,
        :class:`.Vector`, :class:`.Trajectory`
    :arg modes: up to three normal modes
    :type modes: :class:`.Mode`, :class:`.ModeSet`, :class:`.NMA`

    By default root-mean-square deviation (RMSD) along the normal mode is
    calculated. To calculate the projection pass ``rmsd=True``.
    :class:`.Vector` instances are accepted as *ensemble* argument to allow
    for projecting a deformation vector onto normal modes."""

    if not isinstance(ensemble, (Ensemble, Conformation, Vector, TrajBase)):
        raise TypeError('ensemble must be Ensemble, Conformation, Vector, '
                        'or a TrajBase, not {0}'.format(type(ensemble)))
    if not isinstance(modes, (NMA, ModeSet, VectorBase)):
        raise TypeError('rows must be NMA, ModeSet, or Mode, not {0}'
                        .format(type(modes)))
    if not modes.is3d():
        raise ValueError('modes must be 3-dimensional')
    if isinstance(ensemble, Vector):
        n_atoms = ensemble.numAtoms()
    else:
        n_atoms = ensemble.numSelected()
    if n_atoms != modes.numAtoms():
        raise ValueError('number of atoms are not the same')
    if isinstance(ensemble, Vector):
        if not ensemble.is3d():
            raise ValueError('ensemble must be a 3d vector instance')
        deviations = ensemble._getArray()
    elif isinstance(ensemble, (Ensemble, Conformation)):
        deviations = ensemble.getDeviations()
    else:
        nfi = ensemble.nextIndex()
        ensemble.goto(0)
        deviations = np.array([frame.getDeviations() for frame in ensemble])
        ensemble.goto(nfi)
    if deviations.ndim == 3:
        deviations = deviations.reshape((deviations.shape[0],
                                         deviations.shape[1] * 3))
    elif deviations.ndim == 2:
        deviations = deviations.reshape((1, deviations.shape[0] * 3))
    else:
        deviations = deviations.reshape((1, deviations.shape[0]))
    la = importLA()
    if norm:
        N = la.norm(deviations)
        if N != 0:
            deviations = deviations / N
    projection = np.dot(deviations, modes._getArray())
    if rmsd:
        projection = (1 / (n_atoms ** 0.5)) * projection
    return projection


def calcCrossProjection(ensemble, mode1, mode2, scale=None, **kwargs):
    """Returns projection of conformational deviations onto modes from
    different models.

    :arg ensemble: ensemble for which deviations will be projected
    :type ensemble: :class:`.Ensemble`
    :arg mode1: normal mode to project conformations onto
    :type mode1: :class:`.Mode`, :class:`.Vector`
    :arg mode2: normal mode to project conformations onto
    :type mode2: :class:`.Mode`, :class:`.Vector`
    :arg scale: scale width of the projection onto mode1 (``x``) or mode2(``y``),
        an optimized scaling factor (scalar) will be calculated by default 
        or a value of scalar can be passed."""

    if not isinstance(ensemble, (Ensemble, Conformation, Vector, TrajBase)):
        raise TypeError('ensemble must be Ensemble, Conformation, Vector, '
                        'or a Trajectory, not {0}'.format(type(ensemble)))
    if not isinstance(mode1, VectorBase):
        raise TypeError('mode1 must be a Mode instance, not {0}'
                        .format(type(mode1)))
    if not mode1.is3d():
        raise ValueError('mode1 must be 3-dimensional')
    if not isinstance(mode2, VectorBase):
        raise TypeError('mode2 must be a Mode instance, not {0}'
                        .format(type(mode2)))
    if not mode2.is3d():
        raise ValueError('mode2 must be 3-dimensional')

    if scale is not None:
        assert isinstance(scale, str), 'scale must be a string'
        scale = scale.lower()
        assert scale in ('x', 'y'), 'scale must be x or y'

    xcoords = calcProjection(ensemble, mode1, kwargs.get('rmsd', True), kwargs.get('norm', True))
    ycoords = calcProjection(ensemble, mode2, kwargs.pop('rmsd', True), kwargs.pop('norm', True))
    if scale:
        scalar = kwargs.get('scalar', None)
        if scalar:
            assert isinstance(scalar, (float, int)), 'scalar must be a number'
        else:
            scalar = ((ycoords.max() - ycoords.min()) /
                      (xcoords.max() - xcoords.min())
                      ) * np.sign(np.dot(xcoords, ycoords))
            if scale == 'x':
                LOGGER.info('Projection onto {0} is scaled by {1:.2f}'
                            .format(mode1, scalar))
            else:
                scalar = 1 / scalar
                LOGGER.info('Projection onto {0} is scaled by {1:.2f}'
                            .format(mode2, scalar))

        if scale == 'x':
            xcoords = xcoords * scalar
        else:
            ycoords = ycoords * scalar

    return xcoords, ycoords


def calcSqFlucts(modes):
    """Returns sum of square-fluctuations for given set of normal *modes*.
    Square fluctuations for a single mode is obtained by multiplying the
    square of the mode array with the variance (:meth:`.Mode.getVariance`)
    along the mode.  For :class:`.PCA` and :class:`.EDA` models built using
    coordinate data in Å, unit of square-fluctuations is |A2|, for
    :class:`.ANM` and :class:`.GNM`, on the other hand, it is arbitrary or
    relative units."""

    if not isinstance(modes, (VectorBase, NMA, ModeSet)):
        try:
            modes2 = []
            for mode in modes:
                if not isinstance(mode, Mode):
                    raise TypeError('modes can be a list of Mode instances, '
                                    'not {0}'.format(type(mode)))
                modes2.append(mode)
            mode = list(modes2)
        except TypeError:
            raise TypeError('modes must be a Mode, NMA, ModeSet instance, '
                            'or a list of Mode instances, not {0}'.format(type(modes)))
    if isinstance(modes, list):
        is3d = modes[0].is3d()
        n_atoms = modes[0].numAtoms()
    else:
        is3d = modes.is3d()
        n_atoms = modes.numAtoms()

    if isinstance(modes, Vector):
        if is3d:
            return (modes._getArrayNx3()**2).sum(axis=1)
        else:
            return (modes._getArray() ** 2)
    else:
        sq_flucts = np.zeros(n_atoms)
        if isinstance(modes, VectorBase):
            modes = [modes]
        for mode in modes:
            if is3d:
                sq_flucts += ((mode._getArrayNx3()**2).sum(axis=1) *
                              mode.getVariance())
            else:
                sq_flucts += (mode._getArray() ** 2) * mode.getVariance()
        return sq_flucts


def calcCrossCorr(modes, n_cpu=1, norm=True):
    """Returns cross-correlations matrix.  For a 3-d model, cross-correlations
    matrix is an NxN matrix, where N is the number of atoms.  Each element of
    this matrix is the trace of the submatrix corresponding to a pair of atoms.
    Covariance matrix may be calculated using all modes or a subset of modes
    of an NMA instance.  For large systems, calculation of cross-correlations
    matrix may be time consuming.  Optionally, multiple processors may be
    employed to perform calculations by passing ``n_cpu=2`` or more."""

    if not isinstance(n_cpu, int):
        raise TypeError('n_cpu must be an integer')
    elif n_cpu < 1:
        raise ValueError('n_cpu must be equal to or greater than 1')

    if not isinstance(modes, (Mode, NMA, ModeSet)):
        raise TypeError('modes must be a Mode, NMA, or ModeSet instance, '
                        'not {0}'.format(type(modes)))

    if modes.is3d():
        model = modes
        if isinstance(modes, (Mode, ModeSet)):
            model = modes._model
            if isinstance(modes, (Mode)):
                indices = [modes.getIndex()]
                n_modes = 1
            else:
                indices = modes.getIndices()
                n_modes = len(modes)
        else:
            n_modes = len(modes)
            indices = np.arange(n_modes)
        array = model._getArray()
        n_atoms = model._n_atoms
        variances = model._vars
        if n_cpu == 1:
            s = (n_modes, n_atoms, 3)
            arvar = (array[:, indices]*variances[indices]).T.reshape(s)
            array = array[:, indices].T.reshape(s)
            covariance = np.tensordot(array.transpose(2, 0, 1),
                                      arvar.transpose(0, 2, 1),
                                      axes=([0, 1], [1, 0]))
        else:
            import multiprocessing
            n_cpu = min(multiprocessing.cpu_count(), n_cpu)
            queue = multiprocessing.Queue()
            size = n_modes / n_cpu
            for i in range(n_cpu):
                if n_cpu - i == 1:
                    indices = modes.indices[i*size:]
                else:
                    indices = modes.indices[i*size:(i+1)*size]
                process = multiprocessing.Process(
                    target=_crossCorrelations,
                    args=(queue, n_atoms, array, variances, indices))
                process.start()
            while queue.qsize() < n_cpu:
                time.sleep(0.05)
            covariance = queue.get()
            while queue.qsize() > 0:
                covariance += queue.get()
    else:
        covariance = calcCovariance(modes)
    if norm:
        diag = np.power(covariance.diagonal(), 0.5)
        covariance /= np.outer(diag, diag)
    return covariance


def _crossCorrelations(queue, n_atoms, array, variances, indices):
    """Calculate covariance-matrix for a subset of modes."""

    n_modes = len(indices)
    arvar = (array[:, indices] * variances[indices]).T.reshape((n_modes,
                                                                n_atoms, 3))
    array = array[:, indices].T.reshape((n_modes, n_atoms, 3))
    covariance = np.tensordot(array.transpose(2, 0, 1),
                              arvar.transpose(0, 2, 1),
                              axes=([0, 1], [1, 0]))
    queue.put(covariance)

def calcDistFlucts(modes, n_cpu=1, norm=True):
    """Returns the matrix of distance fluctuations (i.e. an NxN matrix
    where N is the number of residues, of MSFs in the inter-residue distances)
    computed from the cross-correlation matrix (see Eq. 12.E.1 in [IB18]_). 
    The arguments are the same as in :meth:`.calcCrossCorr`.

    .. [IB18] Dill K, Jernigan RL, Bahar I. Protein Actions: Principles and
       Modeling. *Garland Science* **2017**. """

    cc = calcCrossCorr(modes, n_cpu=n_cpu, norm=norm)
    cc_diag = np.diag(cc).reshape(-1,1)
    distFluct = cc_diag.T + cc_diag -2.*cc
    return distFluct

def calcTempFactors(modes, atoms):
    """Returns temperature (β) factors calculated using *modes* from a
    :class:`.ANM` or :class:`.GNM` instance scaled according to the 
    experimental B-factors from *atoms*."""

    model = modes.getModel()
    if not isinstance(model, GNMBase):
        raise TypeError('modes must come from GNM or ANM')
    if model.numAtoms() != atoms.numAtoms():
        raise ValueError('modes and atoms must have same number of nodes')
    sqf = calcSqFlucts(modes)
    return sqf / ((sqf**2).sum()**0.5) * (atoms.getBetas()**2).sum()**0.5


def calcCovariance(modes):
    """Returns covariance matrix calculated for given *modes*."""

    if isinstance(modes, Mode):
        array = modes._getArray()
        return np.outer(array, array) * modes.getVariance()
    elif isinstance(modes, ModeSet):
        array = modes._getArray()
        return np.dot(array, np.dot(np.diag(modes.getVariances()), array.T))
    elif isinstance(modes, NMA):
        return modes.getCovariance()
    else:
        raise TypeError('modes must be a Mode, NMA, or ModeSet instance')


def calcPairDeformationDist(model, coords, ind1, ind2, kbt=1.):
                                                
    """Returns distribution of the deformations in the distance contributed by each mode 
    for selected pair of residues *ind1* *ind2* using *model* from a :class:`.ANM`.
    Method described in [EB08]_ equation (10) and figure (2).     
    
    .. [EB08] Eyal E., Bahar I. Toward a Molecular Understanding of 
        the Anisotropic Response of Proteins to External Forces:
        Insights from Elastic Network Models. *Biophys J* **2008** 94:3424-34355. 
    
    :arg model: this is an 3-dimensional :class:`NMA` instance from a :class:`.ANM`
        calculations.
    :type model: :class:`.ANM`  

    :arg coords: a coordinate set or an object with :meth:`getCoords` method.
        Recommended: ``coords = parsePDB('pdbfile').select('protein and name CA')``.
    :type coords: :class:`~numpy.ndarray`.

    :arg ind1: first residue number.
    :type ind1: int 
    
    :arg ind2: secound residue number.
    :type ind2: int 
    """

    try:
        resnum_list = coords.getResnums()
        resnam_list = coords.getResnames()
        coords = (coords._getCoords() if hasattr(coords, '_getCoords') else
                coords.getCoords())
    except AttributeError:
        try:
            checkCoords(coords)
        except TypeError:
            raise TypeError('coords must be a Numpy array or an object '
                            'with `getCoords` method')
    
    if not isinstance(model, NMA):
        raise TypeError('model must be a NMA instance')
    elif not model.is3d():
        raise TypeError('model must be a 3-dimensional NMA instance')
    elif len(model) == 0:
        raise ValueError('model must have normal modes calculated')
    
    linalg = importLA()
    n_atoms = model.numAtoms()
    n_modes = model.numModes()
    LOGGER.timeit('_pairdef')

    r_ij = np.zeros((n_atoms,n_atoms,3))
    r_ij_norm = np.zeros((n_atoms,n_atoms,3))

    for i in range(n_atoms):
        for j in range(i+1,n_atoms):
            r_ij[i][j] = coords[j,:] - coords[i,:]
            r_ij[j][i] = r_ij[i][j]
            r_ij_norm[i][j] = r_ij[i][j]/linalg.norm(r_ij[i][j])
            r_ij_norm[j][i] = r_ij_norm[i][j]

    eigvecs = model.getEigvecs()
    eigvals = model.getEigvals()
    
    D_pair_k = []
    mode_nr = []
    ind1 = ind1 - resnum_list[0]
    ind2 = ind2 - resnum_list[0]

    for m in range(6,n_modes):
        U_ij_k = [(eigvecs[ind1*3][m] - eigvecs[ind2*3][m]), (eigvecs[ind1*3+1][m] \
            - eigvecs[ind2*3+1][m]), (eigvecs[ind1*3+2][m] - eigvecs[ind2*3+2][m])] 
        D_ij_k = abs(sqrt(kbt/eigvals[m])*(np.vdot(r_ij_norm[ind1][ind2], U_ij_k)))  
        D_pair_k.append(D_ij_k)
        mode_nr.append(m)

    LOGGER.report('Deformation was calculated in %.2lfs.', label='_pairdef')
    
    return mode_nr, D_pair_k
