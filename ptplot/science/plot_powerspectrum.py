#!/usr/bin/env python3

"""
Create the power spectrum plot

This file contains all the functions related to producing the power spectrum plot.

Contains the following functions:
    * get_ps_data - gets the data for the power spectrum plot and stores it
    * get_ps_image - creates the power spectrum plot
"""

import math
import os.path
import sys
import time

import matplotlib
from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const, snr
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot_utils import fig_to_svg
from ptplot.science.powerspectrum import PowerSpectrum
# from ptplot.science.powerspectrum_dbpl import PowerSpectrumDBPL
# from ptplot.science.powerspectrum_ssm import PowerSpectrumSSM
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile

matplotlib.use("Agg")



def get_ps_data(
        vw: float = const.DEFAULT_VW,
        alpha: float = const.DEFAULT_ALPHA,
        beta_over_H: float = const.DEFAULT_BETA_OVER_H,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        sw_only: bool = True) -> str:
    """Retrieve the data for the power spectrum plot

    Note that this is not then used to create the plot, this stores the data,
    to be exported as a csv if requested.

    Parameters
    ----------
    vw : float
        Wall velocity (default to 0.9)
    T_star : float
        Transition temperature (default to 180)
    g_star : float
        Degrees of freedom (default to 100)
    alpha : float
        Phase transition strength (default to 0.1)
    beta_over_H : float
        Inverse phase transition duration relative to H (default to 10)
    adiabatic_ratio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    mission_profile : int
        Which sensitivity curve to use
    sw_only : bool
        Flag to decide if we want to ignore turbulence (default to True)

    Returns
    -------
    res : string
        String containing all the data to reproduce the power spectrum plot
    """
    curves_ps = PowerSpectrum(
        vw=vw,
        T_star=T_star,
        alpha=alpha,
        beta_over_H=beta_over_H,
        g_star=g_star,
        adiabatic_ratio=adiabatic_ratio
    )

    res = ""
    if sw_only:
        res = res + "f, omegaSens, omegaSW\n"
    else:
        res = res + "f, omegaSens, omegaSW, omegaTurb, omegaTot\n"

    for x,y in zip(mission_profile.f, mission_profile.sensitivity):
        if sw_only:
            res = res + "%g, %g, %g\n" % (x, y, curves_ps.power_spectrum_sw_conservative(x))
        else:
            res = res + "%g, %g, %g, %g, %g\n" % (
                x, y,
                curves_ps.power_spectrum_sw_conservative(x),
                curves_ps.power_spectrum_turb(x),
                curves_ps.power_spectrum_conservative(x)
            )

    return res


def get_ps_image(
        vw: float = const.DEFAULT_VW,
        alpha: float = const.DEFAULT_ALPHA,
        beta_over_H: float = const.DEFAULT_BETA_OVER_H,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        usetex: bool = False,
        sw_only: bool = True) -> Figure:
    """Produce the power spectrum plot

    Parameters
    ----------
    vw : float
        Wall velocity (default to 0.9)
    T_star : float
        Transition temperature (default to 180)
    g_star : float
        Degrees of freedom (default to 100)
    alpha : float
        Phase transition strength (default to 0.1)
    beta_over_H : float
        Inverse phase transition duration relative to H (default to 10)
    adiabatic_ratio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    mission_profile : int
        Which sensitivity curve to use
    usetex : bool
        Flag for using latex (default to False)
    sw_only : bool
        Flag to decide if we want to ignore turbulence (default to True)

    Returns
    -------
    sio : Figure
        plot of the power spectrum
    """
    curves_ps = PowerSpectrum(
        vw=vw,
        T_star=T_star,
        alpha=alpha,
        beta_over_H=beta_over_H,
        g_star=g_star,
        adiabatic_ratio=adiabatic_ratio
    )

    # Uncomment to set up latex plotting
    # matplotlib.rc("text", usetex=usetex)
    matplotlib.rc("font", family="serif")
    matplotlib.rc("mathtext", fontset="dejavuserif")
    # Uncomment to make font size bigger
    # matplotlib.rcParams.update({"font.size": 16})
    # Uncomment to make legend smaller
    # matplotlib.rcParams.update({"legend.fontsize": 14})

    f_more = np.logspace(math.log(min(mission_profile.f)), math.log(max(mission_profile.f)), num=len(mission_profile.f)*10)

    fig = Figure()
    ax = fig.add_subplot(111)

    snr_value, frange = snr.stock_bkg_compute_snr(
        SensFr=mission_profile.f,
        SensOm=mission_profile.sensitivity,
        GWFr= mission_profile.f,
        GWOm=curves_ps.power_spectrum_sw_conservative(mission_profile.f),
        Tobs=mission_profile.duration_seconds,
        fmin=1.e-6,
        fmax=1
    )
    ax.fill_between(mission_profile.f, mission_profile.sensitivity, 1, alpha=0.3, label=r"LISA sensitivity")

    if sw_only:
        ax.plot(
            f_more, curves_ps.power_spectrum_sw_conservative(f_more), "k",
            label=r"$\Omega_\mathrm{sw}$")
    else:
        ax.plot(
            f_more, curves_ps.power_spectrum_sw_conservative(f_more), "r",
            label=r"$\Omega_\mathrm{sw}$")
        ax.plot(
            f_more, curves_ps.power_spectrum_turb(f_more), "b",
            label=r"$\Omega_\mathrm{turb}$")
        ax.plot(
            f_more, curves_ps.power_spectrum_conservative(f_more), "k",
            label=r"Total")

    ax.set_xlabel(r"$f\; \mathrm{(Hz)}$", fontsize=14)
    ax.set_ylabel(r"$h^2 \, \Omega_\mathrm{GW}(f)$", fontsize=14)
    ax.set_xlim(1e-5, 0.1)
    ax.set_ylim(1e-16, 1e-8)
    ax.set_yscale("log", nonpositive="clip")
    ax.set_xscale("log", nonpositive="clip")
    ax.legend(loc="upper right")

    # July 2023: No longer watermark with LISACosWG
    # # position bottom right
    # fig.text(0.95, 0.05, "LISACosWG",
    #          fontsize=50, color="gray",
    #          ha="right", va="bottom", alpha=0.4)

    # position top left
    fig.text(
        0.13, 0.87,
        r"%s [$\mathrm{SNR}_\mathrm{sw} = %g$]" % (time.asctime(), snr_value),
        fontsize=8, color="black",
        ha="left", va="top", alpha=1.0
    )
    return fig


def main():
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        methods=True
    )
    args = parser.parse_args()
    fig = get_ps_image(
        vw=args.vw, alpha=args.alpha, beta_over_H=args.BetaoverH,
        T_star=args.Tstar, g_star=args.gstar,
        # ssm=args.ssm, dbpl=args.dbpl
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
