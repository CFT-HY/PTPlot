import math

import numpy as np

from ptplot.science import const
import ptplot.science.type_hints as th


def atleast_2d(*args: th.FloatOrListOrNestedLisOrArr) -> th.ArrOrListOfArrs | list[list[np.ndarray]]:
    """Convert a scalar, 1D array or 2D array into a 2D numpy array.

    Similar to numpy.atleast_2d, but supports nested lists with varying lenghts.
    """
    num_args = len(args)
    if not num_args:
        raise ValueError("At least one argument is required.")
    if num_args == 1:
        return atleast_2d_single(args[0])
    return [atleast_2d_single(values) for values in args]


def atleast_2d_single(values: th.FloatOrListOrNestedLisOrArr) -> th.ArrOrListOfArrs:
    if isinstance(values, np.ndarray):
        return np.atleast_2d(values)
    if np.isscalar(values):
        return np.array([[values]])
    if np.isscalar(values[0]):
        return np.array([values])
    # If the data has a regular shape, convert it to a 2D numpy array.
    if np.all([len(sub_values) == len(values[0]) for sub_values in values]):
        return np.array(values)
    return [np.array(sub_values) for sub_values in values]


def rstar_to_beta(rstar: float, vw: float, cs: float = const.CS0) -> float:
    r"""Convert R_* to \Beta_* for a given wall velocity

    Parameters
    ----------
    rstar : float
        Mean bubble separation
    vw : float
        Wall velocity
    cs : float
        Speed of sound (default to 1/sqrt(3))

    Returns
    -------
    beta : float
        Inverse phase transition duration
    """
    return math.pow(8.0 * math.pi, 1.0/3.0) * max(vw, cs) / rstar


def beta_to_rstar(beta: float, vw: float, cs: float = const.CS0) -> float:
    r"""Convert \Beta_* to R_* for a given wall velocity

    Parameters
    ----------
    beta : float
        Inverse phase transition duration
    vw : float
        Wall velocity
    cs : float
        Speed of sound (default to 1/sqrt(3))

    Returns
    -------
    rstar : float
        Mean bubble separation
    """
    return math.pow(8.0 * math.pi, 1.0/3.0) * max(vw, cs) / beta
