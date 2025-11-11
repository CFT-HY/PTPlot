import logging

import numpy as np
from pttools.bubble import Bubble
from pttools.models import BagModel, Model
from pttools.omgw0 import Spectrum, SuppressionMethod, f_star0

# Temporary
from pttools.bubble import Phase
from pttools.ssmtools import spec_den_v, pow_spec, gen_lookup, spec_den_gw_scaled, N_Z_LOOKUP_DEFAULT, lookup_limits

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
        if np.isnan(f).any():
            raise ValueError("f must not contain nan values.")
        # Todo: Use the PTtools implementation when it's available
        z = f / f_star0(Tn=self.T_star, g_star=self.g_star) * self.r_star
        if np.isnan(z).any():
            raise ValueError("z must not contain nan values.")
        try:
            # TODO: Remove gs_star when PTtools is updated
            spectrum = Spectrum(bubble=self.bubble, y=z, r_star=self.r_star, g_star=self.g_star, gs_star=self.g_star, Tn=self.T_star, compute=False)

            # Todo: Remove this temporary implementation when the PTtools fix for eps handling is available
            spectrum.cs = np.sqrt(spectrum.bubble.model.cs2(spectrum.bubble.va_enthalpy_density, Phase.BROKEN))
            spectrum.spec_den_v, spectrum.a2 = spec_den_v(
                bub=spectrum.bubble, z=spectrum.y, a=1.,
                nuc_type=spectrum.nuc_type, nt=spectrum.nt, z_st_thresh=spectrum.z_st_thresh, cs=spectrum.cs, return_a2=True
            )
            spectrum.pow_v = pow_spec(spectrum.y, spec_den=spectrum.spec_den_v)

            # spectrum.z_lookup = gen_lookup(y=spectrum.y, cs=spectrum.cs, n_z_lookup=spectrum.n_z_lookup, eps=1e-10)
            eps = 1e-8
            z_minus_min = spectrum.y.min() * 0.5 * (1. - spectrum.cs) / spectrum.cs * (1 - eps)
            z_plus_max = spectrum.y.max() * 0.5 * (1. + spectrum.cs) / spectrum.cs * (1 + eps)
            spectrum.z_lookup = np.logspace(np.log10(z_minus_min), np.log10(z_plus_max), spectrum.n_z_lookup)
            if np.isnan(spectrum.z_lookup).any():
                raise ValueError("z_lookup contains nan values")

            z_lookup_min, z_lookup_max = lookup_limits(spectrum.y, spectrum.cs)
            print(f"z_lookup_min_lim={z_lookup_min}, z_lookup_max_lim={z_lookup_max}")
            print(f"z_lookup_min_val={spectrum.z_lookup.min()}, z_lookup_max_val={spectrum.z_lookup.max()}")
            print(spectrum.z_lookup.min() < z_lookup_min, spectrum.z_lookup.max() > z_lookup_max)

            sdv2 = spec_den_v(
                bub=spectrum.bubble, z=spectrum.z_lookup, a=1.,
                nuc_type=spectrum.nuc_type, nt=spectrum.nt, z_st_thresh=spectrum.z_st_thresh, cs=spectrum.cs
            )
            spectrum.spec_den_gw, y = spec_den_gw_scaled(
                z_lookup=spectrum.z_lookup, P_v_lookup=sdv2, y=spectrum.y, cs=spectrum.cs,
                source_lifetime_factor=spectrum.source_lifetime_factor
            )
            spectrum.pow_gw = pow_spec(spectrum.y, spec_den=spectrum.spec_den_gw)
        except ValueError as e:
            logger.error(
                "Could not create SSM spectrum with r_star=%s, g_star=%s, Tn=%s, z = %.3e - %.3e (%s points)",
                self.r_star, self.g_star, self.T_star, z.min(), z.max(), z.size)
            raise e
        return const.H_PLANCK2 * spectrum.omgw0(suppression=self.suppression)
