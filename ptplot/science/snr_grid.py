"""Precomputation of the SNR curves

This file contains all the functions related to the computation of the signal-to-noise ratio
curves for the UbarfRstar and AlphaBeta plots. This is done first
so that the same grid can be used for several figures.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015)
"""

from abc import ABC
from multiprocessing import set_forkserver_preload
import typing as tp

import numpy as np
from pttools.analysis import v_wall_alpha_n_grid
from pttools.bubble import precompile
from pttools.bubble.fluid_reference import ref
from pttools.speedup import DEFAULT_FORKSERVER_PRELOAD, MAX_WORKERS_DEFAULT, run_parallel

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import MissionProfile
from ptplot.science.snr import snr_point
from ptplot.science.snr_ssm import snr_column_ssm
import ptplot.science.type_hints as th

set_forkserver_preload(DEFAULT_FORKSERVER_PRELOAD + ["ptplot", "ptplot.science"])


class SNRGrid(ABC):
    r"""SNR values on a grid of two parameters

    The grid is computed when the object is created,
    so that the same grid can be reused for several figures.
    The points to be drawn on top of the grid are stored here as well,
    since the grid ranges are derived from them.
    """
    X_NAME: str = "x"
    Y_NAME: str = "y"
    X_LABEL: str = "$x$"
    Y_LABEL: str = "$y$"

    def __init__(
            self,
            x: th.FloatArr1D,
            y: th.FloatArr1D,
            T_star: float,
            g_star: float,
            v_wall: float,
            mission_profile: MissionProfile,
            x_points: th.FloatOrArrOrList1D2D | None = None,
            y_points: th.FloatOrArrOrList1D2D | None = None,
            labels_points: th.StrOrListOrNestedList | None = None,
            titles: th.StrOrList | None = None,
            adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
            engine: Engine = Engine.DEFAULT,
            f_min: float = const.DEFAULT_SNR_F_MIN,
            f_max: float = const.DEFAULT_SNR_F_MAX,
            ubarf_rstar: bool = False,
            log_progress_percentage: bool = True,
            max_workers: int = MAX_WORKERS_DEFAULT):
        if T_star is None or not np.isfinite(T_star):
            raise ValueError(f"Invalid T_star={T_star}")
        if g_star is None or not np.isfinite(g_star):
            raise ValueError(f"Invalid g_star={g_star}")
        if v_wall is None or not 0 < v_wall <= 1:
            raise ValueError(f"Invalid v_wall={v_wall}")
        if x is None or np.any(x <= 0) or not np.isfinite(x).all():
            raise ValueError(f"Invalid {self.X_NAME}={x}")
        if y is None or np.any(y <= 0) or not np.isfinite(y).all():
            raise ValueError(f"Invalid {self.Y_NAME}={y}")

        self.x: th.FloatArr1D = x
        self.y: th.FloatArr1D = y
        self.x_points: th.FloatOrArrOrList1D2D | None = x_points
        self.y_points: th.FloatOrArrOrList1D2D | None = y_points
        self.labels_points: th.StrOrListOrNestedList | None = labels_points
        self.titles: th.StrOrList | None = titles
        self.T_star: float = T_star
        self.g_star: float = g_star
        self.v_wall: float = v_wall
        self.mission_profile: MissionProfile = mission_profile
        self.engine: Engine = engine

        # Ensure that SSM is loaded before starting subprocesses
        if engine == Engine.SSM:
            ref()
            precompile()

        kwargs = {
            "adiabatic_ratio": adiabatic_ratio,
            "f_min": f_min,
            "f_max": f_max,
            "g_star": g_star,
            "mission_profile": mission_profile,
            "parallel": False,
            "T_star": T_star,
            "ubarf_rstar": ubarf_rstar,
            "v_wall": v_wall
        }
        if engine == Engine.SSM:
            ret: th.FloatArr = tp.cast("th.FloatArr", run_parallel(
                func=snr_column_ssm,
                params=x,
                output_dtypes=(np.float64,),
                return_arr_shape=(2, y.size),
                max_workers=max_workers,
                single_thread=False,
                global_pool=True,
                log_progress_percentage=log_progress_percentage,
                kwargs={
                    "y": y,
                    **kwargs,
                }
            ))
            # The values are computed column by column, one column per x value,
            # resulting in ret[x, quantity, y].
            # Transpose to the [y, x] indexing used by the other engines and by Matplotlib contours.
            self.snr: th.FloatArr2D = ret[:, 0, :].T
            self.shock_times: th.FloatArr2D = ret[:, 1, :].T
        else:
            self.snr, self.shock_times = tp.cast("tuple[th.FloatArr2D, th.FloatArr2D]", run_parallel(
                func=snr_point,
                params=v_wall_alpha_n_grid(v_walls=x, alpha_ns=y),  # This works also for ubarf and r_star
                multiple_params=True,
                unpack_params=True,
                output_dtypes=(np.float64, np.float64),
                max_workers=max_workers,
                single_thread=True,
                log_progress_percentage=None,
                kwargs={
                    **kwargs,
                    "engine": engine
                }
            ))

    @property
    def has_points(self) -> bool:
        """Whether the grid has points to be drawn on top of it"""
        return self.x_points is not None and self.y_points is not None
