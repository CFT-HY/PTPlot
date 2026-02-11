#!/usr/bin/env python3

"""AlphaBeta plotting

This file contains all the functions related to producing the AlphaBeta plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).
"""

import math
import os.path
import sys

from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ptplot.science import const
from ptplot.science.engine import Engine
from ptplot.science.espinosa import alpha_n_from_ubarf
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.utils import fig_to_svg
from ptplot.science.plot.snr import snr_figure
from ptplot.science.snr_grid import snr_grid
from ptplot.science.utils import atleast_2d, beta_from_R_star
import ptplot.science.type_hints as th


def snr_figure_alpha_beta(
        v_wall: float,
        alphas: th.FloatOrArrOrList1D2D = const.DEFAULT_ALPHA,
        beta_over_Hs: th.FloatOrArrOrList1D2D = 100,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        cs: float = const.CS0,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        engine: Engine = Engine.DEFAULT,
        huge_alpha: bool = False) -> Figure:
    r"""Produce the $\alpha,\beta$ plot

    :param v_wall: Wall velocity $v_\text{wall}$
    :param alphas: Phase transition strengths $\alpha$[scenario, point]
    :param beta_over_Hs: Inverse phase transition durations $\frac{\beta}{H}$[scenario, point]
    :param T_star: Transition temperature $T_*$
    :param g_star: Degrees of freedom $g_*$
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param labels: Labels for the points
    :param titles: Titles for the points
    :param mission_profile: Which sensitivity curve to use
    :param huge_alpha: Whether $\alpha$ is very large
    :return: Figure of $\alpha,\beta$
    """
    # Todo: do this with (alpha, beta)
    tshHn, snr, log10HnRstar, log10Ubarf = snr_grid(
        v_wall=v_wall,
        T_star=T_star,
        g_star=g_star,
        mission_profile=mission_profile,
        ubarf_max=0.866 if huge_alpha else 0.6,
        engine=engine
    )
    log10BetaOverH = np.log10(beta_from_R_star(R_star=10.**log10HnRstar, v_wall=v_wall))
    log10alpha = np.log10(alpha_n_from_ubarf(v_wall=v_wall, ubarf=10.**log10Ubarf, cs=cs, adiabatic_ratio=adiabatic_ratio))

    # Location of contour labels
    locs_tsh = np.array([
        (int(math.ceil(min(log10alpha))) + 0.2, x)
        for x in range(int(math.ceil(min(log10BetaOverH))), int(math.floor(max(log10BetaOverH)) + 1))
    ])
    fig, ax = snr_figure(
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

    # Iterate over scenarios
    for i, (BetaoverH_set, alpha_set) in enumerate(zip(beta_over_Hs, alphas)):
        alpha_log_set = np.log10(alpha_set)
        BetaOverH_log_set = np.log10(BetaoverH_set)

        # Plot points
        ax.plot(alpha_log_set, BetaOverH_log_set, ".")
        # Add labels to points
        if labels:
            label_set = labels[i]
            for x, y, label in zip(alpha_log_set, BetaOverH_log_set, label_set):
                ax.annotate(label, xy=(x, y), xycoords="data", xytext=(5, 0), textcoords="offset points")

    if titles:
        ax.legend([titles] if isinstance(titles, str) else titles, loc="lower left", framealpha=0.9)

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
    fig = snr_figure_alpha_beta(
        v_wall=args.vw, alphas=args.alpha, beta_over_Hs=args.BetaoverH,
        T_star=args.Tstar, g_star=args.gstar, mission_profile=mission_profile, engine=args.engine
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
