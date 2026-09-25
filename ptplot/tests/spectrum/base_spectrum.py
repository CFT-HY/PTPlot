"""Shared test case for the power spectrum classes.

The test classes of the individual power spectra should inherit from both
:class:`PowerSpectrumBaseCase` and :class:`unittest.TestCase`.
The base case does not inherit from :class:`unittest.TestCase` itself,
as then its tests would also be run for the abstract base case.
"""

from abc import ABC
import typing as tp

import numpy as np

from ptplot.science.noise import noise_curve
from ptplot.science.plot.ps import power_spectrum_figure
from ptplot.science.spectrum import PowerSpectrum


class PowerSpectrumBaseCase(ABC):
    """Tests that are run for each power spectrum class."""

    SPECTRUM_CLASS: type[PowerSpectrum]
    V_WALL: float = 0.3
    ALPHA: float = 0.1
    BETA_TILDE: float = 10000
    T_STAR: float = 100
    G_STAR: float = 100

    spectrum: PowerSpectrum

    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # pyrefly: ignore[missing-attribute]
        cls.spectrum = cls.SPECTRUM_CLASS(
            T_star=cls.T_STAR, g_star=cls.G_STAR,
            v_wall=cls.V_WALL, alpha=cls.ALPHA, beta_tilde=cls.BETA_TILDE
        )

    def assert_positive(self, value: tp.Any) -> None:
        """Assert that all values are finite and positive."""
        arr = np.asarray(value)
        assert np.all(np.isfinite(arr)), f"Got non-finite values: {value}"
        assert np.all(arr > 0), f"Got non-positive values: {value}"

    def test_csv(self):
        assert self.spectrum.csv()

    def test_f_peak(self):
        self.assert_positive(self.spectrum.f_peak())

    def test_F_gw0_h2(self):
        self.assert_positive(self.spectrum.F_gw0_h2())

    def test_h_star(self):
        self.assert_positive(self.spectrum.h_star())

    def test_H_star_eta_sh(self):
        self.assert_positive(self.spectrum.H_star_eta_sh)

    def test_H_star_eta_v(self):
        self.assert_positive(self.spectrum.H_star_eta_v)

    def test_J(self):
        self.assert_positive(self.spectrum.J)

    def test_J_old(self):
        self.assert_positive(self.spectrum.J_old)

    def test_kinetic_energy(self):
        self.assert_positive(self.spectrum.kinetic_energy_fraction_approx)

    def test_power_spectrum(self):
        f = noise_curve().f
        power_spectrum, snr = self.spectrum.power_spectrum(f=f)
        assert power_spectrum.shape == f.shape
        self.assert_positive(power_spectrum)
        assert snr >= 0

    def test_power_spectrum_common(self):
        self.assert_positive(self.spectrum.power_spectrum_common())

    def test_ps_image(self):
        assert power_spectrum_figure(self.spectrum, sw_only=False) is not None

    def test_s(self):
        self.assert_positive(self.spectrum.s(f=noise_curve().f))

    def test_source_lifetime_factor(self):
        self.assert_positive(self.spectrum.source_lifetime_factor())
