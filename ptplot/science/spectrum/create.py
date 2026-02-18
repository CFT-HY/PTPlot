"""Utilities for creating power spectra"""

from pttools.models import ConstCSModel, Model

from ptplot.science import const
from ptplot.science.engine import Engine
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.bpl import PowerSpectrumBPL
from ptplot.science.spectrum.dbpl import PowerSpectrumDBPL
from ptplot.science.spectrum.ssm import PowerSpectrumSSM, bag


def power_spectrum(
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        vw: float | None = None,
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
        model: Model = bag) -> PowerSpectrum:
    if engine == Engine.DEFAULT:
        return PowerSpectrumBPL(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf=ubarf
        )
    elif engine == Engine.SSM:
        # If css2 or csb2 is provided, but the model has not been specified, use ConstCSModel.
        if (css2 is not None or csb2 is not None) and model is bag:
            model = ConstCSModel(css2=css2, csb2=csb2)
        return PowerSpectrumSSM(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf=ubarf,
            model=model
        )
    elif engine == Engine.DBPL:
        return PowerSpectrumDBPL(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf=ubarf
        )
    raise ValueError(f"Invalid engine: {engine}")
