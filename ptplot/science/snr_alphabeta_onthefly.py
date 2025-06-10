#!/usr/bin/env python3

"""Create the AlphaBeta plot

This file contains all the functions related to producing the AlphaBeta plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).

Contains the following function:
    * get_snr_alphabeta_image - creates the AlphaBeta plot
"""

import math
import os.path
import sys

from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const
from ptplot.science.espinosa import ubarf_to_alpha
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot_utils import fig_to_svg
from ptplot.science.powerspectrum import rstar_to_beta
from ptplot.science.snr_onthefly import create_snr_figure
from ptplot.science.snr_precompute import get_snr_curve
from ptplot.science.utils import atleast_2d
import ptplot.science.type_hints as th


def get_snr_alphabeta_image(
        vw: float,
        alphas: th.FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR = const.DEFAULT_ALPHA,
        beta_over_Hs: th.FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR = 100,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.STR_OR_LIST_OR_NESTED_LIST = None,
        titles: th.STR_OR_LIST = None,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        usetex: bool = False,
        huge_alpha: bool = False) -> Figure:
    """Produce the AlphaBeta plot

    Parameters
    ----------
    vw : float
        Wall velocity
    alphas : list[float]
        List of phase transition strengths
    beta_over_Hs : list[float]
        List of inverse phase transition durations
    T_star : float
        Transition temperature (default to 180)
    g_star : float
        Degrees of freedom (default to 100)
    adiabatic_ratio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    labels : list[string]
        List of labels
    titles : list[string]
        List of titles
    mission_profile : int
        Which sensitivity curve to use
    usetex : bool
        Flag for using latex (default to False)
    huge_alpha : bool
        Flag for if alpha is very large (default to False)

    Returns
    -------
    fig : Figure
        plot of AlphaBeta
    """
    tshHn, snr, log10HnRstar, log10Ubarf = get_snr_curve(
        Tn=T_star, g_star=g_star, mission_profile=mission_profile, ubarf_max=0.866 if huge_alpha else 0.6
    )
    log10BetaOverH = np.log10(rstar_to_beta(np.power(10.0, log10HnRstar), vw))
    log10alpha = np.log10(ubarf_to_alpha(vw, np.power(10.0, log10Ubarf), adiabatic_ratio))

    # Location of contour labels
    locs_tsh = np.array([
        (int(math.ceil(min(log10alpha))) + 0.2, x)
        for x in range(int(math.ceil(min(log10BetaOverH))), int(math.floor(max(log10BetaOverH)) + 1))
    ])
    fig, ax = create_snr_figure(
        x=log10alpha,
        y=log10BetaOverH,
        xlabel=r"$\alpha$",
        ylabel=r"$\beta/H_*$",
        titles=titles,
        snr=snr,
        tshHn=tshHn,
        locs_tsh=locs_tsh,
        label_wanted_y=2,
        huge_alpha=huge_alpha,
    )
    alphas, beta_over_Hs = atleast_2d(alphas, beta_over_Hs)
    if labels:
        if isinstance(labels, str):
            labels = [[labels]]
        elif isinstance(labels[0], str):
            labels = [labels]

    for i, (BetaoverH_set, alpha_set) in enumerate(zip(beta_over_Hs, alphas)):
        BetaOverH_log_set = [math.log10(BetaoverH) for BetaoverH in BetaoverH_set]

        alpha_log_set = [math.log10(alpha) for alpha in alpha_set]
        # Benchmarks
        ax.plot(alpha_log_set, BetaOverH_log_set, ".")

        if labels:
            label_set = labels[i]
            for x, y, label in zip(alpha_log_set, BetaOverH_log_set, label_set):
                ax.annotate(label, xy=(x, y), xycoords="data", xytext=(5, 0), textcoords="offset points")

    # Old attempts at getting the ticks in the right place
    # xtickpos = [min(log10alpha)] \
    #     + list(range(int(math.ceil(min(log10alpha))),
    #                  int(math.floor(max(log10alpha))+1))) \
    #     + [max(log10alpha)]
    # xticklabels = [r"$10^{%.2g}$" % min(log10alpha)] \
    #     + [r"$10^{%d}$" % ind
    #        for ind in list(range(int(math.ceil(min(log10alpha))),
    #                              int(math.floor(max(log10alpha))+1)))] \
    #     + [r"$10^{%.2g}$" % max(log10alpha)]

    # xtickpos = [-2, -1, 0, 1]
    # xticklabels = [ r"$10^{-2}$", r"$10^{-1}$", r"$10^{0}$", r"$10^{1}$"]
    # ytickpos = [min(log10BetaOverH)] \
    #     + list(range(int(math.ceil(min(log10BetaOverH))),
    #               int(math.floor(max(log10BetaOverH))+1))) \
    #     + [max(log10BetaOverH)]
    # yticklabels = [r"$10^{%.2g}$" % min(log10BetaOverH)] \
    #     + [r"$10^{%d}$" % ind
    #        for ind in list(range(int(math.ceil(min(log10BetaOverH))),
    #                              int(math.floor(max(log10BetaOverH))+1)))] \
    #     + [r"$10^{%.2g}$" % max(log10BetaOverH)]

    # ytickpos = [0, 1, 2, 3, 4]
    # yticklabels = [r"$10^{0}$", r"$10^{1}$", r"$10^{2}$", r"$10^{3}$", r"$10^{4}$"]

    # # Remove if too close together
    # if xtickpos[1]/xtickpos[0] < 3:
    #     xtickpos = xtickpos[1:]
    #     xticklabels = xticklabels[1:]

    return fig


def main():
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    fig = get_snr_alphabeta_image(
        vw=args.vw, alphas=args.alpha, beta_over_Hs=args.BetaoverH,
        T_star=args.Tstar, g_star=args.gstar, mission_profile=mission_profile
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
