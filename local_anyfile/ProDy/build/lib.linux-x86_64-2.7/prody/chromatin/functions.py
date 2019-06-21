import numpy as np

from prody.dynamics import NMA
from prody.dynamics.mode import Mode
from prody.dynamics.modeset import ModeSet
from prody.utilities import importLA
from prody import LOGGER, SETTINGS
from prody.utilities import showFigure

__all__ = ['showMap', 'showDomains', 'showEmbedding', 'getDomainList']

## normalization methods ##
def div0(a, b):
    """ Performs ``true_divide`` but ignores the error when division by zero 
    (result is set to zero instead). """

    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide(a, b)
        if np.isscalar(c):
            if not np.isfinite(c):
                c = 0
        else:
            c[~np.isfinite(c)] = 0.  # -inf inf NaN
    return c

def showMap(map, spec='', **kwargs):
    """A convenient function that can be used to visualize Hi-C contact map. 
    *kwargs* will be passed to :func:`matplotlib.pyplot.imshow`.

    :arg map: a Hi-C contact map.
    :type map: :class:`numpy.ndarray`

    :arg spec: a string specifies how to preprocess the matrix. Blank for no preprocessing,
    'p' for showing only data from *p*-th to *100-p*-th percentile. '_' is to suppress 
    creating a new figure and paint to the current one instead. The letter specifications 
    can be applied sequentially, e.g. 'p_'.
    :type spec: str

    :arg p: specifies the percentile threshold.
    :type p: double
    """

    assert isinstance(map, np.ndarray), 'map must be a numpy.ndarray.'
    
    from matplotlib.pyplot import figure, imshow

    if not '_' in spec:
        figure()
    
    if 'p' in spec:
        p = kwargs.pop('p', 5)
        lp = kwargs.pop('lp', p)
        hp = kwargs.pop('hp', 100-p)
        vmin = np.percentile(map, lp)
        vmax = np.percentile(map, hp)
    else:
        vmin = vmax = None
    
    im = imshow(map, vmin=vmin, vmax=vmax, **kwargs)

    if SETTINGS['auto_show']:
        showFigure()

    return im

def showDomains(domains, linespec='r-', **kwargs):
    """A convenient function that can be used to visualize Hi-C structural domains. 
    *kwargs* will be passed to :func:`matplotlib.pyplot.plot`.

    :arg domains: a 2D array of Hi-C domains, such as [[start1, end1], [start2, end2], ...].
    :type domains: :class:`numpy.ndarray`
    """

    domains = np.array(domains)
    shape = domains.shape

    if len(shape) < 2:
        # convert to domain list if labels are provided
        indicators = np.diff(domains)
        indicators = np.append(1., indicators)
        indicators[-1] = 1
        sites = np.where(indicators != 0)[0]
        starts = sites[:-1]
        ends = sites[1:]
        domains = np.array([starts, ends]).T

    from matplotlib.pyplot import figure, plot

    x = []; y = []
    lwd = kwargs.pop('linewidth', 1)
    linewidth = np.abs(lwd)
    for i in range(len(domains)):
        domain = domains[i]
        start = domain[0]; end = domain[1]
        if lwd > 0:
            x.extend([start, end, end])
            y.extend([start, start, end])
        else:
            x.extend([start, start, end])
            y.extend([start, end, end])
    
    plt = plot(x, y, linespec, linewidth=linewidth, **kwargs)
    if SETTINGS['auto_show']:
        showFigure()
    return plt

def _getEigvecs(modes, row_norm=False, remove_zero_rows=False):
    if isinstance(modes, (ModeSet, NMA)):
        V = modes.getEigvecs()
    elif isinstance(modes, Mode):
        V = modes.getEigvec()
    elif isinstance(modes, np.ndarray):
        V = modes
    else:
        try:
            mode0 = modes[0]
            if isinstance(mode0, Mode):
                V = np.empty((len(mode0),0))
                for mode in modes:
                    assert isinstance(mode, Mode), 'Modes should be a list of modes.'
                    v = mode.getEigvec()
                    v = np.expand_dims(v, axis=1)
                    V = np.hstack((V, v))
            else:
                V = np.array(modes)
        except TypeError:
            TypeError('Modes should be a list of modes.')
    if V.ndim == 1:
        V = np.expand_dims(V, axis=1)

    # normalize the rows so that feature vectors are unit vectors
    if row_norm:
        la = importLA()
        norms = la.norm(V, axis=1)
        N = np.diag(div0(1., norms))
        V = np.dot(N, V)
    
    # remove rows with all zeros
    m, _ = V.shape
    mask = np.ones(m, dtype=bool)
    if remove_zero_rows:
        mask = V.any(axis=1)
        V = V[mask]
    return V, mask

def showEmbedding(modes, labels=None, trace=True, headtail=True, cmap='prism'):
    """Visualizes Laplacian embedding of Hi-C data. 

    :arg modes: modes in which loci are embedded. It can only have 2 or 3 modes for the purpose 
    of visualization.
    :type modes: :class:`ModeSet`

    :arg labels: a list of integers indicating the segmentation of the sequence.
    :type labels: list

    :arg trace: if **True** then the trace of the sequence will be indicated by a grey dashed line.
    :type trace: bool

    :arg headtail: if **True** then a star and a closed circle will indicate the head and the tail 
    of the sequence respectively.
    :type headtail: bool

    :arg cmap: the color map used to render the *labels*.
    :type cmap: str
    """
    V = _getEigvecs(modes, True)
    m,n = V.shape

    if labels is not None:
        if len(labels) != m:
            raise ValueError('Modes (%d) and the Hi-C map (%d) should have the same number'
                                ' of atoms. Turn off "masked" if you intended to apply the'
                                ' modes to the full map.'
                                %(m, len(labels)))
    if n > 3:
        raise ValueError('This function can only visualize the embedding of 2 or 3 modes.')
    
    from matplotlib.pyplot import figure, plot, scatter
    from mpl_toolkits.mplot3d import Axes3D

    if n == 2:
        la = importLA()

        X, Y = V[:,:2].T
        R = np.array(range(len(X)))
        R = R / la.norm(R)
        X *= R; Y *= R
        
        f = figure()
        if trace:
            plot(X, Y, ':', color=[0.3, 0.3, 0.3])
        if labels is None:
            C = 'b'
        else:
            C = labels
        scatter(X, Y, s=30, c=C, cmap=cmap)
        if headtail:
            plot(X[:1], Y[:1], 'k*', markersize=12)
            plot(X[-1:], Y[-1:], 'ko', markersize=12)
    elif n == 3:
        X, Y, Z = V[:,:3].T
        
        f = figure()
        ax = Axes3D(f)
        if trace:
            ax.plot(X, Y, Z, ':', color=[0.3, 0.3, 0.3])
        if labels is None:
            C = 'b'
        else:
            C = labels
        ax.scatter(X, Y, Z, s=30, c=C, depthshade=True, cmap=cmap)
        if headtail:
            ax.plot(X[:1], Y[:1], Z[:1], 'k*', markersize=12)
            ax.plot(X[-1:], Y[-1:], Z[-1:], 'ko', markersize=12)

    if SETTINGS['auto_show']:
        showFigure()
    return f

def getDomainList(labels):
    """Returns a list of domain separations. The list has two columns: the first is for 
    the domain starts and the second is for the domain ends."""

    indicators = np.diff(labels)
    indicators = np.append(1., indicators)
    indicators[-1] = 1
    sites = np.where(indicators != 0)[0]
    starts = sites[:-1]
    ends = sites[1:]
    domains = np.array([starts, ends]).T

    return domains