import logging

import numpy as np
from pttools.bubble import Bubble
from pttools.models import BagModel, Model
from pttools.omgw0 import Spectrum, SuppressionMethod, f_star0

from ptplot.science import const
from ptplot.science.engine import ENGINE_NAMES, Engine
from ptplot.science.spectrum.base import PowerSpectrum

bag = BagModel()

logger = logging.getLogger(__name__)


class PowerSpectrumSSM(PowerSpectrum):
    ENGINE: Engine = Engine.SSM
    NAME: str = ENGINE_NAMES[ENGINE]
    SHORT_NAME: str = ENGINE.name

    def __init__(
            self,
            beta_over_H: float = None,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            vw: float = None,
            adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
            zp: float = const.DEFAULT_ZP,
            alpha: float = None,
            k_turb: float = const.DEFAULT_K_TURB,
            r_star: float = None,
            ubarf_in: float = None,
            suppression: SuppressionMethod = SuppressionMethod.NONE,
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

        self.suppression: SuppressionMethod = suppression
        self.model: Model = model
        self.bubble: Bubble = Bubble(model=self.model, v_wall=self.vw, alpha_n=self.alpha)

    def power_spectrum(self, f: np.ndarray) -> np.ndarray:
        if self.g_star is None:
            raise ValueError("g_star is required for converting Sound Shell Model spectra to present frequencies.")
        # Todo: add proper conversion here
        r_star = self.r_star
        # Todo: add this function to PTtools
        z = f / f_star0(Tn=self.T_star, g_star=self.g_star) * r_star
        # TODO: Remove gs_star when the typo in PTtools is fixed
        try:
            spectrum = Spectrum(bubble=self.bubble, y=z, r_star=r_star, g_star=self.g_star, gs_star=self.g_star, Tn=self.T_star)
        except ValueError as e:
            logger.error("Could not create SSM spectrum with z=%s", z)
            raise e
        return const.H_PLANCK2 * spectrum.omgw0(suppression=self.suppression)
