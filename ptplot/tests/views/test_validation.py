"""Tests for the validation of the query parameters of the views."""

from django.http import HttpResponseBadRequest
from django.test import RequestFactory, TestCase

from ptplot.forms import BenchmarkForm
from ptplot.science import const
from ptplot.science.snr.grid import GridAxes
from ptplot.science.spectrum.ssm import SSMSettings
from ptplot.tests.const import FAST_DATA, TEST_GRID_SIZE, TEST_SSM_SETTINGS
from ptplot.views.validation import ValidatedForms, validate_forms


class ValidateFormsTest(TestCase):
    """Tests for :py:func:`ptplot.views.validation.validate_forms`."""

    def setUp(self) -> None:
        """Create the request factory."""
        self.factory: RequestFactory = RequestFactory()

    def test_defaults(self) -> None:
        """Without the optional settings, the defaults should be used."""
        validated = validate_forms(self.factory.get("/"), BenchmarkForm)
        assert isinstance(validated, ValidatedForms)
        assert isinstance(validated.form, BenchmarkForm)
        assert validated.axes == GridAxes()
        assert validated.ssm_settings == SSMSettings()

    def test_settings(self) -> None:
        """The optional settings should be read from the query parameters."""
        validated = validate_forms(self.factory.get("/", data=FAST_DATA), BenchmarkForm)
        assert isinstance(validated, ValidatedForms)
        assert validated.axes == GridAxes(size=TEST_GRID_SIZE)
        assert validated.ssm_settings == TEST_SSM_SETTINGS

    def test_invalid(self) -> None:
        """Invalid data in any of the forms should give a plain text response with the errors."""
        for data in (
                {"obs_years": "<b>x</b>"},
                {"grid_size": const.DEFAULT_GRID_SIZE + 1},
                {"n_z_lookup": 1}):
            response = validate_forms(self.factory.get("/", data=data), BenchmarkForm)
            assert isinstance(response, HttpResponseBadRequest), data
            assert response["Content-Type"].startswith("text/plain"), data
            assert next(iter(data)) in response.content.decode(), data
