r"""SNR grid for the $(\alpha_n, \beta/H)$ plane."""

from pttools.speedup import MAX_WORKERS_DEFAULT

from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.snr_grid import SNRGrid
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th
from ptplot.science.utils import log_range


class SNRGridAlphaBeta(SNRGrid):
    r"""SNR values on a grid of $(\alpha_n, \beta/H)$ points."""

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
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            engine: Engine = Engine.DEFAULT,
            noise: Noise | None = None,
            log_progress_percentage: float | None = const.DEFAULT_LOG_PROGRESS_PERCENTAGE,
            max_workers: int = MAX_WORKERS_DEFAULT):
        r"""Calculate SNR for a grid of $(\alpha_n, \beta/H)$ points.

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
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param engine: Which power spectrum engine to use
        :param noise: Which noise curve to use
        :param log_progress_percentage: Log the progress every $x$ %. Set to None to disable the logging.
        :param max_workers: Maximum number of worker processes
        """
        if alpha_n is None:
            if alpha_points is None:
                raise ValueError("Provide either alpha_n or alpha_points.")
            alpha_n = log_range(alpha_points, const.DEFAULT_ALPHA_N_RANGE)
        if beta_over_H is None:
            if beta_over_H_points is None:
                raise ValueError("Provide either beta_over_H or beta_over_H_points.")
            beta_over_H = log_range(beta_over_H_points, const.DEFAULT_BETA_OVER_H_RANGE)

        self.v_wall_points: th.FloatOrArrOrList1D2D | None = v_wall_points

        super().__init__(
            x=alpha_n,
            y=beta_over_H,
            T_star=T_star, g_star=g_star, v_wall=v_wall,
            x_points=alpha_points, y_points=beta_over_H_points, labels_points=labels_points, titles=titles,
            noise=noise, adiabatic_index=adiabatic_index, engine=engine,
            log_progress_percentage=log_progress_percentage,
            max_workers=max_workers
        )

    @property
    def alpha_n(self) -> th.FloatArr1D:
        r"""Range of $\alpha_n$ values of the grid."""
        return self.x

    @property
    def beta_over_H(self) -> th.FloatArr1D:
        r"""Range of $\beta/H$ values of the grid."""
        return self.y

    @property
    def alpha_points(self) -> th.FloatOrArrOrList1D2D | None:
        r"""$\alpha$ values of the points to be drawn on the grid."""
        return self.x_points

    @property
    def beta_over_H_points(self) -> th.FloatOrArrOrList1D2D | None:
        r"""$\beta/H$ values of the points to be drawn on the grid."""
        return self.y_points
