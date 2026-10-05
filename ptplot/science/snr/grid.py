"""Precomputation of the SNR curves.

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
from pttools.export import Exporter, Record
from pttools.speedup import DEFAULT_FORKSERVER_PRELOAD, MAX_WORKERS_DEFAULT, run_parallel

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.snr.point import export_records, snr_point
from ptplot.science.snr.ssm import snr_column_ssm
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.ssm import BAG
from ptplot.science.type_hints import (
    FloatArr1D,
    FloatArr2D,
    FloatOrArrOrList1D2D,
    StrOrList,
    StrOrListOrNestedList,
)

set_forkserver_preload([*DEFAULT_FORKSERVER_PRELOAD, "ptplot", "ptplot.science"])


class SNRGrid(ABC):  # noqa: B024
    r"""SNR values on a grid of two parameters.

    The grid is computed when the object is created,
    so that the same grid can be reused for several figures.
    The points to be drawn on top of the grid are stored here as well,
    since the grid ranges are derived from them.
    """

    X_NAME: tp.ClassVar[str] = "x"
    Y_NAME: tp.ClassVar[str] = "y"
    X_LABEL: tp.ClassVar[str] = "$x$"
    Y_LABEL: tp.ClassVar[str] = "$y$"

    def __init__(
            self,
            x: FloatArr1D,
            y: FloatArr1D,
            T_star: float,
            g_star: float,
            v_wall: float,
            noise: Noise | None = None,
            x_points: FloatOrArrOrList1D2D | None = None,
            y_points: FloatOrArrOrList1D2D | None = None,
            labels_points: StrOrListOrNestedList | None = None,
            titles: StrOrList | None = None,
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            engine: Engine = Engine.DEFAULT,
            name: str | None = None,
            ubarf_rstar: bool = False,
            log_progress_percentage: float | None = const.DEFAULT_LOG_PROGRESS_PERCENTAGE,
            max_workers: int = MAX_WORKERS_DEFAULT,
            legacy_nucleation_cs_max: bool = False,
            exporter: Exporter | None = None):
        r"""Compute the SNR grid.

        :param x: Values of the parameter on the x-axis, $\alpha$ or $\bar{U}_f$
        :param y: Values of the parameter on the y-axis, $\tilde{\beta}$ or $r_*$
        :param T_star: $T_*$, temperature at which the GWs were produced
        :param g_star: $g_*$, degrees of freedom
        :param v_wall: $v_\text{wall}$, wall velocity
        :param noise: Which noise curve to use
        :param x_points: x values of the points [scenario, point] to be drawn on the grid
        :param y_points: y values of the points [scenario, point] to be drawn on the grid
        :param labels_points: Labels of the points [scenario, point]
        :param titles: Titles of the scenarios
        :param adiabatic_index: $\Gamma$, mean adiabatic index
        :param engine: Which power spectrum engine to use
        :param name: Name of the grid in comparison figures, defaults to the name of the engine
        :param ubarf_rstar: Whether $x$ and $y$ are $\bar{U}_f$ and $r_*$ instead of $\alpha$ and $\tilde{\beta}$
        :param log_progress_percentage: Interval of the progress logging of the SSM engine in percent.
            Set to None to disable the logging.
        :param max_workers: Maximum number of worker processes
        :param legacy_nucleation_cs_max:
            Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
        :param exporter: Exporter to which the computed spectra are added, e.g. for saving them to an HDF5 file.
            The fields are extracted in the worker processes with the extractor of the exporter.
            Only the spectra of the engines that support exporting are added,
            see :py:meth:`ptplot.science.spectrum.base.PowerSpectrum.record`.
            The spectra whose computation failed are not added.
            The errors in exporting are logged instead of raised, so that they do not discard the computed SNR values.
        :raises ValueError: If a parameter is invalid
        """
        if engine is None or not engine:
            engine = Engine.DEFAULT
        if g_star is None or not np.isfinite(g_star):
            raise ValueError(f"Invalid g_star={g_star}")
        if T_star is None or not np.isfinite(T_star):
            raise ValueError(f"Invalid T_star={T_star}")
        if v_wall is None or not 0 < v_wall <= 1:
            raise ValueError(f"Invalid v_wall={v_wall}")
        if x is None or np.any(x <= 0) or not np.isfinite(x).all():
            raise ValueError(f"Invalid {self.X_NAME}={x}")
        if y is None or np.any(y <= 0) or not np.isfinite(y).all():
            raise ValueError(f"Invalid {self.Y_NAME}={y}")

        self.x: FloatArr1D = x
        self.y: FloatArr1D = y
        self.x_points: FloatOrArrOrList1D2D | None = x_points
        self.y_points: FloatOrArrOrList1D2D | None = y_points
        self.labels_points: StrOrListOrNestedList | None = labels_points
        self.titles: StrOrList | None = titles
        self.T_star: float = T_star
        self.g_star: float = g_star
        self.v_wall: float = v_wall
        self.noise: Noise = resolve_noise(noise)
        self.engine: Engine = engine
        self.name: str = engine if name is None else name

        # Ensure that SSM is loaded before starting subprocesses
        if engine == Engine.SSM:
            ref()
            precompile()

        kwargs = {
            "adiabatic_index": adiabatic_index,
            "extractor": None if exporter is None else exporter.extractor,
            "g_star": g_star,
            "legacy_nucleation_cs_max": legacy_nucleation_cs_max,
            "noise": self.noise,
            "parallel": False,
            "T_star": T_star,
            "ubarf_rstar": ubarf_rstar,
            "v_wall": v_wall,
        }
        records: list[Record | None]
        if engine == Engine.SSM:
            columns: np.ndarray = tp.cast(np.ndarray, run_parallel(
                func=snr_column_ssm,
                params=x,
                output_dtypes=(object,),
                max_workers=max_workers,
                single_thread=False,
                global_pool=True,
                log_progress_percentage=log_progress_percentage,
                kwargs={
                    "y": y,
                    # The model is given explicitly, so that all the worker processes use the same model object.
                    # Its identifier is preserved in pickling, and therefore the exported spectra share a model.
                    "model": BAG,
                    **kwargs,
                }
            ))
            # The values are computed column by column, one column per x value.
            # Stack the columns along the second axis
            # to get the [y, x] indexing used by the other engines and by Matplotlib contours.
            self.snr: FloatArr2D = np.stack([column.snr for column in columns], axis=1)
            self.shock_times: FloatArr2D = np.stack([column.shock_times for column in columns], axis=1)
            records = [record for column in columns for record in column.records]
        else:
            self.snr, self.shock_times, records_arr = tp.cast(
                tuple[FloatArr2D, FloatArr2D, np.ndarray],
                run_parallel(
                    func=snr_point,
                    params=v_wall_alpha_n_grid(v_walls=x, alpha_ns=y),  # This works also for ubarf and r_star
                    multiple_params=True,
                    unpack_params=True,
                    # The third output is the record of the spectrum for exporting, or None.
                    output_dtypes=(np.float64, np.float64, object),
                    max_workers=max_workers,
                    single_thread=True,
                    # The BPL and DBPL engines are fast and run in a single thread,
                    # so there is no need to log their progress.
                    log_progress_percentage=None,
                    kwargs={
                        **kwargs,
                        "engine": engine
                    }
                )
            )
            records = list(records_arr.flat)
        if exporter is not None:
            export_records(exporter, records)

    @property
    def has_points(self) -> bool:
        """Whether the grid has points to be drawn on top of it."""
        return self.x_points is not None and self.y_points is not None

    def points(self) -> tuple[FloatOrArrOrList1D2D, FloatOrArrOrList1D2D]:
        """Get the x and y values of the points to be drawn on top of the grid.

        :return: x and y values of the points
        """
        if self.x_points is None or self.y_points is None:
            raise ValueError("The grid has no points to be drawn on top of it.")
        return self.x_points, self.y_points
