"""Tests for views."""

import typing as tp

from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse

from ptplot.forms import BenchmarkForm, PTPlotForm
from ptplot.management.commands.populate import Command as PopulateCommand
from ptplot.models import ParameterChoice
from ptplot.science import const
from ptplot.science.noise import noise_curve
from ptplot.science.spectrum.engine import Engine
from ptplot.tests.check import check_status_code, check_url, check_view


class ViewTest(TestCase):
    """Tests for Django views."""

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

    def test_form(self) -> None:
        """The form of the test parameters should be valid."""
        assert self.form.is_valid()

    # -----
    # Views
    # -----

    def test_csv(self) -> None:
        """The CSV view should return a valid status code."""
        check_view(self, "csv", form=self.form)

    def test_index(self) -> None:
        """The index view should return a valid status code."""
        check_view(self, "index")

    def test_snr_alpha_beta(self) -> None:
        r"""The SNR view in the $(\alpha_n, \beta/H)$ plane should return a valid status code."""
        check_view(self, "snr_alpha_beta", form=self.form)

    def test_snr_ubarf_rstar(self) -> None:
        r"""The SNR view in the $(\bar{U}_f, r_*)$ plane should return a valid status code."""
        check_view(self, "snr_ubarf_rstar", form=self.form)

    def test_ps(self) -> None:
        """The power spectrum view should return a valid status code."""
        check_view(self, "ps", form=self.form)

    def test_single(self) -> None:
        """The single point view should return a valid status code."""
        check_view(self, "single", form=self.form)

    def test_single_bubble_v(self) -> None:
        """The single point page should show the fluid velocity and enthalpy profiles only for the SSM."""
        for engine, shown in ((Engine.SSM, True), (Engine.DEFAULT, False)):
            response = self.client.get(reverse("single"), data=self.form_data(engine=engine))
            check_status_code(response)
            for view in ("bubble_v", "bubble_w"):
                assert (reverse(view).encode() in response.content) == shown, (engine, view)

    def test_bubble_v(self) -> None:
        """The fluid velocity profile view should return a valid status code, also with the sound speeds."""
        check_view(self, "bubble_v", form=self.form)
        check_view(self, "bubble_v", form=self.form, data={"alpha": 0.2, "css2": 0.25, "csb2": 0.3})

    def test_sound_speeds(self) -> None:
        """The plots of the single point page should accept the sound speeds of the SSM."""
        data = {"engine": Engine.SSM, "alpha": 0.2, "css2": "1/4", "csb2": 0.3}
        for view in ("csv", "ps", "snr_alpha_beta", "snr_ubarf_rstar"):
            check_view(self, view, form=self.form, data=data)

    def test_csv_sound_speeds(self) -> None:
        """The sound speeds should change the SSM spectrum."""
        url = reverse("csv")
        data = self.form_data(engine=Engine.SSM, alpha=0.2)
        assert self.csv_content(url, data) != self.csv_content(url, {**data, "css2": 0.25, "csb2": 0.3})

    def test_single_invalid_sound_speeds(self) -> None:
        """Invalid sound speeds for the SSM should be reported on the single point page."""
        response = self.client.get(
            reverse("single"), data=self.form_data(engine=Engine.SSM, css2=0.3, csb2=0.25))
        check_status_code(response)
        assert b"Invalid sound speeds" in response.content

    def test_bubble_w(self) -> None:
        """The enthalpy profile view should return a valid status code, also with the sound speeds."""
        check_view(self, "bubble_w", form=self.form)
        check_view(self, "bubble_w", form=self.form, data={"alpha": 0.2, "css2": 0.25, "csb2": 0.3})

    def test_multiple(self) -> None:
        """The multiple points form is submitted with POST."""
        url = reverse("multiple")
        response = self.client.post(url, data={
            "v_wall": 0.3,
            "T_star": 100,
            "g_star": 100,
            "table": "0.1,10000,A\n0.2,1000,B",
            "engine": Engine.DEFAULT,
            "obs_years": 3,
            "noise_eb": True,
            "noise_gb": True
        })
        check_status_code(response, url=url)
        # An invalid form results in the form page instead of the figure,
        # and therefore the status code alone is not enough.
        assert response.headers["Content-Type"] == "image/svg+xml", \
            f"The form was not accepted: {response.content[:500]!r}"

    def test_models(self) -> None:
        """The model list view should return a valid status code."""
        check_view(self, "models")

    def test_model(self) -> None:
        """The model detail view should return a valid status code."""
        check_view(self, "model_detail", view_kwargs=self.MODEL_KWARGS)

    def test_model_plot(self) -> None:
        """The model plot view should return a valid status code."""
        check_view(self, "model_detail_plot", view_kwargs=self.MODEL_KWARGS)

    def test_model_snr_alphabeta(self) -> None:
        r"""The model SNR view in the $(\alpha_n, \beta/H)$ plane should return a valid status code."""
        check_view(self, "model_snr_alpha_beta", view_kwargs=self.MODEL_KWARGS)

    def test_model_snr_comparison(self) -> None:
        """The model SNR comparison view should return a valid status code."""
        check_view(self, "model_snr_comparison", view_kwargs=self.MODEL_KWARGS)

    def test_model_snr_histogram(self) -> None:
        """The model SNR histogram view should return a valid status code."""
        check_view(self, "model_snr_histogram", view_kwargs=self.MODEL_KWARGS)

    def test_model_snr_ubarf_rstar(self) -> None:
        r"""The model SNR view in the $(\bar{U}_f, r_*)$ plane should return a valid status code."""
        check_view(self, "model_snr_ubarf_rstar", view_kwargs=self.MODEL_KWARGS)

    def test_parameter_choice(self) -> None:
        """The parameter choice view should return a valid status code."""
        check_view(self, "parameter_choice")

    def test_point(self) -> None:
        """The point plot view should return a valid status code."""
        check_view(self, "model_point_plot", view_kwargs=self.POINT_KWARGS)

    def test_point_snr_alpha_beta(self) -> None:
        r"""The point SNR view in the $(\alpha_n, \beta/H)$ plane should return a valid status code."""
        check_view(self, "model_point_snr_alpha_beta", view_kwargs=self.POINT_KWARGS)

    def test_point_snr_comparison(self) -> None:
        """The point SNR comparison view should return a valid status code."""
        check_view(self, "model_point_snr_comparison", view_kwargs=self.POINT_KWARGS)

    def test_point_snr(self) -> None:
        r"""The point SNR view in the $(\bar{U}_f, r_*)$ plane should return a valid status code."""
        check_view(self, "model_point_snr_ubarf_rstar", view_kwargs=self.POINT_KWARGS)

    def test_point_ps(self) -> None:
        """The point power spectrum view should return a valid status code."""
        check_view(self, "model_point_ps", view_kwargs=self.POINT_KWARGS)

    def test_point_bubble_v(self) -> None:
        """The point fluid velocity profile view should return a valid status code."""
        check_view(self, "model_point_bubble_v", view_kwargs=self.POINT_KWARGS)

    def test_point_bubble_w(self) -> None:
        """The point enthalpy profile view should return a valid status code."""
        check_view(self, "model_point_bubble_w", view_kwargs=self.POINT_KWARGS)

    def test_point_csv(self) -> None:
        """The point CSV view should return a valid status code."""
        check_view(self, "model_point_csv", view_kwargs=self.POINT_KWARGS)

    def test_point_legacy_nucleation_cs_max(self) -> None:
        r"""The legacy $\max(v_{\text{wall}}, c_s)$ option should be selectable in the query string."""
        for view in ("model_point_snr_alpha_beta", "model_point_snr_ubarf_rstar", "model_point_ps"):
            check_view(self, view, view_kwargs=self.POINT_KWARGS, data={"legacy_nucleation_cs_max": True})

    def test_model_legacy_nucleation_cs_max(self) -> None:
        r"""The legacy $\max(v_{\text{wall}}, c_s)$ option should be selectable in the model views."""
        for view in ("model_snr_alpha_beta", "model_snr_ubarf_rstar", "model_snr_histogram"):
            check_view(self, view, view_kwargs=self.MODEL_KWARGS, data={"legacy_nucleation_cs_max": True})

    def test_scenario_legacy_nucleation_cs_max(self) -> None:
        r"""The legacy $\max(v_{\text{wall}}, c_s)$ option should be selectable in the scenario views."""
        for view in ("model_scenario_snr_alpha_beta", "model_scenario_snr_comparison"):
            check_view(self, view, view_kwargs=self.SCENARIO_KWARGS, data={"legacy_nucleation_cs_max": True})

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

    def test_csv_legacy_nucleation_cs_max(self) -> None:
        r"""The legacy option should change the spectrum only when $v_{\text{wall}} < c_s$."""
        url = reverse("csv")
        for v_wall, should_differ in ((0.3, True), (0.9, False)):
            data = self.form_data(v_wall=v_wall)
            legacy = self.csv_content(url, {**data, "legacy_nucleation_cs_max": True})
            default = self.csv_content(url, {**data, "legacy_nucleation_cs_max": False})
            assert (legacy != default) == should_differ, f"v_wall={v_wall}"

    def test_point_csv_legacy_nucleation_cs_max(self) -> None:
        """The legacy option should reach the spectra of the benchmark points."""
        point = ParameterChoice.objects.filter(v_wall__lt=const.CS0).select_related("model").first()
        assert point is not None, "The test data should have a point with v_wall < c_s."
        url = reverse("model_point_csv", kwargs={"model_id": point.model.id, "point_id": point.number})
        legacy = self.csv_content(url, {"legacy_nucleation_cs_max": True})
        default = self.csv_content(url, {})
        assert legacy != default

    def test_multiple_legacy_nucleation_cs_max(self) -> None:
        """The multiple points form should accept the legacy option."""
        url = reverse("multiple")
        response = self.client.post(url, data={
            "v_wall": 0.3,
            "T_star": 100,
            "g_star": 100,
            "table": "0.1,10000,A\n0.2,1000,B",
            "engine": Engine.DEFAULT,
            "obs_years": 3,
            "noise_eb": True,
            "noise_gb": True,
            "legacy_nucleation_cs_max": True
        })
        check_status_code(response, url=url)
        assert response.headers["Content-Type"] == "image/svg+xml", \
            f"The form was not accepted: {response.content[:500]!r}"

    def test_single_legacy_nucleation_cs_max(self) -> None:
        """The single point page should show that the legacy conversion is used."""
        response = self.client.get(reverse("single"), data=self.form_data(legacy_nucleation_cs_max=True))
        check_status_code(response)
        assert b"legacy, with" in response.content

    def test_point_ps_noise(self) -> None:
        """The noise settings should be selectable in the query string."""
        check_view(
            self, "model_point_ps", view_kwargs=self.POINT_KWARGS,
            data={"obs_years": 7, "noise_eb": False, "noise_gb": True}
        )

    def test_scenario(self) -> None:
        """The scenario plot view should return a valid status code."""
        check_view(self, "model_scenario_plot", view_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr_alpha_beta(self) -> None:
        r"""The scenario SNR view in the $(\alpha_n, \beta/H)$ plane should return a valid status code."""
        check_view(self, "model_scenario_snr_alpha_beta", view_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr_comparison(self) -> None:
        """The scenario SNR comparison view should return a valid status code."""
        check_view(self, "model_scenario_snr_comparison", view_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr_histogram(self) -> None:
        """The scenario SNR histogram view should return a valid status code."""
        check_view(self, "model_scenario_snr_histogram", view_kwargs=self.SCENARIO_KWARGS)

    def test_scenario_snr_ubarf_rstar(self) -> None:
        r"""The scenario SNR view in the $(\bar{U}_f, r_*)$ plane should return a valid status code."""
        check_view(self, "model_scenario_snr_ubarf_rstar", view_kwargs=self.SCENARIO_KWARGS)

    # -----
    # Old urls
    # -----

    def test_old_snr_alpha_beta(self) -> None:
        r"""The old URL of the point SNR figure in the $(\alpha_n, \beta/H)$ plane should redirect to the new one."""
        check_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr_alphabeta.svg", allow_codes=(301,))

    def test_old_snr_alpha_beta2(self) -> None:
        r"""The old URL of the point SNR view in the $(\alpha_n, \beta/H)$ plane should redirect to the new one."""
        check_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr_alphabeta", allow_codes=(301,))

    def test_old_snr_ubarf_rstar(self) -> None:
        r"""The old URL of the point SNR figure in the $(\bar{U}_f, r_*)$ plane should redirect to the new one."""
        check_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr.svg", allow_codes=(301,))

    def test_old_snr_ubarf_rstar2(self) -> None:
        r"""The old URL of the point SNR view in the $(\bar{U}_f, r_*)$ plane should redirect to the new one."""
        check_url(self, f"/ptplot/models/{self.MODEL_ID}/{self.POINT_ID}/snr", allow_codes=(301,))


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
