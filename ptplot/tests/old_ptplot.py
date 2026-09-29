r"""Access to the last version of PTPlot before the restructuring, for comparisons.

The old PTPlot is the ``main`` branch of PTPlot (commit 68aaf96 or similar).
It is looked for in ``../old/PTPlot`` relative to this repository,
or in the directory given by the environment variable :py:data:`OLD_PTPLOT_ENV`.
The old code is imported as standalone modules from its ``ptplot/science`` directory,
so Django is not needed for it.

The SNR of the new code differs from the old one by constant factors:

- The noise: the old sensitivity curves are smaller than the PTtools instrument noise by
  :py:data:`ptplot.tests.test_noise.SENSITIVITY_FILE_FACTOR` $\approx 5.98$
  (please see :py:mod:`ptplot.tests.test_noise`), and the SNR is inversely proportional to the noise.
- $F_{\text{gw},0} h^2$: the old code has $0.678^2 \cdot 3.57 \cdot 10^{-5} (100/g_*)^{1/3}$,
  whereas :py:func:`pttools.omgw0.F_gw0_h2` computes it from $\Omega_{\gamma,0} h^2$, which gives 0.66 % more.

If the old PTPlot is not available, :py:func:`reconstructed_old_grid` reproduces its SNR grid
with the new code, the old sensitivity curve and the old $F_{\text{gw},0} h^2$.
"""

import contextlib
import functools
import importlib
import logging
import math
import os
from pathlib import Path
import sys
import types
import typing as tp
from unittest import mock
import warnings

import numpy as np
from pttools.bubble.energy_budget import alpha_n_from_ubarf
from pttools.omgw0 import F_gw0_h2
from pttools.omgw0.noise import S_AE_approx, omega_h2
from pttools.ssm import beta_tilde as beta_tilde_func
import scipy.integrate

from ptplot import PTPLOT_DIR
from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th
from ptplot.tests.test_noise import SENSITIVITY_FILE_FACTOR, load_sensitivity

#: Environment variable that overrides the location of the old PTPlot
OLD_PTPLOT_ENV: str = "PTPLOT_OLD_DIR"
#: Location of the old PTPlot, by default ``../old/PTPlot`` relative to this repository
OLD_PTPLOT_DIR: Path = Path(os.environ.get(OLD_PTPLOT_ENV, PTPLOT_DIR.parents[1] / "old" / "PTPlot"))
OLD_SCIENCE_DIR: Path = OLD_PTPLOT_DIR / "ptplot" / "science"
#: The old modules, in the order of their dependencies
OLD_MODULES: tuple[str, ...] = ("espinosa", "snr", "precomputed", "calculate_powerspectrum", "SNR_precompute")
#: Whether the old PTPlot was found
HAVE_OLD_PTPLOT: bool = all((OLD_SCIENCE_DIR / f"{name}.py").is_file() for name in OLD_MODULES)
NOT_FOUND_MESSAGE: str = f"The old PTPlot was not found in {OLD_PTPLOT_DIR}. Set {OLD_PTPLOT_ENV} to its location."

#: Mission profile 0 of the old code: the science requirements curve for 3 years
OLD_MISSION_PROFILE: int = 0
#: Mission duration of :py:data:`OLD_MISSION_PROFILE`
OLD_OBS_YEARS: float = 3.
#: The old sensitivity curve that the old SNR code used
OLD_SENSITIVITY_FILE: str = "ScienceRequirementsLite"
#: The old SNR code integrated up to this frequency (Hz)
OLD_F_MAX: float = 1.
#: The largest $\bar{U}_f$ of the old $(\bar{U}_f, r_*)$ figure without "huge alpha"
OLD_UBARF_MAX_UBARF_RSTAR: float = 1.
#: The largest $\bar{U}_f$ of the old $(\alpha, \beta/H_*)$ figure without "huge alpha"
OLD_UBARF_MAX_ALPHA_BETA: float = 0.6
#: Size of the old grids
OLD_GRID_SIZE: int = 51
#: $\log_{10} r_*$ range of the old grids
OLD_LOG10_R_STAR_RANGE: tuple[float, float] = (-4., 0.08)
#: Smallest $\log_{10} \bar{U}_f$ of the old grids
OLD_LOG10_UBARF_MIN: float = -2.

#: The old grid: shock times $H_* \tau_\text{sh}$, SNR, $\log_{10} r_*$ and $\log_{10} \bar{U}_f$
type OldGrid = tuple[th.FloatArr2D, th.FloatArr2D, th.FloatArr1D, th.FloatArr1D]


def old_f_gw0_h2(g_star: float) -> float:
    r"""$F_{\text{gw},0} h^2$ of the old code."""
    return 0.678**2 * 3.57e-5 * (100 / g_star)**(1 / 3)


def f_gw0_ratio(g_star: float) -> float:
    r"""Ratio of the new and the old $F_{\text{gw},0} h^2$."""
    return float(F_gw0_h2(g_star)) / old_f_gw0_h2(g_star)


def snr_factor(g_star: float) -> float:
    r"""Ratio of the new and the old SNR, when the only differences are the constant factors.

    These are the noise conversion factor and $F_{\text{gw},0} h^2$.
    """
    return f_gw0_ratio(g_star) / SENSITIVITY_FILE_FACTOR


@functools.cache
def old_modules() -> types.SimpleNamespace:
    """Import the old science modules without leaving them in :py:data:`sys.modules`.

    The old modules import each other with bare names such as ``snr``,
    so their directory has to be in :py:data:`sys.path` while they are being imported.

    :raises FileNotFoundError: if the old PTPlot is not found
    """
    if not HAVE_OLD_PTPLOT:
        raise FileNotFoundError(NOT_FOUND_MESSAGE)
    saved = {name: sys.modules.pop(name) for name in OLD_MODULES if name in sys.modules}
    sys.path.insert(0, str(OLD_SCIENCE_DIR))
    try:
        with warnings.catch_warnings():
            # The old code has invalid escape sequences in regular expressions.
            warnings.simplefilter("ignore", SyntaxWarning)
            modules = {name: importlib.import_module(name) for name in OLD_MODULES}
    finally:
        sys.path.remove(str(OLD_SCIENCE_DIR))
        for name in OLD_MODULES:
            sys.modules.pop(name, None)
        sys.modules.update(saved)
    # The old code looks for the sensitivity curves relative to the working directory.
    vars(modules["SNR_precompute"])["sensitivity_root"] = str(OLD_SCIENCE_DIR / "sensitivity")
    return types.SimpleNamespace(**modules)


@contextlib.contextmanager
def old_scipy() -> tp.Iterator[None]:
    """Provide :py:func:`scipy.integrate.trapz`, which the old code uses but SciPy no longer has."""
    with mock.patch.object(scipy.integrate, "trapz", np.trapezoid, create=True):
        yield


@functools.cache
def old_grid(
        T_star: float,
        g_star: float,
        ubarf_max: float = OLD_UBARF_MAX_UBARF_RSTAR,
        mission_profile: int = OLD_MISSION_PROFILE) -> OldGrid:
    r"""Compute the SNR grid of the old code on the $(\bar{U}_f, r_*)$ plane.

    :param T_star: $T_*$
    :param g_star: $g_*$
    :param ubarf_max: Largest $\bar{U}_f$ of the grid
    :param mission_profile: Which sensitivity curve and mission duration to use
    :return: shock times $H_* \tau_\text{sh}$, SNR, $\log_{10} r_*$ and $\log_{10} \bar{U}_f$
    """
    with old_scipy():
        return old_modules().SNR_precompute.get_SNRcurve(T_star, g_star, mission_profile, ubarf_max)


def exact_noise(obs_years: float = OLD_OBS_YEARS) -> Noise:
    """PTtools instrument noise with the exact LISA response."""
    return Noise(obs_years=obs_years, eb=False, gb=False)


def approx_noise(obs_years: float = OLD_OBS_YEARS) -> Noise:
    """PTtools instrument noise with the low-frequency approximation of the LISA response."""
    noise = Noise(obs_years=obs_years, eb=False, gb=False)
    noise.noise = np.ascontiguousarray(omega_h2(f=noise.f, S=S_AE_approx(noise.f)))
    return noise


def old_file_noise(obs_years: float = OLD_OBS_YEARS) -> Noise:
    """Get the old sensitivity curve as a :py:class:`Noise` object, cut to the frequencies of the old SNR code."""
    f, sensitivity = load_sensitivity(OLD_SENSITIVITY_FILE)
    noise = Noise(obs_years=obs_years, eb=False, gb=False)
    mask = f < OLD_F_MAX
    noise.f = np.ascontiguousarray(f[mask])
    noise.noise = np.ascontiguousarray(sensitivity[mask])
    return noise


def old_grid_axes(ubarf_max: float = OLD_UBARF_MAX_UBARF_RSTAR) -> tuple[th.FloatArr1D, th.FloatArr1D]:
    r"""Get the $\bar{U}_f$ and $r_*$ axes of the old grids."""
    ubarf = np.logspace(OLD_LOG10_UBARF_MIN, math.log10(ubarf_max), OLD_GRID_SIZE)
    r_star = np.logspace(*OLD_LOG10_R_STAR_RANGE, OLD_GRID_SIZE)
    return ubarf, r_star


@functools.cache
def reconstructed_old_grid(
        T_star: float,
        g_star: float,
        ubarf_max: float = OLD_UBARF_MAX_UBARF_RSTAR) -> OldGrid:
    r"""Reproduce the SNR grid of the old code with the new code.

    This uses the old sensitivity curve and the old $F_{\text{gw},0} h^2$,
    and is therefore independent of the new noise curves.
    It can be used when the old PTPlot is not available.
    The BPL2020 spectrum does not depend on $v_\text{wall}$ on the $(\bar{U}_f, r_*)$ plane.

    :param T_star: $T_*$
    :param g_star: $g_*$
    :param ubarf_max: Largest $\bar{U}_f$ of the grid
    :return: shock times $H_* \tau_\text{sh}$, SNR, $\log_{10} r_*$ and $\log_{10} \bar{U}_f$
    """
    ubarf, r_star = old_grid_axes(ubarf_max)
    grid = SNRGridUbarfRStar(
        v_wall=const.DEFAULT_V_WALL, T_star=T_star, g_star=g_star, ubarf=ubarf, r_star=r_star,
        noise=old_file_noise(), engine=Engine.BPL2020, log_progress_percentage=None
    )
    return grid.shock_times, grid.snr / f_gw0_ratio(g_star), np.log10(r_star), np.log10(ubarf)


def old_or_reconstructed_grid(
        T_star: float,
        g_star: float,
        ubarf_max: float = OLD_UBARF_MAX_UBARF_RSTAR) -> tuple[OldGrid, bool]:
    r"""Get the old SNR grid from the old PTPlot if it is available, and otherwise reconstruct it.

    :return: the grid as returned by :py:func:`old_grid`, and whether it was computed with the old code
    """
    if HAVE_OLD_PTPLOT:
        return old_grid(T_star, g_star, ubarf_max), True
    return reconstructed_old_grid(T_star, g_star, ubarf_max), False


def old_alpha_beta_axes(
        v_wall: float,
        log10_ubarf: th.FloatArr1D,
        log10_r_star: th.FloatArr1D) -> tuple[th.FloatArr1D, th.FloatArr1D]:
    r"""Convert the axes of an old grid to $(\alpha, \beta/H_*)$ as the old $(\alpha, \beta/H_*)$ figure did.

    The old figure (``SNRalphabeta_onthefly.py``) computed the grid on the $(\bar{U}_f, r_*)$ plane
    and converted the axes with the Espinosa fit for $\kappa$ and the legacy $\max(v_{\text{wall}}, c_s)$.
    If the old PTPlot is not available, the equivalent PTtools functions are used.

    :param v_wall: $v_\text{wall}$
    :param log10_ubarf: $\log_{10} \bar{U}_f$ axis of the old grid
    :param log10_r_star: $\log_{10} r_*$ axis of the old grid
    :return: $\alpha$ and $\beta/H_*$ axes
    """
    ubarf = 10**np.asarray(log10_ubarf)
    r_star = 10**np.asarray(log10_r_star)
    if HAVE_OLD_PTPLOT:
        old = old_modules()
        alpha = old.espinosa.ubarf_to_alpha(v_wall, ubarf)
        beta_tilde = np.array([old.calculate_powerspectrum.rstar_to_beta(r, v_wall) for r in r_star])
    else:
        alpha = np.array([alpha_n_from_ubarf(v_wall=v_wall, ubarf=u) for u in ubarf])
        # The old grids extend to beta/H* < 10, for which PTtools warns about the accuracy of the conversion.
        logging.disable(logging.WARNING)
        try:
            beta_tilde = np.asarray(beta_tilde_func(r_star=r_star, v_wall=v_wall, legacy_cs=const.CS0))
        finally:
            logging.disable(logging.NOTSET)
    return alpha, beta_tilde
