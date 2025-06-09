import argparse

from ptplot.science import const


class PTPlotParser(argparse.ArgumentParser):
    def __init__(
            self,
            *args,
            vw_alpha_betaoverh: bool = True,
            Tstar_gstar: bool = True,
            methods: bool = False,
            mission_profile: bool = False,
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
                "-mission_profile", "--mission_profile", type=int, default=const.DEFAULT_MISSION_PROFILE,
                help="mission profile for the sensitivity curve"
            )
        if methods:
            self.add_argument(
                "-ssm", "--ssm", action="store_true",
                help="Use the Sound Shell Model (SSM) from PTtools to compute the power spectrum."
            )
            self.add_argument(
                "-dbpl", "--dbpl", action="store_true",
                help="Use double-broken power law to compute the power spectrum."
            )
