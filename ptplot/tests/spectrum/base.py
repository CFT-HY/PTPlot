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


class PowerSpectrumBaseCase[S: PowerSpectrum](ABC):
    """Tests that are run for each power spectrum class."""

    SPECTRUM_CLASS: type[S]
    V_WALL: float = 0.3
    ALPHA: float = 0.1
    BETA_TILDE: float = 10000
    T_STAR: float = 100
    G_STAR: float = 100

    spectrum: S

    @classmethod
    def setUpClass(cls) -> None:
        """Create the power spectrum to be tested."""
        super().setUpClass()  # pyrefly: ignore[missing-attribute]
        cls.spectrum = cls.SPECTRUM_CLASS(
            T_star=cls.T_STAR, g_star=cls.G_STAR,
            v_wall=cls.V_WALL, alpha=cls.ALPHA, beta_tilde=cls.BETA_TILDE
        )

    @staticmethod
    def assert_positive(value: tp.Any) -> None:
        """Assert that all values are finite and positive."""
        arr = np.asarray(value)
        assert np.all(np.isfinite(arr)), f"Got non-finite values: {value}"
        assert np.all(arr > 0), f"Got non-positive values: {value}"

    def test_csv(self) -> None:
        """The power spectrum should be exportable as CSV."""
        assert self.spectrum.csv()

    def test_F_gw0_h2(self) -> None:
        r"""$F_{\text{gw},0} h^2$ should be finite and positive."""
        self.assert_positive(self.spectrum.F_gw0_h2())

    def test_h_star(self) -> None:
        """$h_*$ should be finite and positive."""
        self.assert_positive(self.spectrum.h_star())

    def test_H_star_eta_sh(self) -> None:
        r"""$\mathcal{H}_* \eta_\text{sh}$ should be finite and positive."""
        self.assert_positive(self.spectrum.H_star_eta_sh)

    def test_H_star_eta_v(self) -> None:
        r"""$\mathcal{H}_* \eta_\text{v}$ should be finite and positive."""
        self.assert_positive(self.spectrum.H_star_eta_v)

    def test_J(self) -> None:
        """$J$ should be finite and positive."""
        self.assert_positive(self.spectrum.J())

    def test_kinetic_energy(self) -> None:
        """The kinetic energy fraction $K$ should be finite and positive."""
        self.assert_positive(self.spectrum.kinetic_energy_fraction)

    def test_power_spectrum(self) -> None:
        """The power spectrum should be positive at the frequencies of the noise curve, and the SNR non-negative."""
        f = noise_curve().f
        power_spectrum, snr = self.spectrum.power_spectrum(f=f)
        assert power_spectrum.shape == f.shape
        self.assert_positive(power_spectrum)
        assert snr >= 0

    def test_ps_image(self) -> None:
        """The power spectrum figure should be created."""
        assert power_spectrum_figure(self.spectrum, sw_only=False) is not None

    def test_source_lifetime_factor(self) -> None:
        r"""The source lifetime factor $\Upsilon_\ell$ should be finite and positive."""
        self.assert_positive(self.spectrum.source_lifetime_factor())
