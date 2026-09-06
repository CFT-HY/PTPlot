"""Sound Shell Model (SSM) power spectrum."""

# from functools import lru_cache
import logging
import typing as tp

import numpy as np
from pttools.bubble import Bubble
from pttools.models import BagModel, Model
from pttools.omgw0 import G0, GS0, Spectrum, Suppression, SuppressionMethod
from pttools.omgw0 import z as z_func
from pttools.ssm.suppression import DEFAULT_SUPPRESSION

from ptplot.science import const
from ptplot.science.spectrum.base import Engine, PowerSpectrum
import ptplot.science.type_hints as th

BAG = BagModel(alpha_n_min=0.0001)

logger = logging.getLogger(__name__)


class PowerSpectrumSSM(PowerSpectrum):
    """Sound Shell Model (SSM) power spectrum.

    Uses PTtools to compute the fluid velocity profile and the resulting GW power spectrum.
    """

    COLOR = "blue"
    ENGINE: Engine = Engine.SSM
    NAME: str = "Sound Shell Model"
    SHORT_NAME: str = "SSM"

    def __init__(
            self,
            beta_over_H: float | None = None,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            v_wall: float | None = None,
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            zp: float = const.DEFAULT_ZP,
            alpha: float | None = None,
            k_turb: float = const.DEFAULT_K_TURB,
            r_star: float | None = None,
            ubarf: float | None = None,
            model: Model = BAG,
            bubble: Bubble | None = None,
            parallel: bool = True):
        super().__init__(
            beta_over_H=beta_over_H,
            T_star=T_star,
            g_star=g_star,
            v_wall=v_wall,
            # cs=TODO
            adiabatic_index=adiabatic_index,
            zp=zp,
            alpha=alpha,
            k_turb=k_turb,
            r_star=r_star,
            ubarf=ubarf,
            parallel=parallel
        )
        if self.v_wall is None or np.isnan(self.v_wall):
            raise ValueError(f"Sound Shell Model requires v_wall to be set. Got v_wall={v_wall}.")

        self.model: Model = model
        self.bubble: Bubble = Bubble(model=self.model, v_wall=self.v_wall, alpha_n=self.alpha) \
            if bubble is None else bubble

    def power_spectrum(
            self,
            f: th.FloatArr1D,
            log_errors: bool = True,
            g0: float = G0,
            gs0: float = GS0,
            suppression: Suppression = DEFAULT_SUPPRESSION,
            suppression_method: SuppressionMethod = SuppressionMethod.EXT_CONSTANT) -> th.FloatArr1D:
        """Power spectrum from the Sound Shell Model.

        The result is multiplied by $h^2$ to get a quantity that is independent of $h$,
        as is done for the other models (BPL and DBPL).
        """
        z = None
        try:
            if np.isnan(f).any():
                raise ValueError("f must not contain nan values.")
            z = tp.cast(
                "th.FloatArr1D",
                z_func(f=f, T_star=self.T_star, r_star=self.r_star, g_star=self.g_star)
            )
            if np.isnan(z).any():
                raise ValueError("z must not contain nan values.")
            spectrum = Spectrum(
                bubble=self.bubble,
                y=z,
                beta_tilde=self.beta_over_H_given,
                g_star=self.g_star,
                r_star=self.r_star_given,
                T_star=self.T_star,
                suppression=suppression,
                suppression_method=suppression_method,
                parallel=self.parallel
            )
            return const.H2 * spectrum.omgw0(g0=g0, gs0=gs0)
        except Exception as exc:
            if log_errors:
                if z is None:
                    z_min = z_max = None
                else:
                    z_min = z.min()
                    z_max = z.max()
                logger.exception(
                    "Could not create SSM power spectrum with r_star=%s, g_star=%s, Tn=%s, "
                    "f = %.3e - %.3e, z = %.3e - %.3e (%s points)",
                    self.r_star, self.g_star, self.T_star, f.min(), f.max(), z_min, z_max, f.size,
                    exc_info=exc
                )
            raise exc


# @lru_cache(maxsize=256)
# def bubble(model: Model, v_wall: float, alpha_n: float) -> Bubble:
#     """Caching Bubble generator for speed-up"""
#     return Bubble(model=model, v_wall=v_wall, alpha_n=alpha_n)
