import argparse

from ptplot.science import const
from ptplot.science.engine import ENGINE_SHORT_NAMES, Engine
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE


class PTPlotParser(argparse.ArgumentParser):
    def __init__(
            self,
            *args,
            vw_alpha_betaoverh: bool = True,
            Tstar_gstar: bool = True,
            mission_profile: bool = False,
            engine: bool = False,
            **kwargs):
        super().__init__(
            *args,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            **kwargs
        )
        if vw_alpha_betaoverh:
            self.add_argument(
                "-vw", "--vw", type=float, default=const.DEFAULT_VW,
                help=const.VW_NAME
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
