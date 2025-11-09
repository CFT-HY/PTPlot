#!/usr/bin/env python3

"""Precomputation of the SNR curves

This file contains all the functions related to the computation of the signal-to-noise ratio
curves for the UbarfRstar and AlphaBeta plots. This is done first
so the plot can then be built in parts. Can be used as a standalone module.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015)

Contains the following function:
    * get_SNRcurve - calculates the SNR curves
"""

import math
import os
import sys

import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import snr
from ptplot.science.engine import Engine
from ptplot.science.parsing import PTPlotParser
from ptplot.science.spectrum.bpl import PowerSpectrumBPL
from ptplot.science.mission_profile import MissionProfile


def get_snr_curve(
        Tn: float,
        g_star: float,
        mission_profile: MissionProfile,
        ubarf_max: float = 1,
        engine: Engine = Engine.DEFAULT) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Calculate the SNR curves for the plots

    Parameters
    ----------
    Tn : float
        Temperature at nucleation time
    g_star : float
        Degrees of freedom
    mission_profile :
        Which sensitivity curve to use
    ubarf_max : float
        Maximum of rms fluid velocity (default to 1)

    Returns
    -------
    tshHn : np.ndarray
        Shocktimes
    snr : np.ndarray
        SNR values
    log10_r_star : np.ndarray
        Scanned values of log10(r_star)
    log10_Ubarf : np.ndarray
        Scanned values of log10(Ubarf)
    """

    # Values of log10(Ubarf) to scan
    log10_Ubarf: np.ndarray[int, np.float64] = np.linspace(-2, math.log10(ubarf_max), 51)

    # Values of log10(r_star) to scan
    log10_r_star: np.ndarray[int, np.float64] = np.linspace(-4, 0.08, 51)

    # Computation of SNR map as a function of GW amplitude and peak frequency
    snr_value = np.zeros((len(log10_r_star), len(log10_Ubarf)))
    tshHn = np.zeros((len(log10_r_star), len(log10_Ubarf)))

    for i in range(len(log10_r_star)):
        for j in range(len(log10_Ubarf)):
            Ubarf: float = 10.**log10_Ubarf[j]
            r_star: float = 10.**log10_r_star[i]

            ps = PowerSpectrumBPL(
                T_star=Tn,
                g_star=g_star,
                r_star=r_star,
                ubarf_in=Ubarf,
                engine=engine
            )
            OmGW0 = ps.power_spectrum(mission_profile.f)

            # Get shocktime (H_tsh = r_star/Ubarf)
            tshHn[i, j] = ps.get_shock_time()

            snr_value[i, j], frange = snr.stock_bkg_compute_snr(
                sens_freq=mission_profile.f,
                sens_omega=mission_profile.sensitivity,
                gw_freq=mission_profile.f,
                gw_omega=OmGW0,
                obs_time=mission_profile.duration_seconds,
                f_min=1.e-6,
                f_max=1.
            )

    return tshHn, snr_value, log10_r_star, log10_Ubarf


def main():
    parser = PTPlotParser(
        description="Computes signal-to-noise contour to a file.",
        vw_alpha_betaoverh=False,
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    tshHn, snr, log10HnRstar, log10Ubarf = get_snr_curve(
        Tn=args.Tstar, g_star=args.gstar, mission_profile=mission_profile, ubarf_max=1
    )

    # Use the mission profile to load the sensitivity curve name
    destination = f"{mission_profile.sensitivity_file_name}_Tn_{args.Tstar}_gstar_{args.gstar}_precomputed.npz"

    np.savez(
        destination,
        tshHn=tshHn,
        snr=snr,
        log10HnRstar=log10HnRstar,
        log10Ubarf=log10Ubarf
    )
    print("Wrote SNR contour to:", destination)


if __name__ == "__main__":
    main()
