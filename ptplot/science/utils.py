"""Utilities for PTPlot science module."""

import logging
import os
import typing as tp

from dulwich.errors import NotGitRepository
from dulwich.porcelain import describe
from dulwich.repo import Repo
import numpy as np
from pttools.bubble.energy_budget import ubarf_approx
from pttools.models import Model
from pttools.ssm.nucleation import r_star as r_star_func

from ptplot.science import const
import ptplot.science.type_hints as th

logger = logging.getLogger(__name__)

GIT_DESCRIPTION: str = "unknown"
HAVE_GITVER: bool = False

try:
    GIT_DESCRIPTION = describe(Repo.discover(os.path.realpath(os.path.dirname(__file__))))
    HAVE_GITVER = True
except NotGitRepository as err:
    logger.exception("Could not load git repository info.", exc_info=err)


@tp.overload
def atleast_2d(values: th.FloatOrArrOrList1D2D, /) -> th.ArrOrListOfArrs: ...


@tp.overload
def atleast_2d(*args: th.FloatOrArrOrList1D2D) -> list[th.ArrOrListOfArrs]: ...


def atleast_2d(*args: th.FloatOrArrOrList1D2D) -> th.ArrOrListOfArrs | list[th.ArrOrListOfArrs]:
    """Convert one or several of these to a 2D Numpy array: a scalar, 1D array or 2D array.

    You can convert multiple arguments at once, and the output will be a list of 2D numpy arrays.
    Similar to numpy.atleast_2d, but supports nested lists with varying lengths.
    """
    num_args = len(args)
    if not num_args:
        raise ValueError("At least one argument is required.")
    if num_args == 1:
        return atleast_2d_single(args[0])
    return [atleast_2d_single(values) for values in args]


def atleast_2d_single(values: th.FloatOrArrOrList1D2D) -> th.ArrOrListOfArrs:  # noqa: PLR0911
    """Convert a scalar, 1D array or 2D array to a Numpy array."""
    if isinstance(values, np.ndarray):
        if values.ndim == 0:
            return np.array([[values]])
        if values.ndim == 1:
            return np.array([values])
        return values
    if np.isscalar(values):
        return np.array([[values]])
    # The scalars and arrays have been handled above, so only the lists are left.
    values_list = tp.cast("list[float] | list[list[float]] | list[th.FloatArr1D]", values)
    if np.isscalar(values_list[0]):
        return np.array([values_list])
    nested = tp.cast("list[list[float]] | list[th.FloatArr1D]", values_list)
    # If the data has a regular shape, convert it to a 2D numpy array.
    if np.all([len(sub_values) == len(nested[0]) for sub_values in nested]):
        return np.array(nested)
    return [np.array(sub_values) for sub_values in nested]


def log_range(x: th.FloatOrArrOrList1D2D, default: th.FloatArr1D) -> th.FloatArr1D:
    """Get a logarithmic range that covers the values in x, but is not smaller than the default range."""
    x_min: float
    x_max: float
    if np.isscalar(x):
        x_min = x_max = tp.cast("float", x)
    elif isinstance(x, list):
        x_min = tp.cast("float", np.nanmin([np.nanmin(sub_x) for sub_x in x]))
        x_max = tp.cast("float", np.nanmax([np.nanmax(sub_x) for sub_x in x]))
    else:
        x_min = tp.cast("float", np.nanmin(x))
        x_max = tp.cast("float", np.nanmax(x))

    return np.logspace(
            np.log10(min(x_min, default[0])),
            np.log10(max(x_max, default[-1])),
            default.size) \
        if x_min < default[0] or x_max > default[-1] \
        else default


def ubarf_rstar_from_alpha_beta(
        v_wall: th.FloatOrArrOrListOfArr1D,
        alpha: th.FloatOrArrOrListOfArr1D,
        beta_tilde: th.FloatOrArrOrListOfArr1D,
        labels: th.StrOrListOrNestedList | None,
        model: Model | None = None,
        cs: float = const.CS0,
        adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
        legacy_nucleation_cs_max: bool = False) -> tuple[
            th.ArrOrListOfArrs,
            th.ArrOrListOfArrs,
            th.ArrOrListOfArrs,
            th.StrOrListOrNestedList | None]:
    r"""Convert $\alpha$ and $\frac{\beta}{H}$ to $\bar{U}_f$ and $R_*$."""
    # Ensure that input values are 2D arrays
    v_wall, alpha, beta_tilde = atleast_2d(v_wall, alpha, beta_tilde)
    if labels:
        if isinstance(labels, str):
            labels = [[labels]]
        elif isinstance(labels[0], str):
            labels = [labels]

    ubarf = [
        np.array([
            ubarf_approx(v_wall=vw, alpha_n=al, model=model, cs=cs, adiabatic_index=adiabatic_index)
            for vw, al in zip(v_wall_set, alpha_set, strict=True)
        ])
        for v_wall_set, alpha_set in zip(v_wall, alpha, strict=True)
    ]
    r_star = [
        np.array([
            r_star_func(
                beta_tilde=bt, v_wall=vw,
                legacy_cs=cs if legacy_nucleation_cs_max else None
            ) for bt, vw in zip(beta_tilde_set, v_wall_set, strict=True)
        ])
        for beta_tilde_set, v_wall_set in zip(beta_tilde, v_wall, strict=True)
    ]
    return v_wall, ubarf, r_star, labels


# def xy_log_ranges(x: th.FloatArr1D, y: th.FloatArr1D, x_range_default: th.FloatArr1D, y_range_default: th.FloatArr1D):
#     return log_range(x, x_range_default), log_range(y, y_range_default)
