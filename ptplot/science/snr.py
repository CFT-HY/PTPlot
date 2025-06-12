"""SNR computation

This file contains all the functions related to the calculation of the
signal to noise ratio for a given sensitivity, spectrum and observation time.
These functions are inspired by the ones in Antoine Petiteau's eLISAToolBox aka
eLISATools.py, adapted to use a trapezium rule integration with nonuniform interval.

Contains the following functions:
    * load_file - reads arrays from a file
    * stock_bkg_compute_snr - computes the SNR
"""

import typing as tp

import numpy as np
import scipy.integrate

from ptplot.science import const
from ptplot.science.powerspectrum import PowerSpectrum


def get_snr_value(
        fSens: np.ndarray,
        omSens: np.ndarray,
        duration: float,
        Tstar: float = const.DEFAULT_T_STAR,
        gstar: float = const.DEFAULT_G_STAR,
        vw: float = const.DEFAULT_VW,
        alpha: float = const.DEFAULT_ALPHA,
        BetaoverH: float = const.DEFAULT_BETA_OVER_H) -> np.ndarray:
    """Calculate the SNR value for a given power spectrum

    Note that this function is currently not being used by the code, but it
    is included here for legacy reasons.

    Parameters
    ----------
    fSens : np.ndarray
        List of frequencies in Hz corresponding to omSens
    omSens : np.ndarray
        List of sensitivities in Omega units
    duration : float
        Observation time in seconds
    Tstar : float, Optional
        Transition temperature (default to 180.0)
    gstar : float, Optional
        Degrees of freedom (default to 100)
    vw : float, Optional
        Wall velocity (default to 0.9)
    alpha : float, Optional
        Phase transition strength (default to 0.1)
    BetaoverH : float, Optional
        Inverse phase transition duration relative to H (default to 10)

    Returns
    -------
    snr : np.ndarray
        Signal-to-noise ratio
    """
    ps = PowerSpectrum(
        T_star=Tstar, g_star=gstar,
        vw=vw, alpha=alpha, beta_over_H=BetaoverH
    )
    snr_value, frange = stock_bkg_compute_snr(
        fSens,
        omSens,
        fSens,
        ps.power_spectrum_sw_conservative(fSens),
        duration,
        1.e-6,
        1
    )
    return snr_value


# Replaced by np.loadtxt
# def load_file(path: str, col_ind: int) -> tp.Tuple[np.ndarray, np.ndarray]:
#     """Load first column and column col_ind of a file
#
#     Parameters
#     ----------
#     path : string
#         Input file name
#     col_ind : int
#         Index of the column containing the data (column 0 is the reference)
#
#     Returns
#     -------
#     x : np.ndarray
#         Reference column
#     y : np.ndarray
#         Data read from file
#     """
#
#     with open(path, "r") as fIn:
#         lines = fIn.readlines()
#
#     Nd = 0
#     for line in lines:
#         if line[0] != "#" and len(line) > 0:
#             Nd += 1
#
#     x  = np.zeros(Nd)
#     y = np.zeros(Nd)
#     iL = 0
#     for line in lines:
#         if line[0] != "#" and len(line) > 0:
#             w = re.split(r"\s+", line)
#             x[iL] = float(w[0])
#             y[iL] = float(w[col_ind])
#             iL += 1
#     return x, y


def stock_bkg_compute_snr(
        sens_freq: np.ndarray,
        sens_omega: np.ndarray,
        gw_freq: np.ndarray,
        gw_omega: np.ndarray,
        obs_time: float,
        f_min: float = None,
        f_max: float = None) -> tp.Tuple[float, tp.Tuple[float, float]]:
    """Compute signal to noise ratio

    Compute signal to noise ratio and the used frequency range fmin and fmax for
    a given sensitivity, defined by the two numpy arrays (of the same size)
    SensFr (for frequency) and SensOm for sensitivity in Omega unit; a given
    spectrum, defined by the two numpy arrays (same size) GWFr for frequency
    and GWOm for GW in Omega units; and a given observation time Tobs in years.
    If the frequency range frange is not defined, the frequency range will be
    adjusted based on the two frequency arrays.

    Parameters
    ----------
    sens_freq : np.ndarray
        Array of frequencies (in Hz) corresponding to SensOm
    sens_omega : np.ndarray
        Array of sensitivities in Omega units
    gw_freq : np.ndarray
        Array of frequencies (in Hz) corresponding to GWOm
    gw_omega : np.ndarray
        Array of GW stochastic background
    obs_time : float
        Total observation time / mission duration (in seconds)
    f_min : float
        Minimum frequency for frange (in Hz)
    f_max : float
        Maximum frequency for frange (in Hz)

    Returns
    -------
    snr: float
        Signal to noise ratio
    """

    # If the frequency range has not been given, find it automatically
    if f_min is None:
        f_min = max(sens_freq[0], gw_freq[0])
    if f_max is None:
        f_max = min(sens_freq[-1], gw_freq[-1])

    i_f_min = np.argmax(sens_freq >= f_min)
    i_f_max = np.argmax(sens_freq >= f_max)

    fr = sens_freq[i_f_min:i_f_max]
    omega_eff = sens_omega[i_f_min:i_f_max]

    # Make an interpolated data series, interpolate GWOm onto same series as omega_eff
    omega_gw_interp = 10.**np.interp(np.log10(fr), np.log10(gw_freq), np.log10(gw_omega))

    # Numerical integration over frequency
    rat = omega_gw_interp**2 / omega_eff**2
    Itg = scipy.integrate.trapezoid(rat, fr)

    # Calculate snr taking into account the observation time
    snr = np.sqrt(obs_time * Itg)

    return snr, (f_min, f_max)
