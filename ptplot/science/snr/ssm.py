"""SNR utilities for the Sound Shell Model."""

import numpy as np
from pttools.bubble import Bubble
from pttools.models import Model

from ptplot.science import const
from ptplot.science import type_hints as th
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM


def snr_column_ssm(
        x: th.FloatOrArr1D,
        y: th.FloatArr1D,
        v_wall: float ,
        T_star: float,
        g_star: float,
        ubarf_rstar: bool = False,
        adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
        model: Model = BAG,
        k_turb: float = const.DEFAULT_K_TURB,
        noise: Noise | None = None,
        zp: float = const.DEFAULT_ZP,
        parallel: bool = False) -> th.FloatArr2D:  # tuple[th.FloatArr1D, th.FloatArr1D]:
    """Compute a column of an SNR grid with the Sound Shell Model."""
    noise = resolve_noise(noise)
    x_value: float
    if isinstance(x, np.ndarray):
        if x.size != 1:
            raise ValueError(f"x (alpha_n or ubarf) must be a scalar. Got a {x.shape} array.")
        x_value = x.item()
    else:
        x_value = x

    alpha_n, _ubarf = PowerSpectrumSSM.validate_alpha_ubarf(
        alpha=None if ubarf_rstar else x_value,
        ubarf=x_value if ubarf_rstar else None,
        v_wall=v_wall,
        adiabatic_index=adiabatic_index,
        cs=const.CS0
    )
    bubble = Bubble(model=model, v_wall=v_wall, alpha_n=alpha_n)
    # snr = np.zeros_like(y)
    # shock_times = np.zeros_like(y)
    ret = np.empty((2, y.size))
    for i, y_i in enumerate(y):
        spectrum = PowerSpectrumSSM(
            alpha=None if ubarf_rstar else x_value,
            ubarf=x_value if ubarf_rstar else None,
            beta_over_H=None if ubarf_rstar else y_i,
            r_star=y_i if ubarf_rstar else None,
            T_star=T_star,
            g_star=g_star,
            v_wall=v_wall,
            adiabatic_index=adiabatic_index,
            zp=zp,
            k_turb=k_turb,
            model=model,
            bubble=bubble,
            parallel=parallel
        )
        # Error logging is handled in this function
        _power_spectrum, snr_i = spectrum.power_spectrum(noise.f, noise=noise, log_errors=False)
        # snr[i] = snr_i
        # shock_times[i] = spectrum.H_star_tau_nl
        ret[0, i] = snr_i
        ret[1, i] = spectrum.H_star_tau_nl
    # return snr, shock_times
    return ret
