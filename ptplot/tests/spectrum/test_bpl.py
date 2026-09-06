"""Broken power law (BPL) tests."""

from ptplot.science.spectrum.bpl import PowerSpectrumBPL
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class BPLTest(PowerSpectrumBaseCase):
    """Tests for the broken power law (BPL) power spectrum."""

    SPECTRUM_CLASS = PowerSpectrumBPL
