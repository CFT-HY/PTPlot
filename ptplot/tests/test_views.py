import typing as tp

from django.forms import Form
from django.http import HttpResponse
from django.test import TestCase

from ptplot.forms import PTPlotForm
from ptplot.management.commands.populate import Command as PopulateCommand
from ptplot.science.engine import Engine

ALLOW_CODES: tp.Iterable[int] = (200, 302)


def check_status_code(response: HttpResponse, allow_codes: tp.Iterable[int] = None) -> int:
    allow_codes2 = ALLOW_CODES if allow_codes is None else (*ALLOW_CODES, *allow_codes)
    if response.status_code not in allow_codes2:
        raise AssertionError("Invalid status code", response.status_code)
    return response.status_code


def test_view(
        test: TestCase,
        url: str,
        form: Form = None,
        data: dict[str, tp.Any] = None,
        allow_codes: tp.Iterable[int] = None) -> int:
    if form is None:
        data2 = {} if data is None else data.copy()
    else:
        data2 = form.cleaned_data.copy() if data is None else {**form.cleaned_data, **data}
    # Remove None values from data2, as they cannot be encoded in the query string.
    delete = [key for key in data2 if data2[key] is None]
    for key in delete:
        del data2[key]
    return check_status_code(test.client.get(url, data=data2), allow_codes=allow_codes)


class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        command = PopulateCommand()
        command.handle()
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
        test_view(self, "/ptplot/curvedata.csv", form=self.form)

    def test_snr_alphabeta(self):
        test_view(self, "/ptplot/snr_alphabeta.svg", form=self.form)

    def test_snr(self):
        test_view(self, "/ptplot/snr.svg", form=self.form)

    def test_ps(self):
        test_view(self, "/ptplot/ps.svg", form=self.form)

    def test_single(self):
        test_view(self, "/ptplot/single", form=self.form)

    # def test_multiple(self):
    #     test_view(self, "/ptplot/snr_alphabeta.svg", form=self.form)

    def test_models(self):
        test_view(self, "/ptplot/models")

    def test_model(self):
        test_view(self, "/ptplot/models/1")

    def test_model_plot(self):
        test_view(self, "/ptplot/models/1/plot")

    def test_point(self):
        test_view(self, "/ptplot/models/1/1/plot")

    def test_point_snr(self):
        test_view(self, "/ptplot/models/1/1/snr.svg")

    def test_point_snr_alphabeta(self):
        test_view(self, "/ptplot/models/1/1/snr_alphabeta.svg")

    def test_model_ps(self):
        test_view(self, "/ptplot/models/1/1/ps.svg")

    def test_model_csv(self):
        test_view(self, "/ptplot/models/1/1/curvedata.csv")

    def test_scenario(self):
        test_view(self, "/ptplot/models/1/scenarios/1/plot")

    def test_scenario_snr(self):
        test_view(self, "/ptplot/models/1/scenarios/1/snr.svg")

    def test_scenario_snr_alpha_beta(self):
        test_view(self, "/ptplot/models/1/scenarios/1/snr_alphabeta.svg")

    def test_model_snr(self):
        test_view(self, "/ptplot/models/1/snr.svg")

    def test_model_snr_alpha_beta(self):
        test_view(self, "/ptplot/models/1/snr_alphabeta.svg")

    # def test_parameterchoice(self):
    #     test_view(self, "/ptplot/parameterchoice")

    def test_index(self):
        test_view(self, "/ptplot", allow_codes=(301, ))
