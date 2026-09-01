r"""SNR grid for the $(\alpha_n, \beta/H)$ plane"""

from pttools.speedup import MAX_WORKERS_DEFAULT

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.snr_grid import SNRGrid
import ptplot.science.type_hints as th
from ptplot.science.utils import log_range


class SNRGridAlphaBeta(SNRGrid):
    r"""SNR values on a grid of $(\alpha_n, \beta/H)$ points"""
    X_NAME = "alpha_n"
    Y_NAME = "beta/H*"
    X_LABEL = r"$\alpha$"
    Y_LABEL = r"$\beta/H_*$"

    def __init__(
            self,
            T_star: float,
            g_star: float,
            v_wall: float,
            alpha_points: th.FloatOrArrOrList1D2D | None = None,
            beta_over_H_points: th.FloatOrArrOrList1D2D | None = None,
            v_wall_points: th.FloatOrArrOrList1D2D | None = None,
            labels_points: th.StrOrListOrNestedList | None = None,
            titles: th.StrOrList | None = None,
            alpha_n: th.FloatArr1D | None = None,
            beta_over_H: th.FloatArr1D | None = None,
            adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
            engine: Engine = Engine.DEFAULT,
            mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE,
            f_min: float = const.DEFAULT_SNR_F_MIN,
            f_max: float = const.DEFAULT_SNR_F_MAX,
            log_progress_percentage: bool = True,
            max_workers: int = MAX_WORKERS_DEFAULT):
        r"""Calculate SNR for a grid of $(\alpha_n, \beta/H)$ points

        The grid ranges are deduced from the points, unless they are given explicitly.

        :param T_star: Temperature $T_*$ at which the GWs were produced
        :param g_star: Degrees of freedom $g_*$
        :param v_wall: Wall velocity $v_\text{wall}$
        :param alpha_points: Phase transition strengths $\alpha$[scenario, point] to be drawn on the grid
        :param beta_over_H_points: Inverse phase transition durations
            $\frac{\beta}{H}$[scenario, point] to be drawn on the grid
        :param v_wall_points: Wall velocities $v_\text{wall}$[scenario, point] of the points
        :param labels_points: Labels of the points [scenario, point]
        :param titles: Titles of the scenarios
        :param alpha_n: Range of $\alpha_n$ values
        :param beta_over_H: Range of $\beta/H$ values
        :param adiabatic_ratio: Adiabatic index $\Gamma$
        :param engine: Which power spectrum engine to use
        :param mission_profile: Which sensitivity curve to use
        :param f_min: Minimum frequency to consider for SNR calculation
        :param f_max: Maximum frequency to consider for SNR calculation
        """
        if alpha_n is None and alpha_points is None:
            raise ValueError("Provide either alpha_n or alpha_points.")
        if beta_over_H is None and beta_over_H_points is None:
            raise ValueError("Provide either beta_over_H or beta_over_H_points.")

        self.v_wall_points: th.FloatOrArrOrList1D2D | None = v_wall_points

        super().__init__(
            x=log_range(alpha_points, const.DEFAULT_ALPHA_N_RANGE) if alpha_n is None else alpha_n,
            y=log_range(beta_over_H_points, const.DEFAULT_BETA_OVER_H_RANGE) if beta_over_H is None else beta_over_H,
            T_star=T_star, g_star=g_star, v_wall=v_wall,
            x_points=alpha_points, y_points=beta_over_H_points, labels_points=labels_points, titles=titles,
            mission_profile=mission_profile, adiabatic_ratio=adiabatic_ratio, engine=engine,
            f_min=f_min, f_max=f_max,
            log_progress_percentage=log_progress_percentage,
            max_workers=max_workers
        )

    @property
    def alpha_n(self) -> th.FloatArr1D:
        r"""Range of $\alpha_n$ values of the grid"""
        return self.x

    @property
    def beta_over_H(self) -> th.FloatArr1D:
        r"""Range of $\beta/H$ values of the grid"""
        return self.y

    @property
    def alpha_points(self) -> th.FloatOrArrOrList1D2D | None:
        r"""$\alpha$ values of the points to be drawn on the grid"""
        return self.x_points

    @property
    def beta_over_H_points(self) -> th.FloatOrArrOrList1D2D | None:
        r"""$\beta/H$ values of the points to be drawn on the grid"""
        return self.y_points
