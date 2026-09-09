"""Tests for the power spectra."""

from django.test import TestCase

from ptplot.science import const
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.spectrum.engine import Engine


class PowerSpectrumTest(TestCase):
    """Tests for the power spectra."""

    @staticmethod
    def test_power_spectrum():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_over_H=const.DEFAULT_BETA_OVER_H
        )

    @staticmethod
    def test_power_spectrum_dbpl():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_over_H=const.DEFAULT_BETA_OVER_H,
            engine=Engine.DBPL
        )

    @staticmethod
    def test_power_spectrum_ssm():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_over_H=const.DEFAULT_BETA_OVER_H,
            engine=Engine.SSM
        )

    @staticmethod
    def test_power_spectrum_ssm_const_cs():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_over_H=const.DEFAULT_BETA_OVER_H,
            engine=Engine.SSM, css2=1 / 4, csb2=1 / 4
        )
