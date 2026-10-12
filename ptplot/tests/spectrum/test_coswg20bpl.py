"""Broken power law (BPL) tests (2020 version)."""

import unittest

from ptplot.science.spectrum.coswg20bpl import CosWG20bpl
from ptplot.tests.spectrum.coswg20 import PowerSpectrumBaseCase2020


class BPL2020Test(PowerSpectrumBaseCase2020[CosWG20bpl], unittest.TestCase):
    """Tests for the broken power law (BPL) power spectrum of 2020."""

    SPECTRUM_CLASS = CosWG20bpl
