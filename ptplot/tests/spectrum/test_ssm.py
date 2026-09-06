"""Sound Shell Model (SSM) tests."""

from ptplot.science.spectrum.ssm import PowerSpectrumSSM
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class SSMTest(PowerSpectrumBaseCase):
    """Tests for the Sound Shell Model (SSM) power spectrum."""

    SPECTRUM_CLASS = PowerSpectrumSSM
