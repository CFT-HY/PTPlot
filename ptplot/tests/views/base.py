"""Base class for the tests of views."""

import typing as tp

from django.test import TestCase

from ptplot.forms import PTPlotForm
from ptplot.management.commands.populate import Command as PopulateCommand
from ptplot.science.spectrum.engine import Engine
from ptplot.tests.check import check_status_code


class ViewTestCase(TestCase):
    """Base class for the tests of Django views.

    The tests are divided into several subclasses so that pytest-xdist can run them in parallel,
    as each class is run on a single worker.
    """

    MODEL_ID: tp.ClassVar[int] = 1
    POINT_ID: tp.ClassVar[int] = 1
    SCENARIO_ID: tp.ClassVar[int] = 1
    MODEL_KWARGS: tp.ClassVar[dict[str, int]] = {"model_id": MODEL_ID}
    POINT_KWARGS: tp.ClassVar[dict[str, int]] = {"model_id": MODEL_ID, "point_id": POINT_ID}
    SCENARIO_KWARGS: tp.ClassVar[dict[str, int]] = {"model_id": MODEL_ID, "scenario_id": SCENARIO_ID}
    form: PTPlotForm

    @classmethod
    def setUpClass(cls) -> None:
        """Populate the database and create the form of the test parameters."""
        super().setUpClass()
        PopulateCommand().handle()
        cls.form = PTPlotForm(data={
            "v_wall": 0.3,
            "alpha": 0.1,
            "beta_tilde": 10000,
            "T_star": 100,
            "g_star": 100,
            "obs_years": 3,
            "noise_eb": True,
            "noise_gb": True,
            "engine": Engine.DEFAULT
        })
        cls.form.is_valid()

    def form_data(self, **kwargs: tp.Any) -> dict[str, tp.Any]:
        """Get the data of the test form without None values, which cannot be encoded in a query string."""
        return {key: value for key, value in {**self.form.cleaned_data, **kwargs}.items() if value is not None}

    def csv_content(self, url: str, data: dict[str, tp.Any]) -> bytes:
        """Get the content of a CSV view.

        :param url: URL of the view
        :param data: Query parameters
        :return: Content of the response
        """
        response = self.client.get(url, data=data)
        check_status_code(response, url=url)
        return response.content
