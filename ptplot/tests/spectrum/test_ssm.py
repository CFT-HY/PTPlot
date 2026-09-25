"""Sound Shell Model (SSM) tests."""

import unittest

from ptplot.science.spectrum.ssm import PowerSpectrumSSM
from ptplot.tests.spectrum.base_spectrum import PowerSpectrumBaseCase


class SSMTest(PowerSpectrumBaseCase, unittest.TestCase):
    """Tests for the Sound Shell Model (SSM) power spectrum."""

    SPECTRUM_CLASS = PowerSpectrumSSM
