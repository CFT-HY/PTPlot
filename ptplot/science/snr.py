"""SNR computation

This file contains all the functions related to the calculation of the
signal to noise ratio for a given sensitivity, spectrum and observation time.
These functions are inspired by the ones in Antoine Petiteau's eLISAToolBox aka
eLISATools.py, adapted to use a trapezium rule integration with nonuniform interval.
"""

import numpy as np

from ptplot.science import const
from ptplot.science.spectrum.bpl import PowerSpectrumBPL
from pttools.omgw0 import signal_to_noise_ratio


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

    :param fSens: Frequencies in Hz corresponding to omSens
    :param omSens: Sensitivities in Omega units
    :param Tstar: Transition temperature $T_*$
    :param gstar: Degrees of freedom $g_*$
    :param vw: Wall velocity $v_\text{wall}$
    :param alpha: Phase transition strengh $\alpha$
    :param BetaoverH: Inverse phase transition duration relative to $H$
    :return: signal-to-noise ratio
    """
    ps = PowerSpectrumBPL(
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


def stock_bkg_compute_snr(
        sens_freq: np.ndarray,
        sens_omega: np.ndarray,
        gw_freq: np.ndarray,
        gw_omega: np.ndarray,
        obs_time: float,
        f_min: float = None,
        f_max: float = None) -> tuple[float, tuple[float, float]]:
    """Compute signal to noise ratio

    Compute signal to noise ratio and the used frequency range fmin and fmax for
    a given sensitivity, defined by the two numpy arrays (of the same size)
    SensFr (for frequency) and SensOm for sensitivity in Omega unit; a given
    spectrum, defined by the two numpy arrays (same size) GWFr for frequency
    and GWOm for GW in Omega units; and a given observation time Tobs in years.
    If the frequency range frange is not defined, the frequency range will be
    adjusted based on the two frequency arrays.

    :param sens_freq: Frequencies (in Hz) corresponding to SensOm
    :param sens_omega: Sensitivities in Omega units
    :param gw_freq: Frequencies (in Hz) corresponding to GWOm
    :param gw_omega: GW stochastic background
    :param obs_time: Total observation time / mission duration (in seconds)
    :param f_min: Minimum frequency for frange (in Hz)
    :param f_max: Maximum frequency for frange (in Hz)
    :return: signal-to-noise ratio, (f_min, f_max)
    """
    # TODO: Replace this function with the PTtools signal-to-noise ratio,
    #   when its updated version is included in a PTtools release.

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

    snr = signal_to_noise_ratio(f=fr, signal=omega_gw_interp, noise=omega_eff, obs_time=obs_time)
    return snr, (f_min, f_max)
