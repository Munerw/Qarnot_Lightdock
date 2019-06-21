# -*- coding: utf-8 -*-
"""This module defines a pointer class for handling subsets of normal modes."""

from numpy import ndarray, array, arange, diag, dot

__all__ = ['ModeSet']

class ModeSet(object):

    """A class for providing access to subset of mode data.  Instances
    are obtained by slicing an NMA model (:class:`.ANM`, :class:`.GNM`, or
    :class:`.PCA`).  ModeSet's contain a reference to the model and a list
    of mode indices.  Methods common to NMA models are also defined for
    mode sets."""

    __slots__ = ['_model', '_indices']

    def __init__(self, model, indices):
        self._model = model
        self._indices = array(indices, int)

    def __len__(self):
        return len(self._indices)

    def __iter__(self):
        for i in self._indices:
            yield self._model[i]

    def __repr__(self):
        return '<ModeSet: {0} modes from {1}>'.format(len(self),
                                                       str(self._model))

    def __str__(self):
        return '{0} modes from {1}'.format(len(self._indices),
                                               str(self._model))
    
    def __getitem__(self, index):
        """A list or tuple of integers can be used for indexing."""

        if isinstance(index, slice):
            indices = arange(*index.indices(len(self)))
            if len(indices) > 1:
                return ModeSet(self._model, self._indices[indices])
            elif len(indices) > 0:
                return self._model._getMode(self._indices[indices[0]])
        elif isinstance(index, (list, tuple, ndarray)):
            if len(index) == 1:
                return self._model._getMode(self._indices[index[0]])
            return ModeSet(self._model, self._indices[index])
        try:
            index = int(index)
        except Exception:
            raise IndexError('indices must be int, slice, list, or tuple')
        else:
            return self._model._getMode(self._indices[index])

    def is3d(self):
        """Returns **True** is model is 3-dimensional."""

        return self._model._is3d

    def numAtoms(self):
        """Returns number of atoms."""

        return self._model.numAtoms()

    def numModes(self):
        """Returns number of modes in the instance (not necessarily maximum
        number of possible modes)."""

        return len(self._indices)

    def numDOF(self):
        """Returns number of degrees of freedom."""

        return self._model.numDOF()

    def getTitle(self):
        """Returns title of the mode set."""

        return str(self)

    def getModel(self):
        """Returns the model that the modes belongs to."""

        return self._model

    def getIndices(self):
        """Returns indices of modes in the mode set."""

        return self._indices

    def getEigvals(self):
        """Returns eigenvalues.  For :class:`.PCA` and :class:`.EDA` models
        built using coordinate data in Å, unit of eigenvalues is |A2|.  For
        :class:`.ANM` and :class:`.GNM`, on the other hand, eigenvalues are
        in arbitrary or relative units but they correlate with stiffness of
        the motion along associated eigenvector."""

        return self._model._eigvals[self._indices]

    def getVariances(self):
        """Returns variances.  For :class:`.PCA` and :class:`.EDA` models
        built using coordinate data in Å, unit of variance is |A2|.  For
        :class:`.ANM` and :class:`.GNM`, on the other hand, variance is the
        inverse of the eigenvalue, so it has arbitrary or relative units."""

        return self._model._vars[self._indices]

    def getCovariance(self):
        """Returns covariance matrix. It will be calculated using available modes."""

        V = self.getEigvecs()
        D = diag(self.getVariances())
        return dot(V, dot(D, V.T))

    def getArray(self):
        """Returns a copy of eigenvectors array."""

        return self._model.getArray()[:, self._indices].copy()

    getEigvecs = getArray

    def _getArray(self):
        """Returns eigenvectors array."""

        return self._model._getArray()[:, self._indices]

    def getHinges(self):
        """Returns residue index of hinge sites."""

        if self.is3d():
            return
        else:
            return self._model.getHinges(self._indices)

    def numHinges(self):
        return len(self.getHinges())
        