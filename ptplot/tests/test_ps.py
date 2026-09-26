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
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE
        )

    @staticmethod
    def test_power_spectrum_bpl2024():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.BPL2024
        )

    @staticmethod
    def test_power_spectrum_dbpl2021():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.DBPL2021
        )

    @staticmethod
    def test_power_spectrum_dbpl2024():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.DBPL2024
        )

    @staticmethod
    def test_power_spectrum_ssm():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.SSM
        )

    @staticmethod
    def test_power_spectrum_ssm_const_cs():
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.SSM, css2=1 / 4, csb2=1 / 4
        )
