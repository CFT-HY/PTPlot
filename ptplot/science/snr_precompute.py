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
import typing as tp

import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import snr
from ptplot.science.parsing import PTPlotParser
from ptplot.science.powerspectrum import PowerSpectrum
from ptplot.science.mission_profile import MISSION_PROFILES, MissionProfile


def get_snr_curve(
        Tn: float,
        g_star: float,
        mission_profile: MissionProfile,
        ubarf_max: float = 1) -> tp.Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Calculate the SNR curves for the plots

    Parameters
    ----------
    Tn : float
        Temperature at nucleation time
    g_star : float
        Degrees of freedom
    mission_profile : int
        Which sensitivity curve to use
    ubarf_max : float
        Maximum of rms fluid velocity (default to 1)

    Returns
    -------
    tshHn : np.ndarray
        Shocktimes
    snr : np.ndarray
        SNR values
    log10HnRstar : np.ndarray
        Scanned values of log10(HnRstar)
    log10Ubarf : np.ndarray
        Scanned values of log10(Ubarf)
    """

    # Values of log10(Ubarf) to scan
    log10Ubarf = np.linspace(-2, math.log10(ubarf_max), 51)

    # Values of log10(HnRstar) to scan
    log10HnRstar = np.linspace(-4, 0.08, 51)

    # Computation of SNR map as a function of GW amplitude and peak frequency
    snr_value = np.zeros((len(log10HnRstar), len(log10Ubarf)))
    tshHn = np.zeros((len(log10HnRstar), len(log10Ubarf)))

    for i in range(len(log10HnRstar)):
        for j in range(len(log10Ubarf)):
            Ubarf = 10.**log10Ubarf[j]
            HnRstar = 10.**log10HnRstar[i]

            ps = PowerSpectrum(
                T_star=Tn,
                g_star=g_star,
                H_rstar=HnRstar,
                ubarf_in=Ubarf
            )
            OmGW0 = ps.power_spectrum_sw_conservative(mission_profile.f)

            # Get shocktime (H_tsh = HnRstar/Ubarf)
            tshHn[i, j] = ps.get_shock_time()

            snr_value[i, j], frange = snr.stock_bkg_compute_snr(
                SensFr=mission_profile.f,
                SensOm=mission_profile.sensitivity,
                GWFr=mission_profile.f,
                GWOm=OmGW0,
                Tobs=mission_profile.duration_seconds,
                fmin=1.e-6,
                fmax=1.
            )

    return tshHn, snr_value, log10HnRstar, log10Ubarf


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
