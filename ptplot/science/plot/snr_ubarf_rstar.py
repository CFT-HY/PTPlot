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
from ptplot.science.espinosa import ubarf
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.plot.snr import snr_figure
from ptplot.science.snr_grid import snr_grid
import ptplot.science.type_hints as th
from ptplot.science.utils import atleast_2d, R_star

LOCS_TSH = np.array([(-1.8,-3.5), (-1.8,-2.5), (-1.8,-1.8), (-1.8,-0.5)])
TICKPOS_HUGE_ALPHA = np.array([-2, -1, 0, 1, 2, 3])


def snr_figure_ubarf_rstar(
        # Todo: Why are some of these defaults different to the ones in const.py?
        vws: th.FloatOrArrOrListOfArr1D = 0.5,
        alphas: th.FloatOrArrOrListOfArr1D = const.DEFAULT_ALPHA,
        beta_over_Hs: th.FloatOrArrOrListOfArr1D = 100,
        T_star: float = 100,
        g_star: float = const.DEFAULT_G_STAR,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        huge_alpha: bool = False,
        engine: Engine = Engine.DEFAULT) -> Figure:
    r"""Produce the $\bar{U}_f-R_*$ plot

    :param vws: Wall velocities $v_\text{wall}$[scenario, point]
    :param alphas: Phase transition strengths $\alpha$[scenario, point]
    :param beta_over_Hs: Inverse phase transition durations $\frac{\beta}{H}$[scenario, point]
    :param T_star: Transition temperature $T_*$
    :param g_star: Degrees of freedom $g_*$
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param labels: Labels for [scenario, point]
    :param titles: Titles for the scenarios
    :param mission_profile: Which sensitivity curve to use
    :param huge_alpha: Whether $\alpha$ is very large
    :return: Figure of $\bar{U}_f-R_*$
    """
    if np.isscalar(vws):
        v_wall = vws
    elif np.isscalar(vws[0]):
        v_wall = vws[0]
    elif np.isscalar(vws[0][0]):
        v_wall = vws[0][0]
    else:
        raise ValueError("vws must be scalar, 1D or 2D")

    # if np.isscalar(alphas):
    #     alpha = alphas
    # elif np.isscalar(alphas[0]):
    #     alpha = alphas[0]
    # elif np.isscalar(alphas[0][0]):
    #     alpha = alphas[0][0]
    # else:
    #     raise ValueError("alphas must be scalar, 1D or 2D")

    tshHn, snr, log10HnRstar, log10Ubarf = snr_grid(
        v_wall=v_wall,
        T_star=T_star,
        g_star=g_star,
        # alpha=alpha,
        mission_profile=mission_profile,
        ubarf_max=1000 if huge_alpha else 1,
        engine=engine
    )
    fig, ax = snr_figure(
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

    # Ensure that input values are 2D arrays
    vws, alphas, beta_over_Hs = atleast_2d(vws, alphas, beta_over_Hs)
    if labels:
        if isinstance(labels, str):
            labels = [[labels]]
        elif isinstance(labels[0], str):
            labels = [labels]

    # Iterate over scenarios
    for i, (vw_set, BetaoverH_set, alpha_set) in enumerate(zip(vws, beta_over_Hs, alphas)):
        log10_ubarfs = [
            np.log10(ubarf(v_wall=vw, alpha_n=alpha, adiabatic_ratio=adiabatic_ratio))
            for vw, alpha in zip(vw_set, alpha_set)
        ]
        log10_R_stars = np.log10(R_star(BetaoverH_set, vw_set, cs=const.CS0))

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
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    fig = snr_figure_ubarf_rstar(
        vws=args.vw, alphas=args.alpha, beta_over_Hs=args.BetaoverH,
        T_star=args.Tstar, g_star=args.gstar, mission_profile=mission_profile, engine=args.engine
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
