"""Double broken power law (DBPL) power spectrum of Caprini et al. (2024)."""

import typing as tp

import numpy as np

from ptplot.science.spectrum.base2024 import PowerSpectrum2024
from ptplot.science.spectrum.engine import Engine


class PowerSpectrumDBPL2024(PowerSpectrum2024):
    r"""Double broken power law (DBPL) power spectrum of Caprini et al. (2024).

    Template II of :caprini_2024:`\ ` sec. 2.2 with the sound wave parameters of sec. 2.2.1,
    which are based on the Higgsless simulations of :jinno_2023:`\ `.
    Equation and page numbers refer to arXiv:2403.03723v2.

    $$\Omega_{\text{gw}}(f) = \Omega_{\text{int}} S(f) = \Omega_2 S_2(f)$$
    :caprini_2024:`\ ` eq. 2.8
    """

    COLOR = "orange"
    ENGINE: tp.ClassVar[Engine] = Engine.DBPL2024
    TABLE = f"spectra_{ENGINE}"
    NAME: tp.ClassVar[str] = "Double broken power law (2024)"
    SHORT_NAME: tp.ClassVar[str] = "DBPL2024"

    REQUIRE_SOUND_SHELL_THICKNESS = True
    REQUIRE_V_WALL = True

    #: $A_{\text{sw}}$, amplitude constant, :caprini_2024:`\ ` p. 10
    A_SW: tp.ClassVar[float] = 0.11
    #: Efficiency of producing bulk kinetic energy relative to a single bubble.
    #: "This accounts for the efficiency in producing kinetic energy in the bulk fluid motion
    #: with respect to the single bubble case" :caprini_2024:`\ ` p. 10.
    #: This was found in :jinno_2023:`\ `.
    #: See also the discussion in :caprini_2024_weak_strong:`\ `.
    K_EFFICIENCY: tp.ClassVar[float] = 0.6
    #: $f_1 \frac{H_* R_*}{H_{\ast,0}}$, :caprini_2024:`\ ` eq. 2.9
    F1_COEFF: tp.ClassVar[float] = 0.2
    #: $f_2 \Delta_w \frac{H_* R_*}{H_{\ast,0}}$, :caprini_2024:`\ ` eq. 2.9
    F2_COEFF: tp.ClassVar[float] = 0.5
    SLOPES: tp.ClassVar[tuple[float, ...]] = (3., 1., -3.)
    SMOOTHNESS: tp.ClassVar[tuple[float, ...]] = (2., 4.)

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
        """$f_1, f_2$, break frequencies."""
        return self.f1(), self.f2()

    def f_ref(self) -> float:
        """$f_2$, the reference frequency is the second break frequency."""
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
        """
        return super().kinetic_energy_fraction

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
        r"""$h^2 \Omega_2$, the spectrum is normalized at the second break frequency."""
        return self.omega_2_h2()
