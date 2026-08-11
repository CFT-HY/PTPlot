"""Double broken power law (DBPL) tests"""

from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase
from ptplot.science.spectrum.dbpl import PowerSpectrumDBPL


class DBPLTest(PowerSpectrumBaseCase):
    SPECTRUM_CLASS = PowerSpectrumDBPL
