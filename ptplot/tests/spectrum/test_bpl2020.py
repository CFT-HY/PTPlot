"""Broken power law (BPL) tests (2020 version)."""

import unittest

from ptplot.science.spectrum.bpl2020 import PowerSpectrumBPL2020
from ptplot.tests.spectrum.base_2020 import PowerSpectrumBaseCase2020


class BPL2020Test(PowerSpectrumBaseCase2020[PowerSpectrumBPL2020], unittest.TestCase):
    """Tests for the broken power law (BPL) power spectrum of 2020."""

    SPECTRUM_CLASS = PowerSpectrumBPL2020
