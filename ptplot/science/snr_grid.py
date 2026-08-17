#!/usr/bin/env python3

"""Precomputation of the SNR curves

This file contains all the functions related to the computation of the signal-to-noise ratio
curves for the UbarfRstar and AlphaBeta plots. This is done first
so the plot can then be built in parts. Can be used as a standalone module.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015)
"""

from multiprocessing import set_forkserver_preload
import os
import sys

import numpy as np
from pttools.analysis import v_wall_alpha_n_grid
from pttools.bubble import precompile
from pttools.bubble.fluid_reference import ref
from pttools.speedup import DEFAULT_FORKSERVER_PRELOAD, MAX_WORKERS_DEFAULT, run_parallel

if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import MissionProfile
from ptplot.science.parsing import PTPlotParser
from ptplot.science.snr import snr_point
from ptplot.science.snr_ssm import snr_column_ssm
import ptplot.science.type_hints as th

type SNRGridOutput = \
    tuple[th.FloatArr2D, th.FloatArr2D] | \
    tuple[th.FloatArr2D, th.FloatArr2D, th.FloatArr1D, th.FloatArr1D]

set_forkserver_preload(DEFAULT_FORKSERVER_PRELOAD + ["ptplot", "ptplot.science"])


def snr_grid(
        x: th.FloatOrArr1D,
        y: th.FloatOrArr1D,
        T_star: float,
        g_star: float,
        v_wall: float,
        mission_profile: MissionProfile,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        engine: Engine = Engine.DEFAULT,
        f_min: float = const.DEFAULT_SNR_F_MIN,
        f_max: float = const.DEFAULT_SNR_F_MAX,
        return_xy: bool = False,
        ubarf_rstar: bool = False,
        log_progress_percentage: bool = True,
        max_workers: int = MAX_WORKERS_DEFAULT) -> SNRGridOutput:
    if T_star is None or not np.isfinite(T_star):
        raise ValueError(f"Invalid T_star={T_star}")
    if g_star is None or not np.isfinite(g_star):
        raise ValueError(f"Invalid g_star={g_star}")
    if v_wall is None or not 0 < v_wall <= 1:
        raise ValueError(f"Invalid v_wall={v_wall}")

    # Ensure that SSM is loaded before starting subprocesses
    if engine == Engine.SSM:
        ref()
        precompile()

    kwargs={
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
        ret = run_parallel(
            func=snr_column_ssm,
            params=x,
            output_dtypes=(np.float64, ),
            return_arr_shape=(2, y.size),
            max_workers=max_workers,
            single_thread=False,
            global_pool=True,
            log_progress_percentage=log_progress_percentage,
            kwargs={
                "y": y,
                **kwargs,
            }
        )
        return ret[:, 0, :], ret[:, 1, :]
    else:
        snr, shock_times = run_parallel(
            func=snr_point,
            params=v_wall_alpha_n_grid(v_walls=x, alpha_ns=y),
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
        )
    if return_xy:
        return snr, shock_times, x, y
    return snr, shock_times


def snr_grid_alpha_beta(
        T_star: float,
        g_star: float,
        v_wall: float,
        mission_profile: MissionProfile,
        alpha_n: th.FloatArr1D = const.DEFAULT_ALPHA_N_RANGE,
        beta_over_H: th.FloatArr1D = const.DEFAULT_BETA_OVER_H_RANGE,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        engine: Engine = Engine.DEFAULT,
        f_min: float = const.DEFAULT_SNR_F_MIN,
        f_max: float = const.DEFAULT_SNR_F_MAX,
        log_progress_percentage: bool = True,
        return_alpha_beta: bool = False,
        max_workers: int = MAX_WORKERS_DEFAULT) -> SNRGridOutput:
    r"""Calculate SNR for a grid of $(\alpha_n, \beta/H)$ points

    :param v_wall: Wall velocity $v_\text{wall}$
    :param T_star: Temperature $T_*$ at which the GWs were produced
    :param g_star: Degrees of freedom $g_*$
    :param mission_profile: Which sensitivity curve to use
    :param alpha_n: Range of $\alpha_n$ values
    :param beta_over_H: Range of $\beta/H$ values
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param engine: Which power spectrum engine to use
    :param f_min: Minimum frequency to consider for SNR calculation
    :param f_max: Maximum frequency to consider for SNR calculation
    :return: SNR values, shock times, ubarf, r_star
    """
    if alpha_n is None or np.any(alpha_n <= 0) or not np.isfinite(alpha_n).all():
        raise ValueError(f"Invalid alpha_n={alpha_n}")
    if beta_over_H is None or np.any(beta_over_H <= 0) or not np.isfinite(beta_over_H).all():
        raise ValueError(f"Invalid beta_over_H={beta_over_H}")

    return snr_grid(
        x=alpha_n, y=beta_over_H,
        T_star=T_star, g_star=g_star, v_wall=v_wall,
        mission_profile=mission_profile, adiabatic_ratio=adiabatic_ratio, engine=engine,
        f_min=f_min, f_max=f_max,
        return_xy=return_alpha_beta,
        log_progress_percentage=log_progress_percentage,
        max_workers=max_workers
    )


def snr_grid_ubarf_rstar(
        v_wall: float,
        T_star: float,
        g_star: float,
        mission_profile: MissionProfile,
        ubarf: th.FloatArr1D = const.DEFAULT_UBARF_RANGE,
        r_star: th.FloatArr1D = const.DEFAULT_R_STAR_RANGE,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        engine: Engine = Engine.DEFAULT,
        f_min: float = const.DEFAULT_SNR_F_MIN,
        f_max: float = const.DEFAULT_SNR_F_MAX,
        return_ubarf_rstar: bool = False,
        log_progress_percentage: bool = True,
        max_workers: int = MAX_WORKERS_DEFAULT) -> SNRGridOutput:
    r"""Calculate SNR for a grid of $(\bar{U}_f, r_*)$ points

    :param v_wall: Wall velocity $v_\text{wall}$
    :param T_star: Temperature $T_*$ at which the GWs were produced
    :param g_star: Degrees of freedom $g_*$
    :param mission_profile: Which sensitivity curve to use
    :param ubarf: Range of $\bar{U}_f$ values
    :param r_star: Range of $r_*$ values
    :param adiabatic_ratio: Adiabatic index $\Gamma$
    :param engine: Which power spectrum engine to use
    :param f_min: Minimum frequency to consider for SNR calculation
    :param f_max: Maximum frequency to consider for SNR calculation
    :return: SNR values, shock times, ubarf, r_star
    """
    if ubarf is None or np.any(ubarf <= 0) or not np.isfinite(ubarf).all():
        raise ValueError(f"Invalid ubarf={ubarf}")
    if r_star is None or np.any(r_star <= 0) or not np.isfinite(r_star).all():
        raise ValueError(f"Invalid r_star={r_star}")

    return snr_grid(
        x=ubarf, y=r_star,
        T_star=T_star, g_star=g_star, v_wall=v_wall,
        mission_profile=mission_profile, adiabatic_ratio=adiabatic_ratio, engine=engine,
        f_min=f_min, f_max=f_max, ubarf_rstar=True,
        return_xy=return_ubarf_rstar,
        log_progress_percentage=log_progress_percentage,
        max_workers=max_workers
    )


def main():
    """Script for command-line use"""
    # Todo: enable the v_wall argument
    parser = PTPlotParser(
        description="Computes signal-to-noise contour to a file.",
        v_wall_alpha_betaoverh=False,
        mission_profile=True
    )
    args = parser.parse_args()
    mission_profile = MissionProfile.from_ind(args.mission_profile)
    tshHn, snr, log10_r_star, log10_ubarf = snr_grid_ubarf_rstar(
        v_wall=args.v_wall, T_star=args.Tstar, g_star=args.gstar, mission_profile=mission_profile,
        return_ubarf_rstar=True
    )

    # Use the mission profile to load the sensitivity curve name
    destination = f"{mission_profile.sensitivity_file_name}_Tn_{args.Tstar}_gstar_{args.gstar}_precomputed.npz"

    np.savez(
        destination,
        tshHn=tshHn,
        snr=snr,
        log10HnRstar=log10_r_star,
        log10Ubarf=log10_ubarf
    )
    print("Wrote SNR contour to:", destination)


if __name__ == "__main__":
    main()
