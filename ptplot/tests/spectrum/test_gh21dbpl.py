"""Double broken power law (DBPL) tests (2021 version)."""

import unittest

from ptplot.science.spectrum.gh21dbpl import GH21dbpl
from ptplot.tests.spectrum.coswg20 import PowerSpectrumBaseCase2020


class DBPL2021Test(PowerSpectrumBaseCase2020[GH21dbpl], unittest.TestCase):
    """Tests for the double broken power law (DBPL) power spectrum of 2021."""

    SPECTRUM_CLASS = GH21dbpl
