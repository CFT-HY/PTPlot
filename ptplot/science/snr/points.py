"""Signal-to-noise ratios of sets of points in the parameter space."""

import typing as tp

import numpy as np
from pttools.bubble import precompile
from pttools.bubble.fluid_reference import ref
from pttools.export import Exporter
from pttools.speedup import MAX_WORKERS_DEFAULT, run_parallel

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.snr.point import export_records, snr_point
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.ssm import SSMSettings
import ptplot.science.type_hints as th

__all__ = ["snr_points"]


def snr_points(
        v_wall: th.FloatArr1D,
        alpha_n: th.FloatArr1D,
        beta_tilde: th.FloatArr1D,
        T_star: th.FloatArr1D,
        g_star: th.FloatArr1D,
        engines: list[Engine],
        adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
        noise: Noise | None = None,
        legacy_nucleation_cs_max: bool = const.DEFAULT_LEGACY_NUCLEATION_CS_MAX,
        exporter: Exporter | None = None,
        ssm_settings: SSMSettings | None = None,
        max_workers: int = MAX_WORKERS_DEFAULT,
        log_progress_percentage: float | None = const.DEFAULT_LOG_PROGRESS_PERCENTAGE) -> th.FloatArr2D:
    r"""Signal-to-noise ratios (SNR) of a set of points in the parameter space with each engine.

    The points of each engine are computed in parallel with :py:func:`pttools.speedup.parallel.run_parallel`,
    see :py:func:`ptplot.science.snr.point.snr_point`.
    As in the SNR grids, see :py:class:`ptplot.science.snr.grid.SNRGrid`,
    only the SSM engine is run in parallel, as the other engines are so fast
    that the overhead of parallelism would exceed the time saved.
    The parallelism of each spectrum is disabled, as the spectra are computed in parallel with each other.

    :param v_wall: $v_\text{wall}$, wall velocities of the points
    :param alpha_n: $\alpha_n$, phase transition strengths of the points
    :param beta_tilde: $\beta/H_*$, inverse phase transition durations of the points
    :param T_star: $T_*$, temperatures at which the GWs were produced
    :param g_star: $g_*$, degrees of freedom
    :param engines: Which power spectrum engines to use
    :param adiabatic_index: $\Gamma$, mean adiabatic index
    :param noise: Which noise curve to use
    :param legacy_nucleation_cs_max:
        Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
    :param exporter: Exporter to which the computed spectra are added in the order of the engines and the points.
        Only the spectra of the engines that support exporting are added,
        see :py:meth:`ptplot.science.spectrum.base.PowerSpectrum.record`.
    :param ssm_settings: Accuracy settings of the PTtools spectra of the SSM engine
    :param max_workers: Maximum number of worker processes or threads
    :param log_progress_percentage: Interval of the progress logging of the SSM engine in percent.
        Set to None to disable the logging.
    :return: SNR values [point, engine], NaN where the computation failed
    """
    noise = resolve_noise(noise)
    params = np.stack((alpha_n, beta_tilde, T_star, g_star, v_wall), axis=-1).astype(np.float64)
    snr = np.empty((alpha_n.size, len(engines)))
    for i_engine, engine in enumerate(engines):
        if engine == Engine.SSM:
            # Ensure that SSM is loaded before starting subprocesses
            ref()
            precompile()
        snr_engine, _, point_spectra = tp.cast(
            tuple[th.FloatArr1D, th.FloatArr1D, np.ndarray],
            run_parallel(
                func=snr_point,
                params=params,
                multiple_params=True,
                unpack_params=True,
                output_dtypes=(np.float64, np.float64, object),
                max_workers=max_workers,
                single_thread=engine != Engine.SSM,
                log_progress_percentage=log_progress_percentage if engine == Engine.SSM else None,
                kwargs={
                    "adiabatic_index": adiabatic_index,
                    "engine": engine,
                    "extractor": None if exporter is None else exporter.extractor,
                    "legacy_nucleation_cs_max": legacy_nucleation_cs_max,
                    "noise": noise,
                    "parallel": False,
                    "ssm_settings": ssm_settings,
                }
            )
        )
        snr[:, i_engine] = snr_engine
        if exporter is not None:
            export_records(exporter, [point.record for point in point_spectra.flat])
    return snr
