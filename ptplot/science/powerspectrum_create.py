from pttools.models import ConstCSModel, Model
from pttools.omgw0 import SuppressionMethod

from ptplot.science import const
from ptplot.science.engine import Engine
from ptplot.science.powerspectrum import PowerSpectrum
from ptplot.science.powerspectrum_dbpl import PowerSpectrumDBPL
from ptplot.science.powerspectrum_ssm import PowerSpectrumSSM, bag


def power_spectrum(
        beta_over_H: float = None,
        T_star: float = const.DEFAULT_T_STAR,
        g_star: float = const.DEFAULT_G_STAR,
        vw: float = None,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        zp: float = const.DEFAULT_ZP,
        alpha: float = None,
        k_turb: float = const.DEFAULT_K_TURB,
        H_rstar: float = None,
        ubarf_in: float = None,
        engine: Engine = Engine.DEFAULT,
        css2: float = None,
        csb2: float = None,
        suppression: SuppressionMethod = SuppressionMethod.NONE,
        model: Model = bag) -> PowerSpectrum:
    if engine == Engine.DEFAULT:
        return PowerSpectrum(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=H_rstar, ubarf_in=ubarf_in
        )
    elif engine == Engine.SSM:
        if (css2 is not None or csb2 is not None) and model is bag:
            model = ConstCSModel(css2=css2, csb2=csb2)
        return PowerSpectrumSSM(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=H_rstar, ubarf_in=ubarf_in,
            suppression=suppression, model=model
        )
    elif engine == Engine.DBPL:
        return PowerSpectrumDBPL(
            beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            vw=vw, adiabatic_ratio=adiabatic_ratio, zp=zp,
            alpha=alpha, k_turb=k_turb, r_star=H_rstar, ubarf_in=ubarf_in
        )
    raise ValueError(f"Invalid engine: {engine}")
