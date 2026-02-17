"""Sound Shell Model (SSM) power spectrum"""

import logging

import numpy as np
from pttools.bubble import Bubble
from pttools.models import BagModel, Model
from pttools.omgw0 import G0, GS0, Spectrum, Suppression, SuppressionMethod, f_star0
from pttools.omgw0.suppression import DEFAULT as SUPPRESSION_DEFAULT

from ptplot.science import const
from ptplot.science.engine import ENGINE_NAMES, Engine
from ptplot.science.spectrum.base import PowerSpectrum
import ptplot.science.type_hints as th

bag = BagModel(alpha_n_min=0.001)

logger = logging.getLogger(__name__)


class PowerSpectrumSSM(PowerSpectrum):
    ENGINE: Engine = Engine.SSM
    NAME: str = ENGINE_NAMES[ENGINE]
    SHORT_NAME: str = ENGINE.name

    def __init__(
            self,
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
            model: Model = bag):
        super().__init__(
            beta_over_H=beta_over_H,
            T_star=T_star,
            g_star=g_star,
            vw=vw,
            adiabatic_ratio=adiabatic_ratio,
            zp=zp,
            alpha=alpha,
            k_turb=k_turb,
            r_star=r_star,
            ubarf_in=ubarf_in,
        )
        if self.vw is None or np.isnan(vw):
            raise ValueError(f"Sound Shell Model requires vw to be set. Got vw={vw}.")

        self.model: Model = model
        self.bubble: Bubble = Bubble(model=self.model, v_wall=self.vw, alpha_n=self.alpha)

    def K(self) -> float:
        # Todo: Use the value from the SSM Spectrum object
        return super().K()

    def power_spectrum(
            self,
            f: th.FloatArr1D,
            g0: float = G0,
            gs0: float = GS0,
            sup: Suppression = SUPPRESSION_DEFAULT,
            sup_method: SuppressionMethod = SuppressionMethod.NONE) -> th.FloatArr1D:
        """Power spectrum from the Sound Shell Model

        The result is multiplied by $h^2$ to get a quantity that is independent of $h$,
        as is done for the other models (BPL and DBPL).
        """
        if np.isnan(f).any():
            raise ValueError("f must not contain nan values.")
        # Todo: Use pttools.omgw0.freq.z() instead when it's available
        z = f / f_star0(Tn=self.T_star, g_star=self.g_star) * self.r_star
        if np.isnan(z).any():
            raise ValueError("z must not contain nan values.")
        try:
            spectrum = Spectrum(bubble=self.bubble, y=z, r_star=self.r_star, g_star=self.g_star, Tn=self.T_star)
        except ValueError as e:
            logger.error(
                "Could not create SSM spectrum with r_star=%s, g_star=%s, Tn=%s, z = %.3e - %.3e (%s points)",
                self.r_star, self.g_star, self.T_star, z.min(), z.max(), z.size)
            raise e
        return const.H_PLANCK2 * spectrum.omgw0(g0=g0, gs0=gs0, sup=sup, sup_method=sup_method)
