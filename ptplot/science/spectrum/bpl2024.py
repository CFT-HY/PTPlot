"""Broken power law (BPL) power spectrum of Caprini et al. (2024)."""

from ptplot.science.spectrum.base import Engine
from ptplot.science.spectrum.base2024 import PowerSpectrum2024


class PowerSpectrumBPL2024(PowerSpectrum2024):
    r"""Broken power law (BPL) power spectrum of Caprini et al. (2024).

    Template I of :caprini_2024:`\ ` sec. 2.1 for bubble collisions and highly relativistic fluid shells
    in very strong phase transitions ($\alpha \gg 1$), based on the simulations of Lewicki & Vaskonen (2022).
    Equation and page numbers refer to arXiv:2403.03723v2.

    $$\Omega_{\text{gw}}(f) = \Omega_b \left( \frac{f}{f_b} \right)^{n_1}
    \left[ \frac{1}{2} + \frac{1}{2} \left( \frac{f}{f_b} \right)^{a_1} \right]^\frac{n_2 - n_1}{a_1}$$
    :caprini_2024:`\ ` eq. 2.4
    """

    COLOR = "purple"
    ENGINE: Engine = Engine.BPL2024
    NAME: str = "Broken power law (2024)"
    SHORT_NAME: str = "BPL2024"

    #: $A_{\text{str}}$, amplitude constant, :caprini_2024:`\ ` p. 7
    A_STR: float = 0.05
    #: $f_p (\beta / H_*)^{-1} / H_{\ast,0}$, :caprini_2024:`\ ` eq. 2.7
    FP_COEFF: float = 0.11
    SLOPES: tuple[float, ...] = (2.4, -2.4)
    SMOOTHNESS: tuple[float, ...] = (1.2,)

    @property
    def K_tilde(self) -> float:
        r"""$\tilde{K}$, fractional energy density of the GW source.

        $$\tilde{K} \equiv \frac{\alpha}{1 + \alpha}$$
        :caprini_2024:`\ ` p. 8
        """
        return self.alpha / (1 + self.alpha)

    def f_b(self) -> float:
        r"""$f_b$, break frequency.

        $$f_b = f_p \left( -\frac{n_1}{n_2} \right)^{-1/a_1}$$
        Inverted from :caprini_2024:`\ ` p. 6.
        For $n_1 = -n_2$, $f_b = f_p$.
        """
        n1, n2 = self.SLOPES
        return self.f_peak() * (-n1 / n2)**(-1 / self.SMOOTHNESS[0])

    def f_breaks(self) -> tuple[float, ...]:
        return (self.f_b(),)

    def f_peak(self) -> float:
        r"""$f_p$, peak frequency.

        $$f_p \simeq 0.11 H_{\ast,0} \frac{\beta}{H_*}$$
        :caprini_2024:`\ ` eq. 2.7
        """
        return self.FP_COEFF * self.h_star() * self.beta_tilde

    def f_ref(self) -> float:
        return self.f_b()

    def omega_b_h2(self) -> float:
        r"""$h^2 \Omega_b$, amplitude of the spectrum at the break frequency $f_b$.

        $$\Omega_b = \Omega_p \left[
        \frac{1}{2} \left( -\frac{n_2}{n_1} \right)^\frac{n_1}{n_1 - n_2}
        + \frac{1}{2} \left( -\frac{n_1}{n_2} \right)^{-\frac{n_2}{n_1 - n_2}}
        \right]^\frac{n_1 - n_2}{a_1}$$
        Inverted from :caprini_2024:`\ ` eq. 2.5.
        For $n_1 = -n_2$, $\Omega_b = \Omega_p$.
        """
        n1, n2 = self.SLOPES
        a1 = self.SMOOTHNESS[0]
        bracket = 0.5 * (-n2 / n1)**(n1 / (n1 - n2)) + 0.5 * (-n1 / n2)**(-n2 / (n1 - n2))
        return self.omega_p_h2() * bracket**((n1 - n2) / a1)

    def omega_p_h2(self) -> float:
        r"""$h^2 \Omega_p$, peak amplitude of the spectrum.

        $$h^2 \Omega_p = h^2 F_{\text{gw},0} A_{\text{str}} \tilde{K}^2 \left( \frac{H_*}{\beta} \right)^2$$
        :caprini_2024:`\ ` eq. 2.7
        """
        return float(self.F_gw0_h2()) * self.A_STR * self.K_tilde**2 / self.beta_tilde**2

    def omega_ref_h2(self) -> float:
        return self.omega_b_h2()
