#!/usr/bin/env python3

r"""$(\alpha_n, \beta/H)$ plotting

Inspired by Antoine Petiteau's ExampleUseSNR1.py v0.3 (May 2015).
"""

import os.path
import sys

from matplotlib.figure import Figure
import numpy as np

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.logarithmic import add_points
from ptplot.science.plot.utils import fig_to_svg
from ptplot.science.plot.snr import snr_figure
from ptplot.science.snr_grid import snr_grid_alpha_beta
from ptplot.science.utils import log_range
import ptplot.science.type_hints as th


def snr_figure_alpha_beta(
        v_wall_snr: float,
        T_star_snr: float,
        g_star_snr: float,
        alphas: th.FloatOrArrOrList1D2D,
        beta_over_Hs: th.FloatOrArrOrList1D2D,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
        huge_alpha: bool = False,
        engine: Engine = Engine.DEFAULT,
        filled: bool = False) -> Figure:
    r"""Produce the $(\alpha_n, \beta/H)$ plot

    :param v_wall_snr: Wall velocity $v_\text{wall}$ used for the SNR curves
    :param T_star_snr: Transition temperature $T_*$ used for the SNR curves
    :param g_star_snr: Degrees of freedom $g_*$ used for the SNR curves
    :param alphas: Phase transition strengths $\alpha$[scenario, point]
    :param beta_over_Hs: Inverse phase transition durations $\frac{\beta}{H}$[scenario, point]
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param labels: Labels for the points
    :param titles: Titles for the points
    :param mission_profile: Which sensitivity curve to use
    :param huge_alpha: Whether $\alpha$ is very large
    :param engine: Which power spectrum engine to use
    :return: SNR figure of $(\alpha_n, \beta/H)$
    """
    alpha_n_grid = log_range(alphas, const.DEFAULT_ALPHA_N_RANGE)
    beta_over_H_grid = log_range(beta_over_Hs, const.DEFAULT_BETA_OVER_H_RANGE)
    snr, shock_times = snr_grid_alpha_beta(
        T_star=T_star_snr, g_star=g_star_snr, v_wall=v_wall_snr, mission_profile=mission_profile,
        alpha_n=alpha_n_grid, beta_over_H=beta_over_H_grid,
        adiabatic_ratio=adiabatic_ratio, engine=engine
    )
    log10_alpha_n_grid = np.log10(alpha_n_grid)
    log10_beta_over_H_grid = np.log10(beta_over_H_grid)
    alpha_mid = (log10_alpha_n_grid[0] + log10_alpha_n_grid[-1]) / 2

    fig, ax = snr_figure(
        x=log10_alpha_n_grid,
        y=log10_beta_over_H_grid,
        xlabel=r"$\alpha$",
        ylabel=r"$\beta/H_*$",
        titles=titles,
        snr=snr,
        shock_times=shock_times,
        shock_label_locs=np.array([
            (alpha_mid - 0.3 + 0.2 * i, y)
            for i, y in enumerate(range(int(log10_beta_over_H_grid[0]), int(log10_beta_over_H_grid[-1]) + 1))
        ]),
        label_wanted_y=2,
        huge_alpha=huge_alpha,
        engine=engine,
        filled=filled
    )
    add_points(ax=ax, x=alphas, y=beta_over_Hs, labels=labels, titles=titles)
    return fig


def main():
    """Script for command-line use"""
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    fig = snr_figure_alpha_beta(
        v_wall_snr=args.v_wall, T_star_snr=args.Tstar, g_star_snr=args.gstar,
        alphas=args.alpha, beta_over_Hs=args.BetaoverH,
        mission_profile=mission_profile, engine=args.engine
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
