"""Tests for the form of the accuracy settings of the SSM."""

from django.test import TestCase
from pttools.ssm.const import DEFAULT_N_T, DEFAULT_N_Z_LOOKUP
from pttools.ssm.settings import SSMSettings

from ptplot.forms import SSMSettingsForm
from ptplot.science.const import MIN_N_Z_LOOKUP


class SSMSettingsFormTest(TestCase):
    """Tests for the accuracy settings of the PTtools spectra of the SSM."""

    @staticmethod
    def test_defaults() -> None:
        """Without data the default settings should be used."""
        form = SSMSettingsForm({})
        assert form.is_valid(), form.errors
        assert form.settings == SSMSettings()

    @staticmethod
    def test_settings() -> None:
        """The given settings should be used, and the defaults for the others."""
        form = SSMSettingsForm({"n_z_lookup": "1000", "nx_P_tilde_gw": "200"})
        assert form.is_valid(), form.errors
        assert form.settings == SSMSettings(n_z_lookup=1000, nT=DEFAULT_N_T, nx_P_tilde_gw=200)

    @staticmethod
    def test_invalid() -> None:
        """Settings above the defaults or below the minimums should be rejected."""
        for data in (
                {"n_z_lookup": DEFAULT_N_Z_LOOKUP + 1},
                {"n_z_lookup": MIN_N_Z_LOOKUP - 1},
                {"nT": DEFAULT_N_T + 1},
                {"nx_P_tilde_gw": 0}):
            form = SSMSettingsForm(data)
            assert not form.is_valid(), data
