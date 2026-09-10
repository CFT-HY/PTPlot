"""Signal-to-noise ratio calculations for gravitational wave spectra."""

import logging
import typing as tp

import numpy as np

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.spectrum.engine import Engine

logger = logging.getLogger(__name__)


def snr_point(
        x: float,
        y: float,
        T_star: float,
        g_star: float,
        v_wall: float,
        noise: Noise | None,
        engine: Engine,
        adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
        ubarf_rstar: bool = False,
        parallel: bool = True) -> tuple[float, float]:
    """Compute the SNR value of a single point in the parameter space."""
    noise = resolve_noise(noise)
    kwargs: dict[str, tp.Any] = {"ubarf": x, "r_star": y} if ubarf_rstar \
        else {"alpha": x, "beta_over_H": y}
    try:
        spectrum = power_spectrum(
            T_star=T_star,
            g_star=g_star,
            v_wall=v_wall,
            adiabatic_index=adiabatic_index,
            engine=engine,
            parallel=parallel,
            **kwargs
        )
        # Error logging is handled in this function
        _power_spectrum, snr = spectrum.power_spectrum(noise.f, noise=noise, log_errors=False)
        return snr, spectrum.H_star_tau_nl
    except Exception as exc:
        logger.exception(
            "Failed to compute SNR for %s=%s, %s=%s, T_star=%s, g_star=%s, v_wall=%s, "
            "noise=%s, engine=%s, adiabatic_index=%s",
            "ubarf" if ubarf_rstar else "alpha", x,
            "r_star" if ubarf_rstar else "beta_over_H", y,
            T_star, g_star, v_wall, noise, engine, adiabatic_index,
            exc_info=exc
        )
        return np.nan, np.nan
