"""Shared test case for the power spectrum classes."""

from abc import ABC

from ptplot.science.noise import noise_curve
from ptplot.science.plot.power_spectrum import power_spectrum_figure
from ptplot.science.spectrum import PowerSpectrum


class PowerSpectrumBaseCase(ABC):
    """Tests that are run for each power spectrum class."""

    SPECTRUM_CLASS: type[PowerSpectrum]
    V_WALL: float = 0.3
    ALPHA: float = 0.1
    BETA_OVER_H: float = 10000
    T_STAR: float = 100
    G_STAR: float = 100

    @classmethod
    def setUpClass(cls):
        cls.spectrum = cls.SPECTRUM_CLASS(
            T_star=cls.T_STAR, g_star=cls.G_STAR,
            v_wall=cls.V_WALL, alpha=cls.ALPHA, beta_over_H=cls.BETA_OVER_H
        )

    def test_csv(self):
        return self.spectrum.csv()

    def test_f_peak(self):
        return self.spectrum.f_peak()

    def test_F_gw0_h2(self):
        return self.spectrum.F_gw0_h2()

    def test_h_star(self):
        return self.spectrum.h_star()

    def test_J(self):
        return self.spectrum.J()

    def test_kinetic_energy(self):
        return self.spectrum.kinetic_energy_fraction_approx

    def test_power_spectrum(self):
        return self.spectrum.power_spectrum(f=noise_curve().f)

    def test_power_spectrum_common(self):
        return self.spectrum.power_spectrum_common()

    def test_ps_image(self):
        return power_spectrum_figure(self.spectrum, sw_only=False)

    def test_s(self):
        return self.spectrum.s(f=noise_curve().f)

    def test_source_lifetime_factor(self):
        return self.spectrum.source_lifetime_factor()

    def test_shock_time(self):
        return self.spectrum.shock_time
