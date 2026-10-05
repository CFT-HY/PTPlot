"""Double broken power law (DBPL) power spectrum of Gowling & Hindmarsh (2021)."""

import typing as tp

from ptplot.science.const import DEFAULT_ADIABATIC_INDEX, DEFAULT_G_STAR, DEFAULT_T_STAR
from ptplot.science.noise import Noise
from ptplot.science.spectrum.base2020 import DEFAULT_ZP, PowerSpectrum2020
from ptplot.science.spectrum.engine import Engine
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatOrArr


class PowerSpectrumDBPL2021(PowerSpectrum2020):
    r"""
    Double broken power law (DBPL) power spectrum of Gowling & Hindmarsh (2021).

    Based on :hakkinen_ptplot:`\ `, :hakkinen_msc:`\ ` and :gowling_2021:`\ `.
    """

    COLOR = "green"
    ENGINE: tp.ClassVar[Engine] = Engine.DBPL2021
    TABLE = f"spectra_{ENGINE}"
    NAME: tp.ClassVar[str] = "Double broken power law (2021)"
    SHORT_NAME: tp.ClassVar[str] = "DBPL2021"

    OLD_J = True

    def __init__(
            self,
            # Primary parameters
            v_wall: float | None = None,
            alpha: float | None = None,
            beta_tilde: float | None = None,
            ubarf: float | None = None,
            r_star: float | None = None,
            T_star: float = DEFAULT_T_STAR,
            g_star: float = DEFAULT_G_STAR,
            # Additional parameters
            adiabatic_index: float = DEFAULT_ADIABATIC_INDEX,
            f_star0_factor: float = 1.,
            # Switches
            legacy_nucleation_cs_max: bool = False,
            # Model-specific parameters
            zb: float = 1.0,
            zp: float = DEFAULT_ZP,
        ):
        """Create a DBPL power spectrum.

        :param zb: $z_b$, angular frequency of the lower break in units of the mean bubble separation
        :param zp: $z_p$, peak angular frequency in units of the mean bubble separation
        """
        super().__init__(
            T_star=T_star, g_star=g_star, v_wall=v_wall,
            alpha=alpha, beta_tilde=beta_tilde,
            ubarf=ubarf, r_star=r_star,
            adiabatic_index=adiabatic_index,
            f_star0_factor=f_star0_factor,
            legacy_nucleation_cs_max=legacy_nucleation_cs_max,
            zp=zp,
        )
        self.zb: float = zb

        #: Ratio of the two peaks in the spectrum, $r_b = \frac{f_b}{f_p} = \frac{z_b}{z_p}$, :gowling_2021:`\ ` p. 9
        self.rb: float = self.zb / self.zp

    def m[T: FloatOrArr](self, b: T = 1.) -> T:
        r"""Compute the value $m$ used in the spectral shape function M(s).

        $$m = \frac{9 r_b^4 + b}{r_b^4 + 1}$$
        :gowling_2021:`\ ` eq. 2.17.
        With $b = 1$, this reduces to
        :gw_pt_ssm:`\ ` p. 22.
        """
        return tp.cast(T, (9 * self.rb**4 + b) / (self.rb**4 + 1))

    def mu(self) -> float:
        r"""Prefactor $\mu(r_b)$ for the peak power of the GW power spectrum, computed exactly.

        This has not been implemented yet. Please use :py:meth:`mu_approx` instead.

        :raises NotImplementedError: Always
        """
        # Todo: implement the full mu integration to get rid of the 10 % error in the approximation.
        raise NotImplementedError

    def mu_approx(self) -> float:
        r"""Prefactor $\mu(r_b)$ for the peak power of the GW power spectrum.

        $$\mu(r_b) = \int_0^\infty \frac{ds}{s} M(s, r_b) \approx 4.78 - 6.27 r_b + 3.34 r_b^2$$
        This approximation is accurate to about 10 % over the relevant range $0 < r_b < 1$.
        :gw_pt_ssm:`\ ` eq. 5.8, 5.9

        This relates the peak power parameter $A_M$ to the total power parameter $\tilde{\Omega}_\text{gw}$.
        """
        return 4.78 - 6.27 * self.rb + 3.34 * self.rb**2

    def M(self, s: th.FloatOrArr, b: th.FloatOrArr = 1.) -> th.FloatOrArr:
        r"""Spectral shape of the GW power spectrum.

        $$M(s, r_b, b) = s^9
        \left( \frac{1 + r_b^4}{r_b^4 + s^4} \right)^\frac{9 - b}{4}
        \left( \frac{b + 4}{b + 4 - m + ms^2} \right)^\frac{b + 4}{2}$$
        This formula is a fit to the Sound Shell Model power spectrum.
        :gowling_2021:`\ ` eq. 2.16
        With $b = 1$, this reduces to
        :gw_pt_ssm:`\ ` eq. 5.7

        :param s: Frequency $s$ relative to the peak frequency
        :param b: $b$ defines the spectral slope between the two breaks in the spectrum
        :return: Spectral shape $M(s, r_b, b)$
        """
        m = self.m(b=b)
        return s**9 * \
            ((1 + self.rb**4) / (self.rb**4 + s**4)) ** ((9 - b) / 4) * \
            ((b + 4) / (b + 4 - m + m * s**2)) ** ((b + 4) / 2)

    def power_spectrum(
            self,
            f: th.FloatArr1D,
            noise: Noise | None = None,
            log_errors: bool = False) -> tuple[th.FloatArr1D, float]:  # noqa: ARG002
        r"""Calculate power spectrum from sound waves for a given frequency f using the double broken power-law ansatz.

        $$\Omega_\text{gw}^\text{fit} = F_{\text{gw},0} \Omega_p M(s, r_b, b)$$

        $F_{\text{gw},0}$ depends on the value of $h$,
        which is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.
        """
        power_spectrum = tp.cast(
            th.FloatArr1D,
            self.power_spectrum_common() / self.mu_approx() * self.J() * self.M(s=self.s(f))
        )
        return self.snr_and_store(f, power_spectrum, noise)
