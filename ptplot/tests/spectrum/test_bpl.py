"""Broken power law (BPL) tests"""

from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase
from ptplot.science.spectrum.bpl import PowerSpectrumBPL


class BPLTest(PowerSpectrumBaseCase):
    SPECTRUM_CLASS = PowerSpectrumBPL
