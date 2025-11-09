from pttools.models import ConstCSModel, Model
from pttools.omgw0 import SuppressionMethod

from ptplot.science import const
from ptplot.science.engine import Engine
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.bpl import PowerSpectrumBPL
from ptplot.science.spectrum.dbpl import PowerSpectrumDBPL
from ptplot.science.spectrum.ssm import PowerSpectrumSSM, bag


def power_spectrum(
        beta_over_H: float | None = None,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        vw: float | None = None,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        zp: float = const.DEFAULT_ZP,
        alpha: float | None = None,
        k_turb: float = const.DEFAULT_K_TURB,
        r_star: float | None = None,
        ubarf_in: float | None = None,
        engine: Engine = Engine.DEFAULT,
        css2: float | None = None,
        csb2: float | None = None,
        suppression: SuppressionMethod = SuppressionMethod.NONE,
        model: Model = bag) -> PowerSpectrum:
    if engine == Engine.DEFAULT:
        return PowerSpectrumBPL(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf_in=ubarf_in
        )
    elif engine == Engine.SSM:
        if (css2 is not None or csb2 is not None) and model is bag:
            model = ConstCSModel(css2=css2, csb2=csb2)
        return PowerSpectrumSSM(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf_in=ubarf_in,
            suppression=suppression, model=model
        )
    elif engine == Engine.DBPL:
        return PowerSpectrumDBPL(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=r_star, ubarf_in=ubarf_in
        )
    raise ValueError(f"Invalid engine: {engine}")
