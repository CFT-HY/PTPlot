"""Utilities for creating power spectra."""

import typing as tp

from pttools.models import ConstCSModel, Model

from ptplot.science import const
from ptplot.science.spectrum.base import Engine, PowerSpectrum
from ptplot.science.spectrum.engine import ENGINE_SPECTRUM_CLASSES
from ptplot.science.spectrum.ssm import BAG, PowerSpectrumSSM


def const_cs_model(css2: float | None = None, csb2: float | None = None) -> ConstCSModel:
    """Create a ConstCSModel, using its default sound speeds for the values that were not given."""
    # Todo: Make PTtools ConstCSModel accept None values for css2 and csb2.
    kwargs: dict[str, tp.Any] = {}
    if css2 is not None:
        kwargs["css2"] = css2
    if csb2 is not None:
        kwargs["csb2"] = csb2
    return ConstCSModel(**kwargs)


def power_spectrum(
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        v_wall: float | None = None,
        alpha: float | None = None,
        beta_over_H: float | None = None,
        ubarf: float | None = None,
        r_star: float | None = None,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        zp: float = const.DEFAULT_ZP,
        k_turb: float = const.DEFAULT_K_TURB,
        engine: Engine = Engine.DEFAULT,
        css2: float | None = None,
        csb2: float | None = None,
        model: Model = BAG,
        parallel: bool = True) -> PowerSpectrum:
    """Create a power spectrum object from the given parameters."""
    if engine not in ENGINE_SPECTRUM_CLASSES:
        raise ValueError(f"Invalid engine: {engine}")

    # SSM requires additional arguments
    if engine == Engine.SSM:
        # If css2 or csb2 is provided, but the model has not been specified, use ConstCSModel.
        if (css2 is not None or csb2 is not None) and model is BAG:
            model = const_cs_model(css2=css2, csb2=csb2)
        return PowerSpectrumSSM(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            v_wall=v_wall, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf=ubarf,
            parallel=parallel, model=model
        )
    return ENGINE_SPECTRUM_CLASSES[engine](
        beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
        v_wall=v_wall, adiabatic_ratio=adiabatic_ratio, zp=zp,
        alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf=ubarf,
        parallel=parallel
    )
