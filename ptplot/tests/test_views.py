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


def check_status_code(
        response: HttpResponse,
        allow_codes: tp.Iterable[int] | None = None,
        url: str | None = None) -> int:
    allow_codes2 = ALLOW_CODES if allow_codes is None else (*ALLOW_CODES, *allow_codes)
    if response.status_code not in allow_codes2:
        raise AssertionError(
            f"Invalid status code {response.status_code}, expected one of {allow_codes2}" +
            ("." if url is None else f' for url "{url}".')
        )
    return response.status_code


def test_url(
        test: TestCase,
        url: str,
        form: Form | None = None,
        data: dict[str, tp.Any] | None = None,
        allow_codes: tp.Iterable[int] | None = None) -> int:
    data2 = {
        key: value for key, value in (
            ({} if data is None else data) if form is None
            else form.cleaned_data if data is None
            else {**form.cleaned_data, **data}
        ).items()
        # Remove None values, as they cannot be encoded in the query string
        if value is not None
    }
    return check_status_code(test.client.get(url, data=data2), allow_codes=allow_codes, url=url)


def test_view(
        test: TestCase,
        view: str,
        view_args: tp.Iterable[tp.Any] | None = None,
        view_kwargs: tp.Iterable[tp.Any] | None = None,
        form: Form | None = None,
        data: dict[str, tp.Any] | None = None,
        allow_codes: tp.Iterable[int] | None = None) -> int:
    return test_url(
        test=test,
        url=reverse(view, args=view_args, kwargs=view_kwargs),
        form=form, data=data, allow_codes=allow_codes
    )


class ViewTest(TestCase):
    MODEL_ID = 1
    POINT_ID = 1
    SCENARIO_ID = 1
    MODEL_KWARGS = {"model_id": MODEL_ID}
    POINT_KWARGS = {"model_id": MODEL_ID, "point_id": POINT_ID}
    SCENARIO_KWARGS = {"model_id": MODEL_ID, "scenario_id": SCENARIO_ID}

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

    # -----
    # Views
    # -----

    def test_csv(self):
        test_view(self, "csv", form=self.form)

    def test_index(self):
        test_view(self, "index")

    def test_snr_alpha_beta(self):
        test_view(self, "snr_alpha_beta", form=self.form)

    def test_snr_ubarf_rstar(self):
        test_view(self, "snr_ubarf_rstar", form=self.form)

    def test_ps(self):
        test_view(self, "ps", form=self.form)

    def test_single(self):
        test_view(self, "single", form=self.form)

    # def test_multiple(self):
    #     test_view(self, "/ptplot/snr_alphabeta.svg", form=self.form)

    def test_models(self):
        test_view(self, "models")

    def test_model(self):
        test_view(self, "model_detail", view_kwargs=self.MODEL_KWARGS)

    def test_model_plot(self):
        test_view(self, "model_detail_plot", view_kwargs=self.MODEL_KWARGS)

    def test_model_snr_alphabeta(self):
        test_view(self, "model_snr_alpha_beta", view_kwargs=self.MODEL_KWARGS)

    def test_model_snr_ubarf_rstar(self):
        test_view(self, "model_snr_ubarf_rstar", view_kwargs=self.MODEL_KWARGS)

    def test_parameter_choice(self):
        test_view(self, "parameter_choice")

    def test_point(self):
        test_view(self, "model_point_plot", view_kwargs=self.POINT_KWARGS)

    def test_point_snr_alpha_beta(self):
        test_view(self, "model_point_snr_alpha_beta", view_kwargs=self.POINT_KWARGS)

    def test_point_snr(self):
        test_view(self, "model_point_snr_ubarf_rstar", view_kwargs=self.POINT_KWARGS)

    def test_point_ps(self):
        test_view(self, "model_point_ps", view_kwargs=self.POINT_KWARGS)

    def test_point_csv(self):
        test_view(self, "model_point_csv", view_kwargs=self.POINT_KWARGS)

    def test_scenario(self):
        test_view(self, "model_scenario_plot", view_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr_alpha_beta(self):
        test_view(self, "model_scenario_snr_alpha_beta", view_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr_ubarf_rstar(self):
        test_view(self, "model_scenario_snr_ubarf_rstar", view_kwargs=self.SCENARIO_KWARGS)

    # -----
    # Old urls
    # -----

    def test_old_snr_alpha_beta(self):
        test_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr_alphabeta.svg", allow_codes=(301, ))

    def test_old_snr_alpha_beta2(self):
        test_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr_alphabeta", allow_codes=(301, ))

    def test_old_snr_ubarf_rstar(self):
        test_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr.svg", allow_codes=(301, ))

    def test_old_snr_ubarf_rstar2(self):
        test_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr", allow_codes=(301, ))
