"""Broken power law (BPL) tests"""

from ptplot.science.spectrum.bpl import PowerSpectrumBPL
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class BPLTest(PowerSpectrumBaseCase):
    SPECTRUM_CLASS = PowerSpectrumBPL
