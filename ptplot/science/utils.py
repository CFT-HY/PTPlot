"""Utilities for PTPlot science module"""

import numpy as np

from ptplot.science import const
import ptplot.science.type_hints as th


def atleast_2d(*args: th.FloatOrArrOrList1D2D) -> th.ArrOrListOfArrs | list[list[np.ndarray]]:
    """Convert a scalar, 1D array or 2D array into a 2D numpy array.

    You can convert multiple arguments at once, and the output will be a list of 2D numpy arrays.
    Similar to numpy.atleast_2d, but supports nested lists with varying lengths.
    """
    num_args = len(args)
    if not num_args:
        raise ValueError("At least one argument is required.")
    if num_args == 1:
        return atleast_2d_single(args[0])
    return [atleast_2d_single(values) for values in args]


def atleast_2d_single(values: th.FloatOrArrOrList1D2D) -> th.ArrOrListOfArrs:
    if isinstance(values, np.ndarray):
        if values.ndim == 0:
            return np.array([[values]])
        if values.ndim == 1:
            return np.array([values])
        return values
    if np.isscalar(values):
        return np.array([[values]])
    if np.isscalar(values[0]):
        return np.array([values])
    # If the data has a regular shape, convert it to a 2D numpy array.
    if np.all([len(sub_values) == len(values[0]) for sub_values in values]):
        return np.array(values)
    return [np.array(sub_values) for sub_values in values]


def beta_from_R_star(R_star: th.FloatOrArr, v_wall: th.FloatOrArr, cs: th.FloatOrArr = const.CS0) -> th.FloatOrArr:
    r"""Convert R_* to \beta for a given wall velocity

    $$R_* = \frac{8\pi}{3} \frac{\max (v_w, c_s)}{\beta}$$

    :param R_star: Mean bubble separation $R_*$
    :param v_wall: Wall velocity $v_w$
    :param cs: Sound speed $c_s$
    :return: Inverse phase transition duration $\beta$
    """
    return (8 * np.pi)**(1/3) * np.maximum(v_wall, cs) / R_star


def R_star_from_beta(beta: th.FloatOrArr, v_wall: th.FloatOrArr, cs: th.FloatOrArr = const.CS0) -> th.FloatOrArr:
    r"""Convert \beta to R_* for a given wall velocity $v_w$

    $$\beta = \frac{8\pi}{3} \frac{\max (v_w, c_s)}{R_*}$$

    :param beta: Inverse phase transition duration $\beta$
    :param v_wall: Wall velocity $v_w$
    :param cs: Sound speed $c_s$
    :return: Mean bubble separation $R_*$
    """
    return (8 * np.pi)**(1/3) * np.maximum(v_wall, cs) / beta
