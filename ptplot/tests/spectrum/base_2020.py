"""Tests for BPL 2020 and DBPL 2021."""

import abc

from ptplot.science.noise import noise_curve
from ptplot.science.spectrum.base2020 import PowerSpectrum2020
from ptplot.tests.spectrum.base import PowerSpectrumBaseCase


class PowerSpectrumBaseCase2020[S: PowerSpectrum2020](PowerSpectrumBaseCase[S], abc.ABC):
    """Tests that are run for BPL 2020 and DBPL 2021."""

    def test_f_peak(self) -> None:
        self.assert_positive(self.spectrum.f_peak())

    def test_power_spectrum_common(self) -> None:
        self.assert_positive(self.spectrum.power_spectrum_common())

    def test_s(self) -> None:
        self.assert_positive(self.spectrum.s(f=noise_curve().f))
