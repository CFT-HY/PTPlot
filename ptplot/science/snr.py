"""Signal-to-noise ratio calculations for gravitational wave spectra"""

import numpy as np
from pttools.omgw0 import signal_to_noise_ratio

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import MissionProfile
from ptplot.science.spectrum.create import power_spectrum


def snr_point(
        x: float,
        y: float,
        T_star: float,
        g_star: float,
        v_wall: float,
        mission_profile: MissionProfile,
        engine: Engine,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        f_min: float = const.DEFAULT_SNR_F_MIN,
        f_max: float = const.DEFAULT_SNR_F_MAX,
        ubarf_rstar: bool = False) -> tuple[float, float]:
    """Compute the SNR value of a single point in the parameter space"""
    kwargs = {"ubarf": x, "r_star": y} if ubarf_rstar \
        else {"alpha": x, "beta_over_H": y}
    try:
        spectrum = power_spectrum(
            T_star=T_star,
            g_star=g_star,
            v_wall=v_wall,
            adiabatic_ratio=adiabatic_ratio,
            engine=engine,
            **kwargs
        )
    except (RuntimeError, ValueError):
        return np.nan, np.nan

    return signal_to_noise_ratio(
        f=mission_profile.f,
        signal=spectrum.power_spectrum(mission_profile.f),
        f_noise=mission_profile.f,
        noise=mission_profile.sensitivity,
        obs_time=mission_profile.duration_seconds,
        f_min=f_min,
        f_max=f_max
    ), spectrum.shock_time
