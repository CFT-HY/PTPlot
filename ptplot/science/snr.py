"""Signal-to-noise ratio calculations for gravitational wave spectra"""

import logging
import typing as tp

import numpy as np
from pttools.omgw0 import signal_to_noise_ratio

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import MissionProfile
from ptplot.science.spectrum.create import power_spectrum

logger = logging.getLogger(__name__)


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
        ubarf_rstar: bool = False,
        parallel: bool = True) -> tuple[float, float]:
    """Compute the SNR value of a single point in the parameter space"""
    kwargs: dict[str, tp.Any] = {"ubarf": x, "r_star": y} if ubarf_rstar \
        else {"alpha": x, "beta_over_H": y}
    try:
        spectrum = power_spectrum(
            T_star=T_star,
            g_star=g_star,
            v_wall=v_wall,
            adiabatic_ratio=adiabatic_ratio,
            engine=engine,
            parallel=parallel,
            **kwargs
        )
        snr, f_min, f_max = signal_to_noise_ratio(
            f=mission_profile.f,
            # Error logging is handled in this function
            signal=spectrum.power_spectrum(mission_profile.f, log_errors=False),
            f_noise=mission_profile.f,
            noise=mission_profile.sensitivity,
            obs_time=mission_profile.duration_seconds,
            f_min=f_min,
            f_max=f_max
        )
        return snr, spectrum.shock_time
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception(
            "Failed to compute SNR for %s=%s, %s=%s, T_star=%s, g_star=%s, v_wall=%s, "
            "mission_profile=%s, engine=%s, adiabatic_ratio=%s, f_min=%s, f_max=%s",
            "ubarf" if ubarf_rstar else "alpha", x,
            "r_star" if ubarf_rstar else "beta_over_H", y,
            T_star, g_star, v_wall, mission_profile, engine, adiabatic_ratio, f_min, f_max,
            exc_info=exc
        )
        return np.nan, np.nan
