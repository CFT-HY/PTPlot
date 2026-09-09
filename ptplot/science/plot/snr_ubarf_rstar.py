#!/usr/bin/env python3

r"""Create the $\bar{U}_f-R_*$ plot.

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

from ptplot.science.noise import noise_curve
from ptplot.science.parsing import PTPlotParser
from ptplot.science.plot.logarithmic import add_points
from ptplot.science.plot.snr import snr_figure
from ptplot.science.plot.utils import fig_to_svg
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
import ptplot.science.type_hints as th


def snr_figure_ubarf_rstar(
        grid: SNRGridUbarfRStar,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        huge_alpha: bool = False,
        filled: bool = False) -> Figure:
    r"""Produce the $(\bar{U}_f, r_*)$ plot.

    :param grid: Precomputed SNR grid
    :param labels: Labels for [scenario, point], defaults to those of the grid
    :param titles: Titles for the scenarios, defaults to those of the grid
    :param huge_alpha: Whether $\alpha$ is very large
    :param filled: Whether to fill the contour plot
    :return: SNR figure of $(\bar{U}_f, r_*)$
    """
    log10_ubarf_grid = np.log10(grid.ubarf)
    log10_r_star_grid = np.log10(grid.r_star)
    log10_ubarf_mid = (log10_ubarf_grid[0] + log10_ubarf_grid[-1]) / 2
    fig, ax = snr_figure(
        grid=grid,
        shock_label_locs=[
            (log10_ubarf_mid + 0.2 - 0.2 * i, float(y))
            for i, y in enumerate(range(int(log10_r_star_grid[0]), int(log10_r_star_grid[-1]) + 1))
        ],
        label_wanted_y=-2.5,
        huge_alpha=huge_alpha,
        filled=filled
    )
    if grid.has_points:
        ubarf_points, r_star_points = grid.points()
        add_points(
            ax=ax,
            x=ubarf_points, y=r_star_points,
            labels=grid.labels_points if labels is None else labels,
            titles=grid.titles if titles is None else titles
        )
    return fig


def main():
    """Script for command-line use."""
    parser = PTPlotParser(
        description="Writes a scalable vector graphic to stdout.",
        noise=True,
        engine=True
    )
    args = parser.parse_args()
    noise = noise_curve(obs_years=args.obs_years, eb=args.noise_eb, gb=args.noise_gb)
    fig = snr_figure_ubarf_rstar(
        grid=SNRGridUbarfRStar(
            v_wall=args.v_wall, T_star=args.Tstar, g_star=args.gstar,
            alpha_points=args.alpha, beta_over_H_points=args.BetaoverH, v_wall_points=args.v_wall,
            noise=noise, engine=args.engine
        )
    )
    print(fig_to_svg(fig).decode("utf-8"))


if __name__ == "__main__":
    main()
