"""Double broken power law (DBPL) tests"""

from ptplot.science.spectrum.dbpl import PowerSpectrumDBPL
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class DBPLTest(PowerSpectrumBaseCase):
    SPECTRUM_CLASS = PowerSpectrumDBPL
