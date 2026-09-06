#!/usr/bin/env python3

r"""SNR grid for the $(\bar{U}_f, r_*)$ plane."""

import os
import sys

import numpy as np
from pttools.speedup import MAX_WORKERS_DEFAULT

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science.const import (
    CS0,
    DEFAULT_ADIABATIC_INDEX,
    DEFAULT_R_STAR_RANGE,
    DEFAULT_SNR_F_MAX,
    DEFAULT_SNR_F_MIN,
    DEFAULT_UBARF_RANGE,
    DEFAULT_V_WALL,
)
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.parsing import PTPlotParser
from ptplot.science.snr_grid import SNRGrid
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th
from ptplot.science.utils import log_range, ubarf_rstar_from_alpha_beta


class SNRGridUbarfRStar(SNRGrid):
    r"""SNR values on a grid of $(\bar{U}_f, r_*)$ points."""

    X_NAME = "ubarf"
    Y_NAME = "r_star"
    X_LABEL = r"$\overline{U}_{\rm f}$"
    Y_LABEL = r"$r_* = H_{\rm n} R_*$"

    def __init__(
            self,
            v_wall: float,
            T_star: float,
            g_star: float,
            alpha_points: th.FloatOrArrOrListOfArr1D | None = None,
            beta_over_H_points: th.FloatOrArrOrListOfArr1D | None = None,
            v_wall_points: th.FloatOrArrOrListOfArr1D | None = None,
            labels_points: th.StrOrListOrNestedList | None = None,
            titles: th.StrOrList | None = None,
            ubarf: th.FloatArr1D | None = None,
            r_star: th.FloatArr1D | None = None,
            adiabatic_index: float = DEFAULT_ADIABATIC_INDEX,
            cs: float = CS0,
            engine: Engine = Engine.DEFAULT,
            mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
            f_min: float = DEFAULT_SNR_F_MIN,
            f_max: float = DEFAULT_SNR_F_MAX,
            log_progress_percentage: bool = True,
            max_workers: int = MAX_WORKERS_DEFAULT):
        r"""Calculate SNR for a grid of $(\bar{U}_f, r_*)$ points.

        The points are converted from $(\alpha, \beta/H)$ to $(\bar{U}_f, r_*)$,
        and the grid ranges are deduced from them, unless the ranges are given explicitly.

        :param v_wall: Wall velocity $v_\text{wall}$
        :param T_star: Temperature $T_*$ at which the GWs were produced
        :param g_star: Degrees of freedom $g_*$
        :param alpha_points: Phase transition strengths $\alpha$[scenario, point] to be drawn on the grid
        :param beta_over_H_points: Inverse phase transition durations
            $\frac{\beta}{H}$[scenario, point] to be drawn on the grid
        :param v_wall_points: Wall velocities $v_\text{wall}$[scenario, point] of the points
        :param labels_points: Labels of the points [scenario, point]
        :param titles: Titles of the scenarios
        :param ubarf: Range of $\bar{U}_f$ values
        :param r_star: Range of $r_*$ values
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param cs: Sound speed $c_s$
        :param engine: Which power spectrum engine to use
        :param mission_profile: Which sensitivity curve to use
        :param f_min: Minimum frequency to consider for SNR calculation
        :param f_max: Maximum frequency to consider for SNR calculation
        """
        self.v_wall_points: th.FloatOrArrOrList1D2D | None
        ubarf_points: th.FloatOrArrOrList1D2D | None
        r_star_points: th.FloatOrArrOrList1D2D | None
        if alpha_points is not None and beta_over_H_points is not None:
            self.v_wall_points, ubarf_points, r_star_points, labels_points = ubarf_rstar_from_alpha_beta(
                v_wall=v_wall if v_wall_points is None else v_wall_points,
                alpha=alpha_points,
                beta_over_H=beta_over_H_points,
                labels=labels_points,
                cs=cs,
                adiabatic_index=adiabatic_index
            )
            if ubarf is None:
                ubarf = log_range(ubarf_points, DEFAULT_UBARF_RANGE)
            if r_star is None:
                r_star = log_range(r_star_points, DEFAULT_R_STAR_RANGE)
        else:
            if ubarf is None:
                raise ValueError("Provide either ubarf or alpha_points.")
            if r_star is None:
                raise ValueError("Provide either r_star or beta_over_H_points.")
            self.v_wall_points = None
            ubarf_points = None
            r_star_points = None
            labels_points = None

        super().__init__(
            x=ubarf,
            y=r_star,
            T_star=T_star, g_star=g_star, v_wall=v_wall,
            x_points=ubarf_points, y_points=r_star_points, labels_points=labels_points, titles=titles,
            mission_profile=mission_profile, adiabatic_index=adiabatic_index, engine=engine,
            f_min=f_min, f_max=f_max, ubarf_rstar=True,
            log_progress_percentage=log_progress_percentage,
            max_workers=max_workers
        )

    @property
    def ubarf(self) -> th.FloatArr1D:
        r"""Range of $\bar{U}_f$ values of the grid."""
        return self.x

    @property
    def r_star(self) -> th.FloatArr1D:
        r"""Range of $r_*$ values of the grid."""
        return self.y

    @property
    def ubarf_points(self) -> th.FloatOrArrOrList1D2D | None:
        r"""$\bar{U}_f$ values of the points to be drawn on the grid."""
        return self.x_points

    @property
    def r_star_points(self) -> th.FloatOrArrOrList1D2D | None:
        r"""$r_*$ values of the points to be drawn on the grid."""
        return self.y_points


def main():
    """Script for command-line use."""
    # Todo: enable the v_wall argument
    parser = PTPlotParser(
        description="Computes signal-to-noise contour to a file.",
        v_wall_alpha_betaoverh=False,
        mission_profile=True,
        engine=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    grid = SNRGridUbarfRStar(
        v_wall=DEFAULT_V_WALL, T_star=args.Tstar, g_star=args.gstar,
        mission_profile=mission_profile, engine=args.engine,
        ubarf=DEFAULT_UBARF_RANGE, r_star=DEFAULT_R_STAR_RANGE
    )

    # Use the mission profile to load the sensitivity curve name
    destination = \
        f"{mission_profile.sensitivity_file_name}_Tn_{args.Tstar}_gstar_{args.gstar}_{args.engine}_precomputed.npz"

    np.savez(
        destination,
        tshHn=grid.shock_times,
        snr=grid.snr,
        log10HnRstar=np.log10(grid.r_star),
        log10Ubarf=np.log10(grid.ubarf)
    )
    print("Wrote SNR contour to:", destination)


if __name__ == "__main__":
    main()
