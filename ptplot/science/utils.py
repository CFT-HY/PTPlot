"""Utilities for PTPlot science module"""
import math

import numpy as np

from ptplot.science import const
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatArr


def atleast_2d(*args: th.FloatOrListOrNestedListOrArr) -> th.ArrOrListOfArrs | list[list[np.ndarray]]:
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


def atleast_2d_single(values: th.FloatOrListOrNestedListOrArr) -> th.ArrOrListOfArrs:
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


def rstar_to_beta[T: (float, FloatArr)](R_star: T, vw: float, cs: float = const.CS0) -> T:
    r"""Convert R_* to \beta for a given wall velocity

    $$R_* = \frac{8\pi}{3} \frac{\max (v_w, c_s)}{\beta}$$

    :param R_star: Mean bubble separation $R_*$
    :param vw: Wall velocity $v_w$
    :param cs: Sound speed $c_s$
    :return: Inverse phase transition duration $\beta$
    """
    return math.pow(8.0 * math.pi, 1.0/3.0) * max(vw, cs) / R_star


def beta_to_R_star[T: (float, FloatArr)](beta: T, vw: float, cs: float = const.CS0) -> T:
    r"""Convert \beta to R_* for a given wall velocity $v_w$

    $$\beta = \frac{8\pi}{3} \frac{\max (v_w, c_s)}{R_*}$$

    :param beta: Inverse phase transition duration $\beta$
    :param vw: Wall velocity $v_w$
    :param cs: Sound speed $c_s$
    :return: Mean bubble separation $R_*$
    """
    return math.pow(8.0 * math.pi, 1.0/3.0) * max(vw, cs) / beta
