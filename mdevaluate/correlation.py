import numpy as np
from itertools import chain
from functools import reduce
from .coordinates import pbc_diff
from .meta import annotate


def log_indices(first, last, num=100):
    ls = np.logspace(0, np.log10(last-first+1), num=num)
    return np.unique(np.int_(ls)-1+first)


def correlation(function, frames):
    iterator = iter(frames)
    start_frame = next(iterator)
    return map(lambda f: function(start_frame, f), chain([start_frame], iterator))


def subensemble_correlation(selector_function, correlation_function=correlation):

    def c(function, frames):
        iterator = iter(frames)
        start_frame = next(iterator)
        selector = selector_function(start_frame)
        subensemble = map(lambda f: f[selector], chain([start_frame], iterator))
        return correlation_function(function, subensemble)
    return c


def shifted_correlation(function,
                        frames,
                        index_distribution=log_indices,
                        segments=10,
                        window=0.5,
                        correlation=correlation):

    start_frames = np.int_(np.linspace(0, len(frames)*(1-window), num=segments, endpoint=False))
    num_frames = int(len(frames) * window)

    idx = index_distribution(0, num_frames)
    def correlate(start_frame):
        shifted_idx = idx+start_frame
        return correlation(function, map(frames.__getitem__, shifted_idx))

    result = np.array([list(correlate(start_frame)) for start_frame in start_frames])
    return idx, result

def msd(start, frame, box=None):
    """
    Mean square displacement
    """
    vec = pbc_diff(start, frame, box)
    return (vec ** 2).sum(axis=1).mean()


def isf(start, frame, q, box=None):
    """
    Incoherent intermediate scattering function. To specify q, use
    water_isf = functools.partial(isf, q=22.77) # q has the value 22.77 nm^-1

    :param q: length of scattering vector
    """
    vec = pbc_diff(start, frame, box)
    distance = (vec ** 2).sum(axis=1) ** .5
    return np.sinc(distance * q / np.pi).mean()


@annotate.untested
def oaf(start, frame):
    """
    Orientation autocorrelation function. start and frame must be connection vectors, not absolute coordinates. Use for
    example oaf_indexed to define connection vectors.

    :param start:
    :param frame:
    :return:
    """
    vec_start_norm = np.norm(start)
    vec_frame_norm = np.norm(frame)

    dot_prod = (start*frame).sum(axis=1) /(vec_start_norm, vec_frame_norm)
    return (3*dot_prod**2 - 1).mean() / 2.0



def oaf_indexed(index_from, index_to):
    """
    Returns a OAF correlation function. Example
    oaf_indexed(t[:,1] == 'C', t[:,1] == 'O')
    :param index_from:
    :param index_to:
    :return:
    """
    return lambda start, frame: oaf(start[index_to]-start[index_from],
                                    frame[index_to]-frame[index_from])



@annotate.unfinished
def van_hove(start, end, bins, box=None):
    vec = pbc_diff(start, end, box)
    delta_r = ((vec)**2).sum(axis=1) ** .5

    return 1/len(start) * np.histogram(delta_r, bins)[0]

