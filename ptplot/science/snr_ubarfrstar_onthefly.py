#!/usr/bin/env python3

"""Create the UbarfRstar plot

This file contains all the functions related to producing the UbarfRstar plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).

Contains the following function:
    * get_snr_image - creates the UbarfRstar plot
"""

import math
import os.path
import sys

from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot_utils import fig_to_svg
from ptplot.science.espinosa import ubarf
from ptplot.science.snr_onthefly import create_snr_figure
from ptplot.science.snr_precompute import get_snr_curve
import ptplot.science.type_hints as th
from ptplot.science.utils import atleast_2d

LOCS_TSH = np.array([(-1.8,-3.5), (-1.8,-2.5), (-1.8,-1.8), (-1.8,-0.5)])
TICKPOS_HUGE_ALPHA = np.array([-2, -1, 0, 1, 2, 3])


def get_snr_image(
        # Todo: Why are some of these defaults different to the ones in const.py?
        vws: th.FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR = 0.5,
        alphas: th.FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR = const.DEFAULT_ALPHA,
        beta_over_Hs: th.FLOAT_OR_LIST_OR_NESTED_LIST_OR_ARR = 100,
        T_star: float = 100,
        g_star: float = const.DEFAULT_G_STAR,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.STR_OR_LIST_OR_NESTED_LIST = None,
        titles: th.STR_OR_LIST = None,
        mission_profile: int = 0,
        usetex: bool = False,
        huge_alpha: bool = False,
        dbpl: bool = False,
        ssm: bool = False) -> Figure:
    """Produce the UbarfRstar plot

    Parameters
    ----------
    vws : list[float]
        List of wall velocities
    alphas : list[float]
        List of phase transition strengths
    beta_over_Hs : list[float]
        List of inverse phase transition durations
    T_star : float
        Transition temperature (default to 100)
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
        plot of UbarfRstar
    """
    tshHn, snr, log10HnRstar, log10Ubarf = get_snr_curve(
        Tn=T_star, g_star=g_star, mission_profile=mission_profile,
        ubarf_max=1000 if huge_alpha else 1
    )
    fig, ax = create_snr_figure(
        x=log10Ubarf,
        y=log10HnRstar,
        xlabel=r"$\overline{U}_{\rm f}$",
        ylabel=r"$H_{\rm n} R_* $",
        titles=titles,
        snr=snr,
        tshHn=tshHn,
        locs_tsh=LOCS_TSH,
        label_wanted_y=-2.5,
        huge_alpha=huge_alpha,
        xtickpos=TICKPOS_HUGE_ALPHA if huge_alpha else None,
        xticklabels=[r"$10^{-2}$", r"$10^{-1}$", r"$1$", r"$10$", r"$10^2$", r"$10^3$"] if huge_alpha else None
    )

    vws, alphas, beta_over_Hs = atleast_2d(vws, alphas, beta_over_Hs)
    if labels:
        if isinstance(labels, str):
            labels = [[labels]]
        elif isinstance(labels[0], str):
            labels = [labels]

    for i, (vw_set, BetaoverH_set, alpha_set) in enumerate(zip(vws, beta_over_Hs, alphas)):
        Rstar_set = [
            math.log10(math.pow(8.0*math.pi, 1.0/3.0) * vw / BetaoverH)
            for vw, BetaoverH in zip(vw_set, BetaoverH_set)
        ]
        ubarf_set = [
            math.log10(ubarf(vw, alpha, adiabatic_ratio))
            for vw, alpha in zip(vw_set, alpha_set)
        ]
        # Benchmarks
        ax.plot(ubarf_set, Rstar_set, ".")

        if labels:
            label_set = labels[i]
            for x, y, label in zip(ubarf_set, Rstar_set, label_set):
                ax.annotate(label, xy=(x, y), xycoords="data", xytext=(5, 0), textcoords="offset points")

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

    return fig


def main():
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        mission_profile=True
    )
    args = parser.parse_args()
    fig = get_snr_image(
        [args.vw], [args.alpha], [args.BetaoverH],
        args.Tstar, args.gstar, mission_profile=args.mission_profile)
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
