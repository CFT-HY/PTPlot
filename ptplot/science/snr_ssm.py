"""SNR utilities for the Sound Shell Model."""

import numpy as np
from pttools.bubble import Bubble
from pttools.models import Model
from pttools.omgw0 import signal_to_noise_ratio

from ptplot.science import const
from ptplot.science import type_hints as th
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
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
        f_min: float = const.DEFAULT_SNR_F_MIN,
        f_max: float = const.DEFAULT_SNR_F_MAX,
        k_turb: float = const.DEFAULT_K_TURB,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        zp: float = const.DEFAULT_ZP,
        parallel: bool = False) -> th.FloatArr2D:  # tuple[th.FloatArr1D, th.FloatArr1D]:
    """Compute a column of an SNR grid with the Sound Shell Model."""
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
        snr_i, f_min, f_max = signal_to_noise_ratio(
            f=mission_profile.f,
            # Error logging is handled in this function
            signal=spectrum.power_spectrum(mission_profile.f, log_errors=False),
            f_noise=mission_profile.f,
            noise=mission_profile.sensitivity,
            obs_time=mission_profile.duration_seconds,
            f_min=f_min,
            f_max=f_max
        )
        # snr[i] = snr_i
        # shock_times[i] = spectrum.shock_time
        ret[0, i] = snr_i
        ret[1, i] = spectrum.shock_time
    # return snr, shock_times
    return ret
