"""Sound Shell Model (SSM) tests"""

from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase
from ptplot.science.spectrum.ssm import PowerSpectrumSSM


class SSMTest(PowerSpectrumBaseCase):
    SPECTRUM_CLASS = PowerSpectrumSSM
