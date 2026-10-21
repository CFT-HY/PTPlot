"""Tests for the form of the benchmark plots."""

from django.http import QueryDict
from django.test import TestCase

from ptplot.forms import BenchmarkForm
from ptplot.science import const
from ptplot.science.noise import noise_curve


class BenchmarkFormTest(TestCase):
    """Tests for the noise fields of the benchmark form."""

    @staticmethod
    def test_defaults() -> None:
        """Without data the form should fall back to the default noise curve."""
        form = BenchmarkForm()
        assert form.is_valid()
        assert form.noise is noise_curve()

    @staticmethod
    def test_query_dict() -> None:
        """The form should also accept a QueryDict, which stores its values as lists."""
        obs_years = 7
        form = BenchmarkForm(QueryDict(f"obs_years={obs_years}&noise_gb=True"))
        assert form.is_valid(), form.errors
        noise = form.noise
        assert noise.obs_years == obs_years
        # An unchecked checkbox is missing from the query string.
        assert not noise.eb
        assert noise.gb
        assert not form.cleaned_data["legacy_nucleation_cs_max"]

    @staticmethod
    def test_legacy_nucleation_cs_max_default() -> None:
        """The legacy option should have its default value when the form has no data."""
        form = BenchmarkForm()
        assert form.is_valid()
        assert form.cleaned_data["legacy_nucleation_cs_max"] == const.DEFAULT_LEGACY_NUCLEATION_CS_MAX

    @staticmethod
    def test_legacy_nucleation_cs_max_query_dict() -> None:
        """The legacy option should be readable from a QueryDict."""
        form = BenchmarkForm(QueryDict("obs_years=3&legacy_nucleation_cs_max=True"))
        assert form.is_valid(), form.errors
        assert form.cleaned_data["legacy_nucleation_cs_max"]
