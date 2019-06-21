# -*- coding: utf-8 -*-
"""This module defines input and output functions."""

import os
from os.path import abspath, join, isfile, isdir, split, splitext

import numpy as np

from prody import LOGGER, SETTINGS, PY3K
from prody.atomic import Atomic, AtomGroup, AtomSubset
from prody.utilities import openFile, isExecutable, which, PLATFORM, addext

from .nma import NMA
from .anm import ANM
from .gnm import GNM, GNMBase, ZERO, MaskedGNM
from .pca import PCA, EDA
from .exanm import exANM
from .mode import Vector, Mode
from .modeset import ModeSet
from .editing import sliceModel, reduceModel

__all__ = ['parseArray', 'parseModes', 'parseSparseMatrix',
           'writeArray', 'writeModes',
           'saveModel', 'loadModel', 'saveVector', 'loadVector',
           'calcENM']


def saveModel(nma, filename=None, matrices=False, **kwargs):
    """Save *nma* model data as :file:`filename.nma.npz`.  By default,
    eigenvalues, eigenvectors, variances, trace of covariance matrix,
    and name of the model will be saved.  If *matrices* is **True**,
    covariance, Hessian or Kirchhoff matrices are saved too, whichever
    are available.  If *filename* is **None**, name of the NMA instance
    will be used as the filename, after ``" "`` (white spaces) in the name
    are replaced with ``"_"`` (underscores).  Extension may differ based
    on the type of the NMA model.  For ANM models, it is :file:`.anm.npz`.
    Upon successful completion of saving, filename is returned. This
    function makes use of :func:`~numpy.savez` function."""

    if not isinstance(nma, NMA):
        raise TypeError('invalid type for nma, {0}'.format(type(nma)))
    if len(nma) == 0:
        raise ValueError('nma instance does not contain data')

    dict_ = nma.__dict__
    attr_list = ['_title', '_trace', '_array', '_eigvals', '_vars', '_n_atoms',
                 '_dof', '_n_modes']
    if filename is None:
        filename = nma.getTitle().replace(' ', '_')
    if isinstance(nma, GNMBase):
        attr_list.append('_cutoff')
        attr_list.append('_gamma')
        if matrices:
            attr_list.append('_kirchhoff')
            if isinstance(nma, ANM):
                attr_list.append('_hessian')
        if isinstance(nma, ANM):
            type_ = 'ANM'
        else:
            type_ = 'GNM'
    elif isinstance(nma, EDA):
        type_ = 'EDA'
    elif isinstance(nma, PCA):
        type_ = 'PCA'
    else:
        type_ = 'NMA'

    if matrices:
        attr_list.append('_cov')
    attr_dict = {'type': type_}
    for attr in attr_list:
        value = dict_[attr]
        if value is not None:
            attr_dict[attr] = value

    if isinstance(nma, MaskedGNM):
        attr_dict['type'] = 'mGNM'
        attr_dict['mask'] = nma.mask
        attr_dict['masked'] = nma.masked

    if isinstance(nma, exANM):
        attr_dict['type'] = 'exANM'
        attr_dict['_membrane'] = np.array([nma._membrane, None])
        attr_dict['_combined'] = np.array([nma._combined, None])

    suffix = '.' + attr_dict['type'].lower()
    if not filename.lower().endswith('.npz'):
        if not filename.lower().endswith(suffix):
            filename += suffix + '.npz'
        else:
            filename += '.npz'
    ostream = openFile(filename, 'wb', **kwargs)
    np.savez(ostream, **attr_dict)
    ostream.close()
    return filename


def loadModel(filename, **kwargs):
    """Returns NMA instance after loading it from file (*filename*).
    This function makes use of :func:`~numpy.load` function.  See
    also :func:`saveModel`."""

    if not 'encoding' in kwargs:
        kwargs['encoding'] = 'latin1'

    attr_dict = np.load(filename, **kwargs)
    try:
        type_ = attr_dict['type']
    except KeyError:
        raise IOError('{0} is not a valid NMA model file'.format(filename))

    if isinstance(type_, np.ndarray):
        type_ = np.asarray(type_, dtype=str)

    type_ = str(type_)

    try:
        title = attr_dict['_title']
    except KeyError:
        title = attr_dict['_name']

    if isinstance(title, np.ndarray):
        title = np.asarray(title, dtype=str)
    title = str(title)
    if type_ == 'ANM':
        nma = ANM(title)
    elif type_ == 'PCA':
        nma = PCA(title)
    elif type_ == 'EDA':
        nma = EDA(title)
    elif type_ == 'GNM':
        nma = GNM(title)
    elif type_ == 'mGNM':
        nma = MaskedGNM(title)
    elif type_ == 'exANM':
        nma = exANM(title)
    elif type_ == 'NMA':
        nma = NMA(title)
    else:
        raise IOError('NMA model type is not recognized: {0}'.format(type_))

    dict_ = nma.__dict__
    for attr in attr_dict.files:
        if attr in ('type', '_name', '_title'):
            continue
        elif attr in ('_trace', '_cutoff', '_gamma'):
            dict_[attr] = float(attr_dict[attr])
        elif attr in ('_dof', '_n_atoms', '_n_modes'):
            dict_[attr] = int(attr_dict[attr])
        elif attr in ('_membrane', '_combined'):
            dict_[attr] = attr_dict[attr][0] 
        else:
            dict_[attr] = attr_dict[attr]
    return nma


def saveVector(vector, filename, **kwargs):
    """Save *vector* data as :file:`filename.vec.npz`.  Upon successful
    completion of saving, filename is returned.  This function makes use
    of :func:`numpy.savez` function."""

    if not isinstance(vector, Vector):
        raise TypeError('invalid type for vector, {0}'.format(type(vector)))
    attr_dict = {}
    attr_dict['title'] = vector.getTitle()
    attr_dict['array'] = vector._getArray()
    attr_dict['is3d'] = vector.is3d()
    filename += '.vec.npz'
    ostream = openFile(filename, 'wb', **kwargs)
    np.savez(ostream, **attr_dict)
    ostream.close()
    return filename


def loadVector(filename):
    """Returns :class:`.Vector` instance after loading it from *filename* using
    :func:`numpy.load`.  See also :func:`saveVector`."""

    attr_dict = np.load(filename)
    try:
        title = str(attr_dict['title'])
    except KeyError:
        title = str(attr_dict['name'])
    return Vector(attr_dict['array'], title, bool(attr_dict['is3d']))


def writeModes(filename, modes, format='%.18e', delimiter=' '):
    """Write *modes* (eigenvectors) into a plain text file with name
    *filename*. See also :func:`writeArray`."""

    if not isinstance(modes, (NMA, ModeSet, Mode)):
        raise TypeError('modes must be NMA, ModeSet, or Mode, not {0}'
                        .format(type(modes)))
    return writeArray(filename, modes._getArray(), format=format,
                      delimiter=delimiter)


def parseModes(normalmodes, eigenvalues=None, nm_delimiter=None,
               nm_skiprows=0, nm_usecols=None, ev_delimiter=None,
               ev_skiprows=0, ev_usecols=None, ev_usevalues=None):
    """Returns :class:`.NMA` instance with normal modes parsed from
    *normalmodes*.

    In normal mode file *normalmodes*, columns must correspond to modes
    (eigenvectors).  Optionally, *eigenvalues* can be parsed from a separate
    file. If eigenvalues are not provided, they will all be set to 1.

    :arg normalmodes: File or filename that contains normal modes.
        If the filename extension is :file:`.gz` or :file:`.bz2`, the file is
        first decompressed.
    :type normalmodes: str or file

    :arg eigenvalues: Optional, file or filename that contains eigenvalues.
        If the filename extension is :file:`.gz` or :file:`.bz2`,
        the file is first decompressed.
    :type eigenvalues: str or file

    :arg nm_delimiter: The string used to separate values in *normalmodes*.
        By default, this is any whitespace.
    :type nm_delimiter: str

    :arg nm_skiprows: Skip the first *skiprows* lines in *normalmodes*.
        Default is ``0``.
    :type nm_skiprows: 0

    :arg nm_usecols: Which columns to read from *normalmodes*, with 0 being the
        first. For example, ``usecols = (1,4,5)`` will extract the 2nd, 5th and
        6th columns. The default, **None**, results in all columns being read.
    :type nm_usecols: list

    :arg ev_delimiter: The string used to separate values in *eigenvalues*.
        By default, this is any whitespace.
    :type ev_delimiter: str

    :arg ev_skiprows: Skip the first *skiprows* lines in *eigenvalues*.
        Default is ``0``.
    :type ev_skiprows: 0

    :arg ev_usecols: Which columns to read from *eigenvalues*, with 0 being the
        first. For example, ``usecols = (1,4,5)`` will extract the 2nd, 5th and
        6th columns. The default, **None**, results in all columns being read.
    :type ev_usecols: list

    :arg ev_usevalues: Which columns to use after the eigenvalue column is
        parsed from *eigenvalues*, with 0 being the first.
        This can be used if *eigenvalues* contains more values than the
        number of modes in *normalmodes*.
    :type ev_usevalues: list

    See :func:`parseArray` for details of parsing arrays from files."""

    modes = parseArray(normalmodes, delimiter=nm_delimiter,
                       skiprows=nm_skiprows, usecols=nm_usecols)
    if eigenvalues is not None:
        values = parseArray(eigenvalues, delimiter=ev_delimiter,
                            skiprows=ev_skiprows, usecols=ev_usecols)
        values = values.flatten()
        if ev_usevalues is not None:
            values = values[ev_usevalues]
    nma = NMA(splitext(split(normalmodes)[1])[0])
    nma.setEigens(modes, values)
    return nma


def writeArray(filename, array, format='%3.2f', delimiter=' '):
    """Write 1-d or 2-d array data into a delimited text file.

    This function is using :func:`numpy.savetxt` to write the file, after
    making some type and value checks.  Default *format* argument is ``"%d"``.
    Default *delimiter* argument is white space, ``" "``.

    *filename* will be returned upon successful writing."""

    if not isinstance(array, np.ndarray):
        raise TypeError('array must be a Numpy ndarray, not {0}'
                        .format(type(array)))
    elif not array.ndim in (1, 2):
        raise ValueError('array must be a 1 or 2-dimensional Numpy ndarray, '
                         'not {0}-d'.format(type(array.ndim)))
    np.savetxt(filename, array, format, delimiter)
    return filename

def parseArray(filename, delimiter=None, skiprows=0, usecols=None,
               dtype=float):
    """Parse array data from a file.

    This function is using :func:`numpy.loadtxt` to parse the file.  Each row
    in the text file must have the same number of values.

    :arg filename: File or filename to read. If the filename extension is
        :file:`.gz` or :file:`.bz2`, the file is first decompressed.
    :type filename: str or file

    :arg delimiter: The string used to separate values. By default,
        this is any whitespace.
    :type delimiter: str

    :arg skiprows: Skip the first *skiprows* lines, default is ``0``.
    :type skiprows: int

    :arg usecols: Which columns to read, with 0 being the first. For example,
        ``usecols = (1,4,5)`` will extract the 2nd, 5th and 6th columns.
        The default, **None**, results in all columns being read.
    :type usecols: list

    :arg dtype: Data-type of the resulting array, default is :func:`float`.
    :type dtype: :class:`numpy.dtype`."""

    array = np.loadtxt(filename, dtype=dtype, delimiter=delimiter,
                       skiprows=skiprows, usecols=usecols)
    return array

def parseSparseMatrix(filename, symmetric=False, delimiter=None, skiprows=0,
                      irow=0, icol=1, first=1):
    """Parse sparse matrix data from a file.

    This function is using :func:`parseArray` to parse the file.
    Input must have the following format::

       1       1    9.958948135375977e+00
       1       2   -3.788214445114136e+00
       1       3    6.236155629158020e-01
       1       4   -7.820609807968140e-01

    Each row in the text file must have the same number of values.

    :arg filename: File or filename to read. If the filename extension is
        :file:`.gz` or :file:`.bz2`, the file is first decompressed.
    :type filename: str or file

    :arg symmetric: Set **True** if the file contains triangular part of a
        symmetric matrix, default is **True**.
    :type symmetric: bool

    :arg delimiter: The string used to separate values. By default,
        this is any whitespace.
    :type delimiter: str

    :arg skiprows: Skip the first *skiprows* lines, default is ``0``.
    :type skiprows: int

    :arg irow: Index of the column in data file corresponding to row indices,
        default is ``0``.
    :type irow: int

    :arg icol: Index of the column in data file corresponding to row indices,
        default is ``0``.
    :type icol: int

    :arg first: First index in the data file (0 or 1), default is ``1``.
    :type first: int

    Data-type of the resulting array, default is :func:`float`."""

    irow = int(irow)
    icol = int(icol)
    first = int(first)
    assert 0 <= irow <= 2 and 0 <= icol <= 2, 'irow/icol may be 0, 1, or 2'
    assert icol != irow, 'irow and icol must not be equal'
    idata = [0, 1, 2]
    idata.pop(idata.index(irow))
    idata.pop(idata.index(icol))
    idata = idata[0]
    sparse = parseArray(filename, delimiter, skiprows)
    if symmetric:
        dim1 = dim2 = int(sparse[:, [irow, icol]].max())
    else:
        dim1, dim2 = sparse[:, [irow, icol]].max(0).astype(int)
    matrix = np.zeros((dim1, dim2))
    irow = (sparse[:, irow] - first).astype(int)
    icol = (sparse[:, icol] - first).astype(int)
    matrix[irow, icol] = sparse[:, idata]
    if symmetric:
        matrix[icol, irow] = sparse[:, idata]
    return matrix

def calcENM(atoms, select=None, model='anm', trim='trim', gamma=1.0, 
            title=None, n_modes=None, **kwargs):
    """Returns an :class:`ANM` or `GNM` instance and atoms used for the 
    calculationsn. The model can be trimmed, sliced, or reduced based on 
    the selection.

    :arg atoms: atoms on which the ENM is performed. It can be any :class:`Atomic` 
        class that supports selection.
    :type atoms: :class:`Atomic`, :class:`AtomGroup`, :class:`Selection`

    :arg select: part of the atoms that is considered as the system. 
        If set to `None`, then all atoms will be considered as the system
    :type select: str, :class:`Selection`

    :arg model: type of ENM that will be performed. It can be either 'anm' 
        or 'gnm'
    :type model: str

    :arg trim: type of method that will be used to trim the model. It can 
        be either 'trim' , 'slice', or 'reduce'. If set to 'trim', the parts 
        that is not in the selection will simply be removed
    :type trim: str
    """
    
    if not isinstance(atoms, Atomic):
        if select is not None:
            raise TypeError('atoms should be Atomic if it needs to be selected')
    try:
        if title is None:
            title = atoms.getTitle()
    except AttributeError:
        title = 'Unknown'

    zeros = kwargs.pop('zeros', False)
    turbo = kwargs.pop('turbo', True)

    if model is GNM:
        model = 'gnm'
    elif model is ANM:
        model = 'anm'
    else:
        model = str(model).lower().strip() 

    if trim is reduceModel:
        trim = 'reduce'
    elif trim is sliceModel:
        trim = 'slice'
    elif trim is None:
        trim = 'trim'
    else:
        trim = str(trim).lower().strip()

    if trim == 'trim' and select is not None:
        if isinstance(select, AtomSubset):
            atoms = select
        else:
            atoms = atoms.select(str(select))
    
    enm = None
    if model == 'anm':
        anm = ANM(title)
        anm.buildHessian(atoms, gamma=gamma, **kwargs)
        enm = anm
    elif model == 'gnm':
        gnm = GNM(title)
        gnm.buildKirchhoff(atoms, gamma=gamma, **kwargs)
        enm = gnm
    else:
        raise TypeError('model should be either ANM or GNM instead of {0}'.format(model))
    
    if select is None:
        enm.calcModes(n_modes=n_modes, zeros=zeros, turbo=turbo)
    else:
        if trim == 'slice':
            enm.calcModes(n_modes=n_modes, zeros=zeros, turbo=turbo)
            enm, atoms = sliceModel(enm, atoms, select)  
            if model == 'gnm':
                enm.calcHinges()
        elif trim == 'reduce':
            enm, atoms = reduceModel(enm, atoms, select)
            enm.calcModes(n_modes=n_modes, zeros=zeros, turbo=turbo)
        else:
            enm.calcModes(n_modes=n_modes, zeros=zeros, turbo=turbo)
    
    return enm, atoms
