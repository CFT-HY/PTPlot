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
from pttools.speedup import MAX_WORKERS_DEFAULT

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ptplot.science import const, ubarf_rstar_from_alpha_beta
from ptplot.science.spectrum.engine import Engine
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.utils import fig_to_svg
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.plot.logarithmic import add_points
from ptplot.science.plot.snr import snr_figure
from ptplot.science.snr_grid import snr_grid_ubarf_rstar
import ptplot.science.type_hints as th
from ptplot.science.utils import log_range


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
        engine: Engine = Engine.DEFAULT,
        filled: bool = False,
        max_workers: int = MAX_WORKERS_DEFAULT) -> Figure:
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
    v_walls, ubarf, r_star, labels = ubarf_rstar_from_alpha_beta(
        v_wall=v_wall_snr if v_walls is None else v_walls,
        alpha=alphas,
        beta_over_H=beta_over_Hs,
        labels=labels,
        cs=cs,
        adiabatic_ratio=adiabatic_ratio
    )
    ubarf_grid = log_range(ubarf, const.DEFAULT_UBARF_RANGE)
    r_star_grid = log_range(r_star, const.DEFAULT_R_STAR_RANGE)

    snr, shock_times = snr_grid_ubarf_rstar(
        v_wall=v_wall_snr,
        T_star=T_star_snr,
        g_star=g_star_snr,
        mission_profile=mission_profile,
        ubarf=ubarf_grid,
        r_star=r_star_grid,
        engine=engine,
        max_workers=max_workers
    )
    log10_ubarf_grid = np.log10(ubarf_grid)
    log10_r_star_grid = np.log10(r_star_grid)
    log10_ubarf_mid = (log10_ubarf_grid[0] + log10_ubarf_grid[-1]) / 2
    fig, ax = snr_figure(
        x=log10_ubarf_grid,
        y=log10_r_star_grid,
        xlabel=r"$\overline{U}_{\rm f}$",
        ylabel=r"$r_* = H_{\rm n} R_*$",
        titles=titles,
        snr=snr,
        shock_times=shock_times,
        shock_label_locs=np.array([
            (log10_ubarf_mid + 0.2 - 0.2 * i, y)
            for i, y in enumerate(range(int(log10_r_star_grid[0]), int(log10_r_star_grid[-1]) + 1))
        ]),
        label_wanted_y=-2.5,
        huge_alpha=huge_alpha,
        engine=engine,
        filled=filled
    )
    add_points(ax=ax, x=ubarf, y=r_star, labels=labels, titles=titles)
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
