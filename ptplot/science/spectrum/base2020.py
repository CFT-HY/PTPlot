r"""Base class for the power law templates of :caprini_2020:`\ ` and :gowling_2021:`\ `."""

import abc
import typing as tp

from pttools.omgw0 import f as f_func
from pttools.omgw0 import f_star0
from pttools.utils.fields import Fields

from ptplot.science.const import DEFAULT_ADIABATIC_INDEX, DEFAULT_G_STAR, DEFAULT_OMEGA_TILDE_GW, DEFAULT_T_STAR
from ptplot.science.spectrum.base import PowerSpectrum
from ptplot.science.spectrum.export import ANALYTIC_SPECTRUM_FIELDS
from ptplot.science.type_hints import FloatOrArr

DEFAULT_ZP: int = 10
r"""
This default value is determine from simulations,
and accounts for the observed peak value of $kR_*$.
When $v_{\text{wall}} \approx v_{\text{CJ}}$, the value of $z_p$ may differ from 10,
as the sound shells are so thin that they may set a substantially smaller length scale
$\Delta R_* = R_* \frac{\lvert v_{\text{wall}} - c_s \rvert}{c_s}$.
:caprini_2020:`\ ` p. 17
"""


class PowerSpectrum2020(PowerSpectrum, abc.ABC):
    r"""Base class for the power law templates of :caprini_2020:`\ ` and :gowling_2021:`\ `."""

    FIELDS: tp.ClassVar[Fields] = ANALYTIC_SPECTRUM_FIELDS
    SUPPORTS_F_STAR0_FACTOR = True

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
            parallel: bool = True,
            # Model-specific parameters
            zp: float = DEFAULT_ZP,
        ):
        """Create a BPL power spectrum.

        :param zp: $z_p$, peak angular frequency in units of the mean bubble separation
        """
        super().__init__(
            v_wall=v_wall,
            alpha=alpha,
            beta_tilde=beta_tilde,
            ubarf=ubarf,
            r_star=r_star,
            T_star=T_star,
            g_star=g_star,
            adiabatic_index=adiabatic_index,
            f_star0_factor=f_star0_factor,
            legacy_nucleation_cs_max=legacy_nucleation_cs_max,
            parallel=parallel
        )
        #: $z_p$, peak angular frequency in units of the mean bubble separation
        self.zp: float = zp

    def f_peak(self) -> float:
        r"""Peak frequency.

        $$f_{p,0} \approx 26
        \left( \frac{1}{H_* R_*} \right)
        \left( \frac{z_p}{10} \right)
        \left( \frac{T_*}{100 \text{GeV}} \right)
        \left( \frac{g_*}{100} \right)^{1/6}
        \text{µHz}$$
        :hindmarsh_2017:`\ ` eq. 43
        :caprini_2020:`\ ` eq. 31
        These equations are equivalent to :gowling_2021:`\ ` eq. 2.12, 2.13.
        The $f_{\ast,0}$ of :py:func:`pttools.omgw0.freq.f_star0` is multiplied by :py:attr:`f_star0_factor`.

        :return: Peak frequency $f_\text{peak}$ in Hz
        """
        f_star0_value = self.f_star0_factor * f_star0(T_star=self.T_star, ge_star=self.g_star)
        return tp.cast(float, f_func(z=self.zp, r_star=self.r_star, f_star0=f_star0_value))

    def power_spectrum_common(self, omega_tilde_gw: float = DEFAULT_OMEGA_TILDE_GW) -> float:
        r"""Compute the common prefactor of the power spectrum for BPL2020 and DBPL2021.

        $$3h^2 F_{\text{gw},0} \Gamma^2 \bar{U}_f^4 \tilde{\Omega}_\text{gw}$$

        Note that $F_{\text{gw},0}$ depends on the value of $h$.
        This is why the result is multiplied by $h^2$ to get a quantity that is independent of $h$.

        Note that this equation has $(\Gamma \bar{U}_f^2)^2$,
        which does not exactly equal the kinetic energy fraction $K$.
        """
        return 3 * tp.cast(float, self.F_gw0_h2()) * (self.adiabatic_index * self.ubarf**2)**2 * omega_tilde_gw

    def s[T: FloatOrArr](self, f: T) -> T:
        r"""Relative frequency $s$ with respect to the peak frequency.

        $$s = \frac{f}{f_{\text{peak}}}$$
        :gowling_2021:`\ ` p. 9
        """
        return tp.cast(T, f / self.f_peak())
