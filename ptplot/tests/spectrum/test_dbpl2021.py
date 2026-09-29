"""Double broken power law (DBPL) tests (2021 version)."""

import unittest

from ptplot.science.spectrum.dbpl2021 import PowerSpectrumDBPL2021
from ptplot.tests.spectrum.base_2020 import PowerSpectrumBaseCase2020


class DBPL2021Test(PowerSpectrumBaseCase2020[PowerSpectrumDBPL2021], unittest.TestCase):
    """Tests for the double broken power law (DBPL) power spectrum of 2021."""

    SPECTRUM_CLASS = PowerSpectrumDBPL2021
