#!/usr/bin/env python3

"""Precomputation of the SNR curves

This file contains all the functions related to the computation of the signal-to-noise ratio
curves for the UbarfRstar and AlphaBeta plots. This is done first
so the plot can then be built in parts. Can be used as a standalone module.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015)
"""

import os
import sys

import numpy as np
from pttools.omgw0 import signal_to_noise_ratio

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const
from ptplot.science.engine import Engine
from ptplot.science.parsing import PTPlotParser
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.mission_profile import MissionProfile
import ptplot.science.type_hints as th


def snr_grid_alpha_beta(
        T_star: float,
        g_star: float,
        v_wall: float,
        mission_profile: MissionProfile,
        alpha_n: th.FloatArr1D = const.DEFAULT_ALPHA_N_RANGE,
        beta_over_H: th.FloatArr1D = const.DEFAULT_BETA_OVER_H_RANGE,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        engine: Engine = Engine.DEFAULT,
        f_min: float = const.DEFAULT_SNR_F_MIN,
        f_max: float = const.DEFAULT_SNR_F_MAX) -> tuple[th.FloatArr2D, th.FloatArr2D, th.FloatArr1D, th.FloatArr1D]:
    r"""Calculate SNR for a grid of $(\alpha_n, \beta/H)$ points

    :param v_wall: Wall velocity $v_\text{wall}$
    :param T_star: Temperature $T_*$ at which the GWs were produced
    :param g_star: Degrees of freedom $g_*$
    :param mission_profile: Which sensitivity curve to use
    :param alpha_n: Range of $\alpha_n$ values
    :param beta_over_H: Range of $\beta/H$ values
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param engine: Which power spectrum engine to use
    :param f_min: Minimum frequency to consider for SNR calculation
    :param f_max: Maximum frequency to consider for SNR calculation
    :return: SNR values, shock times, ubarf, r_star
    """
    if not np.isfinite(T_star):
        raise ValueError(f"Invalid T_star={T_star}")
    if not np.isfinite(g_star):
        raise ValueError(f"Invalid g_star={g_star}")
    if not np.isfinite(v_wall):
        raise ValueError(f"Invalid v_wall={v_wall}")
    if not np.isfinite(alpha_n).all():
        raise ValueError(f"Invalid alpha_n={alpha_n}")
    if not np.isfinite(beta_over_H).all():
        raise ValueError(f"Invalid beta_over_H={beta_over_H}")

    snr = np.zeros((beta_over_H.size, alpha_n.size))
    shock_times = np.zeros_like(snr)

    for i in range(beta_over_H.size):
        for j in range(alpha_n.size):
            try:
                spectrum = power_spectrum(
                    T_star=T_star,
                    g_star=g_star,
                    vw=v_wall,
                    alpha=alpha_n[j],
                    beta_over_H=beta_over_H[i],
                    adiabatic_ratio = adiabatic_ratio,
                    engine=engine
                )
            except (RuntimeError, ValueError):
                snr[i, j] = np.nan
                shock_times[i, j] = np.nan
                continue

            shock_times[i, j] = spectrum.shock_time
            snr[i, j] = signal_to_noise_ratio(
                f=mission_profile.f,
                signal=spectrum.power_spectrum(mission_profile.f),
                f_noise=mission_profile.f,
                noise=mission_profile.sensitivity,
                obs_time=mission_profile.duration_seconds,
                f_min=f_min,
                f_max=f_max
            )

    return snr, shock_times, alpha_n, beta_over_H


def snr_grid_ubarf_rstar(
        v_wall: float,
        T_star: float,
        g_star: float,
        mission_profile: MissionProfile,
        ubarf: th.FloatArr1D = const.DEFAULT_UBARF_RANGE,
        r_star: th.FloatArr1D = const.DEFAULT_R_STAR_RANGE,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        engine: Engine = Engine.DEFAULT,
        f_min: float = const.DEFAULT_SNR_F_MIN,
        f_max: float = const.DEFAULT_SNR_F_MAX) -> tuple[th.FloatArr2D, th.FloatArr2D, th.FloatArr1D, th.FloatArr1D]:
    r"""Calculate SNR for a grid of $(\bar{U}_f, r_*)$ points

    :param v_wall: Wall velocity $v_\text{wall}$
    :param T_star: Temperature $T_*$ at which the GWs were produced
    :param g_star: Degrees of freedom $g_*$
    :param mission_profile: Which sensitivity curve to use
    :param ubarf: Range of $\bar{U}_f$ values
    :param r_star: Range of $r_*$ values
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param engine: Which power spectrum engine to use
    :param f_min: Minimum frequency to consider for SNR calculation
    :param f_max: Maximum frequency to consider for SNR calculation
    :return: SNR values, shock times, ubarf, r_star
    """
    snr = np.zeros((r_star.size, ubarf.size))
    shock_times = np.zeros_like(snr)

    for i in range(r_star.size):
        for j in range(ubarf.size):
            # try:
            spectrum = power_spectrum(
                T_star=T_star,
                g_star=g_star,
                vw=v_wall,
                adiabatic_ratio=adiabatic_ratio,
                r_star=r_star[i],
                ubarf=ubarf[j],
                engine=engine
            )
            # except (RuntimeError, ValueError):
            #     shock_times[i, j] = np.nan
            #     snr[i, j] = np.nan
            #     continue

            shock_times[i, j] = spectrum.shock_time
            snr[i, j] = signal_to_noise_ratio(
                f=mission_profile.f,
                signal=spectrum.power_spectrum(mission_profile.f),
                f_noise=mission_profile.f,
                noise=mission_profile.sensitivity,
                obs_time=mission_profile.duration_seconds,
                f_min=f_min,
                f_max=f_max
            )

    return snr, shock_times, ubarf, r_star


def main():
    # Todo: enable the v_wall argument
    parser = PTPlotParser(
        description="Computes signal-to-noise contour to a file.",
        vw_alpha_betaoverh=False,
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    tshHn, snr, log10_r_star, log10_ubarf = snr_grid_ubarf_rstar(
        v_wall=args.v_wall, T_star=args.Tstar, g_star=args.gstar, mission_profile=mission_profile, ubarf_max=1
    )

    # Use the mission profile to load the sensitivity curve name
    destination = f"{mission_profile.sensitivity_file_name}_Tn_{args.Tstar}_gstar_{args.gstar}_precomputed.npz"

    np.savez(
        destination,
        tshHn=tshHn,
        snr=snr,
        log10HnRstar=log10_r_star,
        log10Ubarf=log10_ubarf
    )
    print("Wrote SNR contour to:", destination)


if __name__ == "__main__":
    main()
