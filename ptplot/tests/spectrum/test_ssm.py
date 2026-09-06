"""Sound Shell Model (SSM) tests"""

from ptplot.science.spectrum.ssm import PowerSpectrumSSM
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class SSMTest(PowerSpectrumBaseCase):
    SPECTRUM_CLASS = PowerSpectrumSSM
