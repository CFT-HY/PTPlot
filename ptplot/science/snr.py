"""Signal-to-noise ratio calculations for gravitational wave spectra"""

import numpy as np
from pttools.omgw0 import signal_to_noise_ratio

from ptplot.science.engine import Engine
from ptplot.science.mission_profile import MissionProfile
from ptplot.science.spectrum.create import power_spectrum


def snr_point(
        x: float,
        y: float,
        T_star: float,
        g_star: float,
        v_wall: float,
        adiabatic_ratio: float,
        f_min: float,
        f_max: float,
        mission_profile: MissionProfile,
        engine: Engine,
        ubarf_rstar: bool = False) -> tuple[float, float]:
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
