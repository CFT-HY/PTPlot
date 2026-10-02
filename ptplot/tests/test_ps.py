"""Tests for the power spectra."""

from django.test import TestCase

from ptplot.science import const
from ptplot.science.spectrum.create import power_spectrum
from ptplot.science.spectrum.engine import Engine


class PowerSpectrumTest(TestCase):
    """Tests for the power spectra."""

    @staticmethod
    def test_power_spectrum() -> None:
        """The power spectrum should be created with the default engine."""
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE
        )

    @staticmethod
    def test_power_spectrum_bpl2024() -> None:
        """The power spectrum should be created with the BPL 2024 engine."""
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.BPL2024
        )

    @staticmethod
    def test_power_spectrum_dbpl2021() -> None:
        """The power spectrum should be created with the DBPL 2021 engine."""
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.DBPL2021
        )

    @staticmethod
    def test_power_spectrum_dbpl2024() -> None:
        """The power spectrum should be created with the DBPL 2024 engine."""
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.DBPL2024
        )

    @staticmethod
    def test_power_spectrum_ssm() -> None:
        """The power spectrum should be created with the SSM engine."""
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.SSM
        )

    @staticmethod
    def test_power_spectrum_ssm_const_cs() -> None:
        """The SSM power spectrum should be created with the constant sound speed model."""
        power_spectrum(
            v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
            engine=Engine.SSM, css2=1 / 4, csb2=1 / 4
        )
