"""Double broken power law (DBPL) power spectrum"""

from ptplot.science import const
from ptplot.science.spectrum.base import Engine, PowerSpectrum
import ptplot.science.type_hints as th
from ptplot.science.type_hints import FloatArr


class PowerSpectrumDBPL(PowerSpectrum):
    r"""
    Double broken power law (DBPL) power spectrum

    Based on :hakkinen_ptplot:`\ `, :hakkinen_msc: and :gowling_2021:`\ `.
    """
    COLOR = "green"
    ENGINE: Engine = Engine.DBPL
    NAME: str = "Double broken power law"
    SHORT_NAME: str = "DBPL"

    def __init__(
            self,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            v_wall: float | None = None,
            alpha: float | None = None,
            beta_over_H: float | None = None,
            ubarf: float | None = None,
            r_star: float | None = None,
            cs: float = const.CS0,
            adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
            zp: float = const.DEFAULT_ZP,
            k_turb: float = const.DEFAULT_K_TURB,
            zb: float = 1.):
        super().__init__(
            T_star=T_star, g_star=g_star, v_wall=v_wall,
            alpha=alpha, beta_over_H=beta_over_H,
            ubarf=ubarf, r_star=r_star,
            cs=cs, adiabatic_ratio=adiabatic_ratio, zp=zp, k_turb=k_turb
        )
        self.zb: float = zb

        #: Ratio of the two peaks in the spectrum, $r_b = \frac{f_b}{f_p} = \frac{z_b}{z_p}$, :gowling_2021:`\ ` p. 9
        self.rb: float = self.zb / self.zp

    def m[T: (float, FloatArr)](self, b: T = 1.) -> T:
        r"""The value $m$ used in the spectral shape function M(s)

        $$m = \frac{9 r_b^4 + b}{r_b^4 + 1}$$
        :gowling_2021:`\ ` eq. 2.17.
        With $b = 1$, this reduces to
        :hindmarsh_2019:`\ ` p. 22.
        """
        return (9 * self.rb**4 + b) / (self.rb**4 + 1)

    def mu(self) -> float:
        # Todo: implement the full mu integration to get rid of the 10 % error in the approximation.
        raise NotImplementedError

    def mu_approx(self) -> float:
        r"""Prefactor $\mu(r_b)$ for the peak power of the GW power spectrum

        $$\mu(r_b) = \int_0^\infty \frac{ds}{s} M(s, r_b) \approx 4.78 - 6.27 r_b + 3.34 r_b^2$$
        This approximation is accurate to about 10 % over the relevant range $0 < r_b < 1$.
        :hindmarsh_2019:`\ ` eq. 5.8, 5.9

        This relates the peak power parameter $A_M$ to the total power parameter $\tilde{\Omega}_\text{gw}$.
        """
        return 4.78 - 6.27 * self.rb + 3.34 * self.rb**2

    def M(self, s: th.FloatOrArr, b: th.FloatOrArr = 1.) -> th.FloatOrArr:
        r"""Spectral shape of the GW power spectrum

        $$M(s, r_b, b) = s^9
        \left( \frac{1 + r_b^4}{r_b^4 + s^4} \right)^\frac{9 - b}{4}
        \left( \frac{b + 4}{b + 4 - m + ms^2} \right)^\frac{b + 4}{2}$$
        This formula is a fit to the Sound Shell Model power spectrum.
        :gowling_2021:`\ ` eq. 2.16
        With $b = 1$, this reduces to
        :hindmarsh_2019:`\ ` eq. 5.7

        :param s: Frequency $s$ relative to the peak frequency
        :param b: $b$ defines the spectral slope between the two breaks in the spectrum
        :return: Spectral shape $M(s, r_b, b)$
        """
        m = self.m(b=b)
        return s**9 * \
            ((1 + self.rb**4) / (self.rb**4 + s**4)) ** ((9 - b) / 4) * \
            ((b + 4) / (b + 4 - m + m * s**2)) ** ((b + 4) / 2)

    def power_spectrum(self, f: th.FloatOrArr, log_errors: bool = False) -> th.FloatOrArr:
        r"""Calculate power spectrum from sound waves for a given frequency f using the double broken power-law ansatz

        $$\Omega_\text{gw}^\text{fit} = F_{\text{gw},0} \Omega_p M(s, r_b, b)$$

        $F_{\text{gw},0}$ depends on the value of $h$,
        which is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.
        """
        return self.power_spectrum_common() / self.mu_approx() * self.J() * self.M(s=self.s(f))
