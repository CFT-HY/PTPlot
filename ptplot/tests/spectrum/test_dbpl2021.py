"""Double broken power law (DBPL) tests (2021 version)."""

import unittest

from ptplot.science.spectrum.dbpl2021 import PowerSpectrumDBPL2021
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class DBPL2021Test(PowerSpectrumBaseCase, unittest.TestCase):
    """Tests for the double broken power law (DBPL) power spectrum of 2021."""

    SPECTRUM_CLASS = PowerSpectrumDBPL2021
