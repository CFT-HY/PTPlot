"""Sound Shell Model (SSM) power spectrum."""

# from functools import lru_cache
import logging
import typing as tp

import numpy as np
from pttools.bubble import Bubble, SolutionType
from pttools.models import BagModel, Model
from pttools.omgw0 import G0, GS0, Spectrum, Suppression, SuppressionMethod
from pttools.omgw0 import z as z_func
from pttools.ssm.suppression import DEFAULT_SUPPRESSION

from ptplot.science import const
from ptplot.science.noise import Noise, resolve_noise
from ptplot.science.spectrum.base import Engine, PowerSpectrum
from ptplot.science.type_hints import FloatArr1D

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
        self.model: Model = model
        # Compute the bubble early if possible so that it can be used for nucleation suppression.
        self._bubble: Bubble | None = Bubble(model=model, v_wall=v_wall, alpha_n=alpha) \
            if bubble is None and not (v_wall is None or alpha is None) else None
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

        self.bubble: Bubble = Bubble(model=self.model, v_wall=self.v_wall, alpha_n=self.alpha) \
            if self._bubble is None else self._bubble

    def power_spectrum(
            self,
            f: FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = True,
            g0: float = G0,
            gs0: float = GS0,
            suppression: Suppression = DEFAULT_SUPPRESSION,
            suppression_method: SuppressionMethod = SuppressionMethod.EXT_CONSTANT) \
            -> tuple[FloatArr1D, float]:
        r"""Power spectrum $\mathcal{P}_\text{gw} h^2$ from the Sound Shell Model, and its SNR.

        The SNR is computed by :py:meth:`pttools.omgw0.spectrum.Spectrum.snr`,
        which generates the noise curve on the frequencies of the spectrum.

        .. note::
           When $\frac{\beta}{H_*}$ is given instead of $r_*$,
           PTtools computes $r_*$ with :py:func:`pttools.ssm.nucleation.r_star`,
           which differs from :py:func:`ptplot.science.utils.R_star` that is used here for the $f \to z$
           conversion. The frequencies of the returned spectrum are therefore those given in ``f``,
           whereas the SNR is integrated over the frequencies that PTtools assigns to the same $z$ values.
        """
        noise = resolve_noise(noise)
        z = None
        try:
            if np.isnan(f).any():
                raise ValueError("f must not contain nan values.")
            z = tp.cast(
                "FloatArr1D",
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
            snr, _f, _omgw0_h2, _f_noise, _noise = spectrum.snr(
                obs_time=noise.obs_time, noise_eb=noise.eb, noise_gb=noise.gb
            )
            return spectrum.omgw0_h2(g0=g0, gs0=gs0), snr
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

    def validate_alpha_ubarf(
            self,
            alpha: float | None,
            ubarf: float | None,
            v_wall: float | None,
            adiabatic_index: float,
            cs: float,
            v_cj: float | None = None,
            model: Model | None = None) -> tuple[float, float]:
        return super().validate_alpha_ubarf(
            alpha=alpha,
            ubarf=ubarf,
            v_wall=v_wall,
            adiabatic_index=adiabatic_index,
            cs=cs,
            v_cj=v_cj,
            model=self.model if model is None else model
        )

    def validate_beta_r_star(
            self,
            beta_over_H: float | None,
            r_star: float | None,
            v_wall: float | None,
            xi: FloatArr1D | None = None,
            T: FloatArr1D | None = None,
            sol_type: SolutionType | None = None,
            legacy_cs: float | None = None) -> tuple[float, float]:
        if sol_type is None:
            sol_type = SolutionType.DETON if self._bubble is None else self._bubble.sol_type
        return super().validate_beta_r_star(
            beta_over_H=beta_over_H,
            r_star=r_star,
            v_wall=v_wall,
            xi=self._bubble.xi if xi is None and self._bubble is not None else xi,
            T=tp.cast(FloatArr1D, self._bubble.T) if T is None and self._bubble is not None else T,
            sol_type=sol_type,
            legacy_cs=legacy_cs
        )

# @lru_cache(maxsize=256)
# def bubble(model: Model, v_wall: float, alpha_n: float) -> Bubble:
#     """Caching Bubble generator for speed-up"""
#     return Bubble(model=model, v_wall=v_wall, alpha_n=alpha_n)
