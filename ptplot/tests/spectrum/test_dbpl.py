"""Double broken power law (DBPL) tests."""

from ptplot.science.spectrum.dbpl import PowerSpectrumDBPL
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class DBPLTest(PowerSpectrumBaseCase):
    """Tests for the double broken power law (DBPL) power spectrum."""

    SPECTRUM_CLASS = PowerSpectrumDBPL
