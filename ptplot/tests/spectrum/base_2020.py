"""Tests for BPL 2020 and DBPL 2021."""

import abc

import pytest

from ptplot.science.noise import noise_curve
from ptplot.science.spectrum.base2020 import PowerSpectrum2020
from ptplot.tests.spectrum.base import PowerSpectrumBaseCase


class PowerSpectrumBaseCase2020[S: PowerSpectrum2020](PowerSpectrumBaseCase[S], abc.ABC):
    """Tests that are run for BPL 2020 and DBPL 2021."""

    def test_f_peak(self) -> None:
        """$f_p$ should be finite and positive."""
        self.assert_positive(self.spectrum.f_peak())

    def test_f_star0_factor(self) -> None:
        r"""$f_p$ should be proportional to the correction factor of $f_{\ast,0}$."""
        factor = 1.5
        spectrum = self.SPECTRUM_CLASS(
            T_star=self.T_STAR, g_star=self.G_STAR,
            v_wall=self.V_WALL, alpha=self.ALPHA, beta_tilde=self.BETA_TILDE,
            f_star0_factor=factor
        )
        assert spectrum.f_peak() == pytest.approx(factor * self.spectrum.f_peak(), rel=1e-14)

    def test_power_spectrum_common(self) -> None:
        """The common prefactor of the power spectrum should be finite and positive."""
        self.assert_positive(self.spectrum.power_spectrum_common())

    def test_s(self) -> None:
        """$s$ at the frequencies of the noise curve should be finite and positive."""
        self.assert_positive(self.spectrum.s(f=noise_curve().f))
