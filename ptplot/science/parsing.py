"""Argument parsing for command-line use of PTPlot"""

import argparse

from ptplot.science import const
from ptplot.science.engine import ENGINE_SHORT_NAMES, Engine
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE


class PTPlotParser(argparse.ArgumentParser):
    """Argument parser for command-line use of PTPlot"""
    def __init__(
            self,
            *args,
            v_wall_alpha_betaoverh: bool = True,
            Tstar_gstar: bool = True,
            mission_profile: bool = False,
            engine: bool = False,
            **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = argparse.ArgumentDefaultsHelpFormatter
        super().__init__(*args, **kwargs)
        if v_wall_alpha_betaoverh:
            self.add_argument(
                "-v_wall", "--v_wall", "-vw", "--vw", type=float, default=const.DEFAULT_V_WALL,
                help=const.V_WALL_NAME
            )
            self.add_argument(
                "-alpha", "--alpha", type=float, default=const.DEFAULT_ALPHA,
                help=const.ALPHA_NAME
            )
            self.add_argument(
                "-BetaoverH", "--BetaoverH", type=float, default=const.DEFAULT_BETA_OVER_H,
                help=const.BETA_OVER_H_NAME
            )
        if Tstar_gstar:
            self.add_argument(
                "-Tstar", "--Tstar", type=float, default=const.DEFAULT_T_STAR,
                help=const.T_STAR_NAME
            )
            self.add_argument(
                "-gstar", "--gstar", type=float, default=const.DEFAULT_G_STAR,
                help=const.G_STAR_NAME
            )
        if mission_profile:
            self.add_argument(
                "-mission_profile", "--mission_profile",
                type=int,
                default=DEFAULT_MISSION_PROFILE,
                help="mission profile for the sensitivity curve"
            )
        if engine:
            self.add_argument(
                "-engine", "--engine", "-ps", "--ps",
                default=Engine.DEFAULT.name,
                choices=ENGINE_SHORT_NAMES,
                help="Method for computing the power spectrum"
            )
