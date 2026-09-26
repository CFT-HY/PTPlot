"""Double broken power law (DBPL) power spectrum of Caprini et al. (2024)."""

import typing as tp

import numpy as np

from ptplot.science import const
from ptplot.science.spectrum.base import Engine
from ptplot.science.spectrum.base2024 import PowerSpectrum2024


class PowerSpectrumDBPL2024(PowerSpectrum2024):
    r"""Double broken power law (DBPL) power spectrum of Caprini et al. (2024).

    Template II of :caprini_2024:`\ ` sec. 2.2 with the sound wave parameters of sec. 2.2.1,
    which are based on the Higgsless simulations of :jinno_2023:`\ `.
    Equation and page numbers refer to arXiv:2403.03723v2.

    $$\Omega_{\text{gw}}(f) = \Omega_{\text{int}} S(f) = \Omega_2 S_2(f)$$
    :caprini_2024:`\ ` eq. 2.8
    """

    COLOR = "orange"
    ENGINE: Engine = Engine.DBPL2024
    NAME: str = "Double broken power law (2024)"
    SHORT_NAME: str = "DBPL2024"

    #: $A_{\text{sw}}$, amplitude constant, :caprini_2024:`\ ` p. 10
    A_SW: float = 0.11
    #: Efficiency of producing bulk kinetic energy relative to a single bubble.
    #: "This accounts for the efficiency in producing kinetic energy in the bulk fluid motion
    #: with respect to the single bubble case" :caprini_2024:`\ ` p. 10.
    #: This was found in :jinno_2023:`\ `.
    #: See also the discussion in :caprini_weak_strong:`\ `.
    K_EFFICIENCY: float = 0.6
    #: $f_1 \frac{H_* R_*}{H_{\ast,0}}$, :caprini_2024:`\ ` eq. 2.9
    F1_COEFF: float = 0.2
    #: $f_2 \Delta_w \frac{H_* R_*}{H_{\ast,0}}$, :caprini_2024:`\ ` eq. 2.9
    F2_COEFF: float = 0.5
    SLOPES: tuple[float, ...] = (3., 1., -3.)
    SMOOTHNESS: tuple[float, ...] = (2., 4.)

    def __init__(
            self,
            T_star: float = const.DEFAULT_T_STAR,
            g_star: float = const.DEFAULT_G_STAR,
            v_wall: float | None = None,
            alpha: float | None = None,
            beta_tilde: float | None = None,
            ubarf: float | None = None,
            r_star: float | None = None,
            cs: float = const.CS0,
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            zp: float = const.DEFAULT_ZP,
            k_turb: float = const.DEFAULT_K_TURB,
            parallel: bool = True,
            legacy_nucleation_cs_max: bool = False):
        super().__init__(
            T_star=T_star, g_star=g_star, v_wall=v_wall,
            alpha=alpha, beta_tilde=beta_tilde,
            ubarf=ubarf, r_star=r_star,
            cs=cs, adiabatic_index=adiabatic_index, zp=zp, k_turb=k_turb,
            parallel=parallel, legacy_nucleation_cs_max=legacy_nucleation_cs_max
        )
        if self.v_wall is None or np.isnan(self.v_wall):
            raise ValueError(f"The DBPL2024 spectrum requires v_wall to be set. Got v_wall={v_wall}.")
        if np.isclose(self.v_wall, cs):
            raise ValueError(f"The sound shell thickness is zero for v_wall=cs={cs}.")
        #: $c_s$, speed of sound
        self.cs: float = cs

    @property
    def delta_w(self) -> float:
        r"""$\Delta_w$, relative sound shell thickness.

        $$\Delta_w = \frac{\xi_{\text{shell}}}{\max(\xi_w, c_s)}$$
        :caprini_2024:`\ ` p. 10
        """
        return self.xi_shell / max(tp.cast(float, self.v_wall), self.cs)

    @property
    def xi_shell(self) -> float:
        r"""$\xi_{\text{shell}}$, dimensionless sound shell thickness.

        $$\xi_{\text{shell}} = \lvert \xi_w - c_s \rvert$$
        :caprini_2024:`\ ` p. 11.
        This is valid for subsonic deflagrations and detonations, but not for hybrids.
        """
        return abs(tp.cast(float, self.v_wall) - self.cs)

    def f1(self) -> float:
        r"""$f_1$, first break frequency.

        $$f_1 \simeq 0.2 H_{\ast,0} (H_* R_*)^{-1}$$
        :caprini_2024:`\ ` eq. 2.9
        """
        return self.F1_COEFF * self.h_star() / self.r_star

    def f2(self) -> float:
        r"""$f_2$, second break frequency.

        $$f_2 \simeq 0.5 H_{\ast,0} \Delta_w^{-1} (H_* R_*)^{-1}$$
        :caprini_2024:`\ ` eq. 2.9
        """
        return self.F2_COEFF * self.h_star() / (self.delta_w * self.r_star)

    def f_breaks(self) -> tuple[float, ...]:
        return self.f1(), self.f2()

    def f_ref(self) -> float:
        return self.f2()

    @property
    def H_star_eta_sh(self) -> float:
        r"""$\mathcal{H}_* \eta_{\text{sh}}$, Hubble-scaled shock formation time.

        $$\mathcal{H}_* \eta_{\text{sh}} = \frac{r_*}{\sqrt{\bar{v}_f^2}}, \quad \bar{v}_f^2 = \frac{K}{\Gamma}$$
        :caprini_2024:`\ ` p. 11, as $H_* \tau_{\text{sh}} = H_* R_* / \sqrt{\bar{v}_f^2}$.
        This overrides the base class version,
        as $K$ includes the efficiency factor 0.6 of :py:attr:`kinetic_energy_fraction`.
        """
        return self.r_star / np.sqrt(self.kinetic_energy_fraction / self.adiabatic_index)

    @property
    def H_star_eta_sw(self) -> float:
        r"""$\mathcal{H}_* \eta_{\text{sw}}$, Hubble-scaled duration of the sound wave source.

        $$\mathcal{H}_* \eta_{\text{sw}} = \min(\mathcal{H}_* \eta_{\text{sh}}, 1)$$
        :caprini_2024:`\ ` p. 10, as $H_* \tau_{\text{sw}} = \min(H_* \tau_{\text{sh}}, 1)$.
        """
        return min(self.H_star_eta_sh, 1.)

    @property
    def kinetic_energy_fraction(self) -> float:
        r"""$K$, kinetic energy fraction.

        $$K \simeq 0.6 \kappa \frac{\alpha}{1 + \alpha} \approx 0.6 \Gamma \bar{U}_f^2$$
        :caprini_2024:`\ ` p. 10.
        The factor 0.6 is the efficiency of producing bulk kinetic energy relative to a single bubble.
        The single bubble kinetic energy fraction $\kappa \alpha / (1 + \alpha)$ is approximated with
        :py:attr:`kinetic_energy_fraction_approx`.
        """
        return self.K_EFFICIENCY * self.kinetic_energy_fraction_approx

    def omega_int_h2(self) -> float:
        r"""$h^2 \Omega_{\text{int}}$, integrated amplitude of the spectrum.

        $$h^2 \Omega_{\text{int}} = h^2 F_{\text{gw},0} A_{\text{sw}} K^2 (\mathcal{H}_* \eta_{\text{sw}}) r_*$$
        :caprini_2024:`\ ` eq. 2.10, with $H_* \tau_{\text{sw}}$ and $H_* R_*$.
        """
        return tp.cast(float, self.F_gw0_h2()) * self.A_SW * self.kinetic_energy_fraction**2 \
            * self.H_star_eta_sw * self.r_star

    def omega_2_h2(self) -> float:
        r"""$h^2 \Omega_2$, amplitude of the spectrum at the second break frequency $f_2$.

        $$\Omega_2 = \frac{1}{\pi} \left( \sqrt{2} + \frac{2 f_2 / f_1}{1 + f_2^2 / f_1^2} \right) \Omega_{\text{int}}$$
        :caprini_2024:`\ ` eq. 2.12.
        This is valid only for the sound wave slopes $n_1 = 3$, $n_2 = 1$, $n_3 = -3$, $a_1 = 2$, $a_2 = 4$.
        """
        r = self.f2() / self.f1()
        return (np.sqrt(2) + 2 * r / (1 + r**2)) / np.pi * self.omega_int_h2()

    def omega_ref_h2(self) -> float:
        return self.omega_2_h2()
