#!/usr/bin/env python3

"""Create the $\bar{U}_f-R_*$ plot

This file contains all the functions related to producing the $\bar{U}_f-R_*$ plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).
"""

import os.path
import sys

from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ptplot.science import const
from ptplot.science.engine import Engine
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.utils import fig_to_svg
from ptplot.science.espinosa import ubarf as ubarf_func
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.plot.snr import snr_figure
from ptplot.science.snr_grid import snr_grid_ubarf_rstar
import ptplot.science.type_hints as th
from ptplot.science.utils import atleast_2d, R_star


def snr_figure_ubarf_rstar(
        v_wall_snr: float,
        T_star_snr: float,
        g_star_snr: float,
        alphas: th.FloatOrArrOrListOfArr1D,
        beta_over_Hs: th.FloatOrArrOrListOfArr1D,
        v_walls: th.FloatOrArrOrListOfArr1D,
        cs: float = const.CS0,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        huge_alpha: bool = False,
        engine: Engine = Engine.DEFAULT) -> Figure:
    r"""Produce the $(\bar{U}_f, r_*)$ plot

    :param v_wall_snr: Wall velocity used for the SNR curves
    :param T_star_snr: Transition temperature $T_*$ used for the SNR curves
    :param g_star_snr: Degrees of freedom $g_*$ used for the SNR curves
    :param v_walls: Wall velocities $v_\text{wall}$[scenario, point]
    :param alphas: Phase transition strengths $\alpha$[scenario, point]
    :param beta_over_Hs: Inverse phase transition durations $\frac{\beta}{H}$[scenario, point]
    :param cs: Sound speed $c_s$
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param labels: Labels for [scenario, point]
    :param titles: Titles for the scenarios
    :param mission_profile: Which sensitivity curve to use
    :param huge_alpha: Whether $\alpha$ is very large
    :param engine: Which power spectrum engine to use
    :return: SNR figure of $(\bar{U}_f, r_*)$
    """
    if v_walls is None:
        v_walls = v_wall_snr

    ubarf = np.logspace(const.DEFAULT_UBARF_RANGE[0], 1000, const.DEFAULT_UBARF_RANGE.size) \
            if huge_alpha else const.DEFAULT_UBARF_RANGE
    r_star = const.DEFAULT_R_STAR_RANGE
    snr, shock_times = snr_grid_ubarf_rstar(
        v_wall=v_wall_snr,
        T_star=T_star_snr,
        g_star=g_star_snr,
        mission_profile=mission_profile,
        ubarf=ubarf,
        r_star=r_star,
        engine=engine
    )
    log10_ubarf = np.log10(ubarf)
    log10_r_star = np.log10(r_star)
    ubarf_mid = (log10_ubarf[0] + log10_ubarf[-1]) / 2
    fig, ax = snr_figure(
        x=np.log10(ubarf),
        y=np.log10(r_star),
        xlabel=r"$\overline{U}_{\rm f}$",
        ylabel=r"$H_{\rm n} R_*$",
        titles=titles,
        snr=snr,
        shock_times=shock_times,
        shock_label_locs=np.array([
            (ubarf_mid + 0.2 - 0.2 * i, y)
            for i, y in enumerate(range(int(log10_r_star[0]), int(log10_r_star[-1]) + 1))
        ]),
        label_wanted_y=-2.5,
        huge_alpha=huge_alpha,
    )

    # Ensure that input values are 2D arrays
    v_walls, alphas, beta_over_Hs = atleast_2d(v_walls, alphas, beta_over_Hs)
    if labels:
        if isinstance(labels, str):
            labels = [[labels]]
        elif isinstance(labels[0], str):
            labels = [labels]

    # Iterate over scenarios
    for i, (v_wall_set, beta_over_H_set, alpha_set) in enumerate(zip(v_walls, beta_over_Hs, alphas)):
        log10_ubarfs = [
            np.log10(ubarf_func(v_wall=v_wall, alpha_n=alpha, cs=cs, adiabatic_ratio=adiabatic_ratio))
            for v_wall, alpha in zip(v_wall_set, alpha_set)
        ]
        log10_R_stars = np.log10(R_star(beta=beta_over_H_set, v_wall=v_wall_set, cs=const.CS0))

        # Plot points
        ax.plot(log10_ubarfs, log10_R_stars, ".")
        # Add labels to points
        if labels:
            label_set = labels[i]
            for x, y, label in zip(log10_ubarfs, log10_R_stars, label_set):
                ax.annotate(label, xy=(x, y), xycoords="data", xytext=(5, 0), textcoords="offset points")

    if titles:
        ax.legend([titles] if isinstance(titles, str) else titles, loc="lower left", framealpha=0.9)

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
    """Script for command-line use"""
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    fig = snr_figure_ubarf_rstar(
        v_wall_snr=args.v_wall, T_star_snr=args.Tstar, g_star_snr=args.gstar,
        alphas=args.alpha, beta_over_Hs=args.BetaoverH, v_walls=args.v_wall,
        mission_profile=mission_profile, engine=args.engine
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
