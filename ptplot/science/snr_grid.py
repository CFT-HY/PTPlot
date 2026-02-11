#!/usr/bin/env python3

"""Precomputation of the SNR curves

This file contains all the functions related to the computation of the signal-to-noise ratio
curves for the UbarfRstar and AlphaBeta plots. This is done first
so the plot can then be built in parts. Can be used as a standalone module.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015)
"""

import math
import os
import sys

import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const
from ptplot.science.snr import stock_bkg_compute_snr
from ptplot.science.engine import Engine
# from ptplot.science.espinosa import alpha_n_from_ubarf
from ptplot.science.parsing import PTPlotParser
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.mission_profile import MissionProfile
import ptplot.science.type_hints as th


def snr_grid(
        v_wall: float,
        T_star: float,
        g_star: float,
        mission_profile: MissionProfile,
        alpha: th.FloatArr1D | None = None,
        ubarf_max: float = 1,
        n_ubarf: int = 51,
        n_r_star: int = 51,
        cs: float = const.CS0,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        engine: Engine = Engine.DEFAULT) -> tuple[th.FloatArr2D, th.FloatArr2D, th.FloatArr1D, th.FloatArr1D]:
    """Calculate the SNR curves for the plots

    :param v_wall: Wall velocity $v_\text{wall}$
    :param T_star: Temperature $T_*$ at which the GWs were produced
    :param g_star: Degrees of freedom $g_*$
    :param mission_profile: Which sensitivity curve to use
    :param alpha: Phase transition strength $\alpha$ for each $\bar{U}_f$.
      If None, it will be calculated from $\bar{U}_f$.
    :param ubarf_max: Maximum RMS fluid velocity $\bar{U}_f$
    :return: tshHn (shock times, 2D array),
      snr (SNR values, 2D array),
      log10_r_star (Scanned values of log10(r_star),
      log10_ubarf (scanned values of log10(ubarf)
    """

    log10_ubarf = np.linspace(-2, math.log10(ubarf_max), n_ubarf)
    log10_r_star = np.linspace(-4, 0.08, n_r_star)

    # if alpha is None:
        # alpha = alpha_n_from_ubarf(v_wall=v_wall, ubarf=10.**log10_ubarf, cs=cs, adiabatic_ratio=adiabatic_ratio)

    # Computation of SNR map as a function of GW amplitude and peak frequency
    snr_values = np.zeros((len(log10_r_star), len(log10_ubarf)))
    tshHn = np.zeros_like(snr_values)

    for i in range(len(log10_r_star)):
        for j in range(len(log10_ubarf)):
            try:
                spectrum = power_spectrum(
                    T_star=T_star,
                    g_star=g_star,
                    vw=v_wall,
                    # alpha=alpha[j],
                    r_star=10.**log10_r_star[i],
                    ubarf_in=10.**log10_ubarf[j],
                    engine=engine
                )
            except (RuntimeError, ValueError):
                tshHn[i, j] = np.nan
                snr_values[i, j] = np.nan
                continue

            # Get shocktime (H_tsh = r_star/ubarf)
            tshHn[i, j] = spectrum.shock_time

            snr_values[i, j], f_range = stock_bkg_compute_snr(
                sens_freq=mission_profile.f,
                sens_omega=mission_profile.sensitivity,
                gw_freq=mission_profile.f,
                gw_omega=spectrum.power_spectrum(mission_profile.f),
                obs_time=mission_profile.duration_seconds,
                f_min=1.e-6,
                f_max=1.
            )

    return tshHn, snr_values, log10_r_star, log10_ubarf


def main():
    # Todo: enable the v_wall argument
    parser = PTPlotParser(
        description="Computes signal-to-noise contour to a file.",
        vw_alpha_betaoverh=False,
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    tshHn, snr, log10_r_star, log10_ubarf = snr_grid(
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
