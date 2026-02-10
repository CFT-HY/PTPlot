"""Tests for views"""

import typing as tp

from django.forms import Form
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from ptplot.forms import PTPlotForm
from ptplot.management.commands.populate import Command as PopulateCommand
from ptplot.science.engine import Engine

ALLOW_CODES: tp.Iterable[int] = (200, 302)


def check_status_code(response: HttpResponse, allow_codes: tp.Iterable[int] | None = None) -> int:
    allow_codes2 = ALLOW_CODES if allow_codes is None else (*ALLOW_CODES, *allow_codes)
    if response.status_code not in allow_codes2:
        raise AssertionError("Invalid status code", response.status_code)
    return response.status_code


def test_view(
        test: TestCase,
        url: str,
        url_args: tp.Iterable[tp.Any] | None = None,
        url_kwargs: tp.Iterable[tp.Any] | None = None,
        form: Form | None = None,
        data: dict[str, tp.Any] | None = None,
        allow_codes: tp.Iterable[int] | None = None) -> int:
    absolute_url = reverse(url, args=url_args, kwargs=url_kwargs)
    if form is None:
        data2 = {} if data is None else data.copy()
    else:
        data2 = form.cleaned_data.copy() if data is None else {**form.cleaned_data, **data}
    # Remove None values from data2, as they cannot be encoded in the query string.
    delete = [key for key in data2 if data2[key] is None]
    for key in delete:
        del data2[key]
    return check_status_code(test.client.get(absolute_url, data=data2), allow_codes=allow_codes)


class ViewTest(TestCase):
    MODEL_KWARGS = {"model_id": 1}
    POINT_KWARGS = {"model_id": 1, "point_id": 1}
    SCENARIO_KWARGS = {"model_id": 1, "scenario_id": 1}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PopulateCommand().handle()
        cls.form = PTPlotForm(data={
            "vw": 0.3,
            "alpha": 0.1,
            "beta_over_H": 10000,
            "T_star": 100,
            "g_star": 100,
            "mission_profile_ind": 0,
            "engine": Engine.DEFAULT
        })
        cls.form.is_valid()

    def test_form(self):
        self.assertTrue(self.form.is_valid())

    def test_csv(self):
        test_view(self, "csv", form=self.form)

    def test_index(self):
        test_view(self, "index")

    def test_snr_alphabeta(self):
        test_view(self, "snr_alphabeta", form=self.form)

    def test_snr(self):
        test_view(self, "snr", form=self.form)

    def test_ps(self):
        test_view(self, "ps", form=self.form)

    def test_single(self):
        test_view(self, "single", form=self.form)

    # def test_multiple(self):
    #     test_view(self, "/ptplot/snr_alphabeta.svg", form=self.form)

    def test_models(self):
        test_view(self, "models")

    def test_model(self):
        test_view(self, "model_detail", url_kwargs=self.MODEL_KWARGS)

    def test_model_plot(self):
        test_view(self, "model_detail_plot", url_kwargs=self.MODEL_KWARGS)

    def test_model_snr(self):
        test_view(self, "model_snr", url_kwargs=self.MODEL_KWARGS)

    def test_model_snr_alphabeta(self):
        test_view(self, "model_snr_alphabeta", url_kwargs=self.MODEL_KWARGS)

    def test_parameterchoice(self):
        test_view(self, "parameterchoice")

    def test_point(self):
        test_view(self, "model_point_plot", url_kwargs=self.POINT_KWARGS)

    def test_point_snr(self):
        test_view(self, "model_point_snr", url_kwargs=self.POINT_KWARGS)

    def test_point_snr_alphabeta(self):
        test_view(self, "model_point_snr_alphabeta", url_kwargs=self.POINT_KWARGS)

    def test_point_ps(self):
        test_view(self, "model_point_ps", url_kwargs=self.POINT_KWARGS)

    def test_point_csv(self):
        test_view(self, "model_point_csv", url_kwargs=self.POINT_KWARGS)

    def test_scenario(self):
        test_view(self, "model_scenario_plot", url_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr(self):
        test_view(self, "model_scenario_snr", url_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr_alpha_beta(self):
        test_view(self, "model_scenario_snr_alphabeta", url_kwargs=self.SCENARIO_KWARGS)
