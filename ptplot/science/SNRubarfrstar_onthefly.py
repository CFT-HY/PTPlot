#!/usr/bin/env python3

"""Create the UbarfRstar plot

This file contains all the functions related to producing the UbarfRstar plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).

Contains the following function:
    * get_SNR_image - creates the UbarfRstar plot
"""

import math
import os.path
import sys
import time
import typing as tp

import matplotlib
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot_utils import fig_to_svg, make_minor_ticks
from ptplot.science.espinosa import ubarf
from ptplot.science.SNR_precompute import get_SNRcurve

matplotlib.use("Agg")


def get_SNR_image(
        # Todo: Why are some of these defaults different to the ones in const.py?
        # Todo: Fix types for vw_list, alpha_list and BetaoverH_list
        vw_list: tp.List[float] = [[0.5]],
        alpha_list: tp.List[float] = [[const.DEFAULT_ALPHA]],
        beta_over_H_list: tp.List[float] = [[100]],
        T_star: float = 100,
        g_star: float = const.DEFAULT_G_STAR,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        label_list: tp.List[str] = None,
        title_list: tp.List[str] = None,
        mission_profile: int = 0,
        usetex: bool = False,
        huge_alpha: bool = False,
        dbpl: bool = False,
        ssm: bool = False) -> Figure:
    """Produce the UbarfRstar plot

    Parameters
    ----------
    vw_list : list[float]
        List of wall velocities
    alpha_list : list[float]
        List of phase transition strengths
    beta_over_H_list : list[float]
        List of inverse phase transition durations
    T_star : float
        Transition temperature (default to 100)
    g_star : float
        Degrees of freedom (default to 100)
    adiabatic_ratio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    label_list : list[string]
        List of labels
    title_list : list[string]
        List of titles
    mission_profile : int
        Which sensitivity curve to use
    usetex : bool
        Flag for using latex (default to False)
    huge_alpha : bool
        Flag for if alpha is very large (default to False)

    Returns
    -------
    sio : Figure
        plot of UbarfRstar
    """

    color_tuple = plt.cm.plasma_r(np.linspace(0.1, 1, 6))

    # matplotlib.rc("text", usetex=usetex)
    matplotlib.rc("font", family="serif")
    matplotlib.rc("mathtext", fontset="dejavuserif")

    if huge_alpha:
        ubarfmax = 1000
    else:
        ubarfmax = 1

    tshHn, snr, log10HnRstar, log10Ubarf = get_SNRcurve(T_star, g_star, mission_profile, ubarfmax)

    levels = np.array([1,5,10,20,50,100])
    levels_tsh = np.array([0.001,0.01,0.1,1,10,100])
    # Only if hugeAlpha in play
    levels_tsh_hugeAlpha = np.array([0.0000001,0.000001,0.00001,0.0001])

    # Where to put contour label, based on y-coordinate and contour value
    def find_place(snr, wantedy, wantedcontour):
        nearesty = (np.abs(log10HnRstar-wantedy)).argmin()
        nearestx = (np.abs(snr[nearesty,:]-wantedcontour)).argmin()

        return (log10Ubarf[nearestx],wantedy)

    # Location of contour labels
    locs = [find_place(snr, -2.5, wantedcontour) for wantedcontour in levels]
    locs_tsh = [(-1.8,-3.5), (-1.8,-2.5), (-1.8,-1.8), (-1.8,-0.5)]

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)

    CS = ax.contour(log10Ubarf, log10HnRstar, snr, levels, linewidths=1,
                    colors=color_tuple,
                     extent=(log10Ubarf[0], log10Ubarf[-1],
                             log10HnRstar[0], log10HnRstar[-1]))
    CStsh = ax.contour(log10Ubarf, log10HnRstar, tshHn, levels_tsh, linewidths=1,
                       linestyles="dashed", colors="k",
                       extent=(log10Ubarf[0], log10Ubarf[-1],
                               log10HnRstar[0], log10HnRstar[-1]))

    if huge_alpha:
        # These don"t get annotated with labels
        CStsh_hugeAlpha = ax.contour(log10Ubarf, log10HnRstar, tshHn, levels_tsh_hugeAlpha, linewidths=1,
                                     linestyles="dashed", colors="k",
                                     extent=(log10Ubarf[0], log10Ubarf[-1],
                                             log10HnRstar[0], log10HnRstar[-1]))

    # CSturb = ax.contourf(log10Ubarf, log10HnRstar, tshHn, [0.00001, 1], colors=("gray"), alpha=0.3,
    CSturb = ax.contourf(log10Ubarf, log10HnRstar, tshHn, [0.0001, 1],
                         colors=("white"), alpha=0.2, hatches="x",
                         extent=(log10Ubarf[0], log10Ubarf[-1],
                                 log10HnRstar[0], log10HnRstar[-1]))

    ax.clabel(CS, inline=1, fontsize=8, fmt="%.0f", manual=locs)
    ax.clabel(CStsh, inline=1, fontsize=8, fmt="%g", manual=locs_tsh)
    # plt.title(r"SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs")
    # plt.xlabel(r"$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $",fontsize=16)
    ax.set_ylabel(r"$H_{\rm n} R_* $", fontsize=14)
    ax.set_xlabel(r"$\overline{U}_{\rm f}$", fontsize=14)
    ax.set_xlim(min(log10Ubarf),max(log10Ubarf))
    ax.set_ylim(min(log10HnRstar),max(log10HnRstar))

    for i, (vw_set, BetaoverH_set, alpha_set) in enumerate(zip(vw_list, beta_over_H_list, alpha_list)):
        Rstar_set = [
            math.log10(math.pow(8.0*math.pi, 1.0/3.0) * vw / BetaoverH)
            for vw, BetaoverH in zip(vw_set, BetaoverH_set)
        ]
        ubarf_set = [
            math.log10(ubarf(vw, alpha, adiabatic_ratio))
            for vw, alpha in zip(vw_set, alpha_set)
        ]
        benchmarks = ax.plot(ubarf_set, Rstar_set, ".")

        if label_list:
            label_set = label_list[i]
            for x,y,label in zip(ubarf_set, Rstar_set, label_set):
                ax.annotate(label, xy=(x,y), xycoords="data", xytext=(5,0),
                            textcoords="offset points")

    if title_list:
        legends = title_list
        ax.legend(legends, loc="lower left", framealpha=0.9)

    # Old attempts at getting the ticks in the right place
    # xtickpos = [min(log10Ubarf)] \
    #     + list(range(int(round(min(log10Ubarf))),
    #                  int(round(max(log10Ubarf))+1))) \
    #     + [max(log10Ubarf)]
    # xticklabels = [r"$10^{%.2g}$" % min(log10Ubarf)] \
    #     + [r"$10^{%d}$" % ind
    #        for ind in list(range(int(round(min(log10Ubarf))),
    #                              int(round(max(log10Ubarf))+1)))] \
    #     + [r"$10^{%.2g}$" % max(log10Ubarf)]

    # ytickpos = [min(log10HnRstar)] \
    #     + list(range(int(math.ceil(min(log10HnRstar))),
    #                  int(round(max(log10HnRstar))+1))) \
    #     + [max(log10HnRstar)]
    # yticklabels = [r"$10^{%.2g}$" % min(log10HnRstar)] \
    #     + [r"$10^{%d}$" % ind
    #        for ind in list(range(int(math.ceil(min(log10HnRstar))),
    #                              int(round(max(log10HnRstar))+1)))] \
    #     + [r"$10^{%.2g}$" % max(log10HnRstar)]

    if huge_alpha:
        xtickpos = [-2, -1, 0, 1, 2, 3]
        xticklabels = [ r"$10^{-2}$", r"$10^{-1}$", r"$1$",
                        r"$10$", r"$10^2$", r"$10^3$"]
    else:
        xtickpos = list(range(int(math.ceil(min(log10Ubarf))),
                    int(math.floor(max(log10Ubarf))+1)))
        xticklabels = [r"$10^{%d}$" % ind
                for ind in list(range(int(math.ceil(min(log10Ubarf))),
                                        int(math.floor(max(log10Ubarf))+1)))]

    ytickpos = list(range(int(math.ceil(min(log10HnRstar))),
                        int(math.floor(max(log10HnRstar))+1)))
    yticklabels = [r"$10^{%d}$" % ind
                    for ind in list(
                            range(int(math.ceil(min(log10HnRstar))),
                                    int(math.floor(max(log10HnRstar))+1)))]

    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.set_xticks(
        ticks=make_minor_ticks(
            int(math.ceil(min(log10Ubarf))),
            int(math.floor(max(log10Ubarf)))
        ),
        minor=True
    )
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)
    ax.set_yticks(
        ticks=make_minor_ticks(
            int(math.ceil(min(log10HnRstar))),
            int(math.floor(max(log10HnRstar)))
        ),
        minor=True
    )

    # July 2023: No longer watermark with LISACosWG
    # # position bottom right
    # fig.text(0.95, 0.05, "LISACosWG",
    #          fontsize=50, color="gray",
    #          ha="right", va="bottom", alpha=0.4)

    # position top left
    fig.text(
        0.13, 0.87, time.asctime(),
        fontsize=8, color="black",
        ha="left", va="top", alpha=1.0
    )
    return fig


def main():
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        mission_profile=True
    )
    args = parser.parse_args()
    fig = get_SNR_image(
        [args.vw], [args.alpha], [args.BetaoverH],
        args.Tstar, args.gstar, mission_profile=args.mission_profile)
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
