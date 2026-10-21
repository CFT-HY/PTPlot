"""Tests for the views of the models, their benchmark points and scenarios."""


from django.urls import reverse

from ptplot.models import ParameterChoice
from ptplot.science import const
from ptplot.tests.check import check_url, check_view
from ptplot.tests.const import FAST_DATA
from ptplot.tests.views.base import ViewTestCase


class ModelViewTest(ViewTestCase):
    """Tests for the views of the models, their benchmark points and scenarios."""

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
        check_view(self, "model_snr_alpha_beta", view_kwargs=self.MODEL_KWARGS, data=FAST_DATA)

    def test_model_snr_comparison(self) -> None:
        """The model SNR comparison view should return a valid status code."""
        check_view(self, "model_snr_comparison", view_kwargs=self.MODEL_KWARGS, data=FAST_DATA)

    def test_model_snr_histogram(self) -> None:
        """The model SNR histogram view should return a valid status code."""
        check_view(self, "model_snr_histogram", view_kwargs=self.MODEL_KWARGS, data=FAST_DATA)

    def test_model_snr_ubarf_rstar(self) -> None:
        r"""The model SNR view in the $(\bar{U}_f, r_*)$ plane should return a valid status code."""
        check_view(self, "model_snr_ubarf_rstar", view_kwargs=self.MODEL_KWARGS, data=FAST_DATA)

    def test_point(self) -> None:
        """The point plot view should return a valid status code."""
        check_view(self, "model_point_plot", view_kwargs=self.POINT_KWARGS)

    def test_point_snr_alpha_beta(self) -> None:
        r"""The point SNR view in the $(\alpha_n, \beta/H)$ plane should return a valid status code."""
        check_view(self, "model_point_snr_alpha_beta", view_kwargs=self.POINT_KWARGS, data=FAST_DATA)

    def test_point_snr_comparison(self) -> None:
        """The point SNR comparison view should return a valid status code."""
        check_view(self, "model_point_snr_comparison", view_kwargs=self.POINT_KWARGS, data=FAST_DATA)

    def test_point_snr(self) -> None:
        r"""The point SNR view in the $(\bar{U}_f, r_*)$ plane should return a valid status code."""
        check_view(self, "model_point_snr_ubarf_rstar", view_kwargs=self.POINT_KWARGS, data=FAST_DATA)

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
            check_view(
                self, view, view_kwargs=self.POINT_KWARGS,
                data={**FAST_DATA, "legacy_nucleation_cs_max": True}
            )

    def test_model_legacy_nucleation_cs_max(self) -> None:
        r"""The legacy $\max(v_{\text{wall}}, c_s)$ option should be selectable in the model views."""
        for view in ("model_snr_alpha_beta", "model_snr_ubarf_rstar", "model_snr_histogram"):
            check_view(
                self, view, view_kwargs=self.MODEL_KWARGS,
                data={**FAST_DATA, "legacy_nucleation_cs_max": True}
            )

    def test_scenario_legacy_nucleation_cs_max(self) -> None:
        r"""The legacy $\max(v_{\text{wall}}, c_s)$ option should be selectable in the scenario views."""
        for view in ("model_scenario_snr_alpha_beta", "model_scenario_snr_comparison"):
            check_view(
                self, view, view_kwargs=self.SCENARIO_KWARGS,
                data={**FAST_DATA, "legacy_nucleation_cs_max": True}
            )

    def test_point_csv_legacy_nucleation_cs_max(self) -> None:
        """The legacy option should reach the spectra of the benchmark points."""
        point = ParameterChoice.objects.filter(v_wall__lt=const.CS0).select_related("model").first()
        assert point is not None, "The test data should have a point with v_wall < c_s."
        url = reverse("model_point_csv", kwargs={"model_id": point.model.id, "point_id": point.number})
        legacy = self.csv_content(url, {"legacy_nucleation_cs_max": True})
        default = self.csv_content(url, {})
        assert legacy != default

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
        check_view(self, "model_scenario_snr_alpha_beta", view_kwargs=self.SCENARIO_KWARGS, data=FAST_DATA)

    def test_scenario_snr_comparison(self) -> None:
        """The scenario SNR comparison view should return a valid status code."""
        check_view(self, "model_scenario_snr_comparison", view_kwargs=self.SCENARIO_KWARGS, data=FAST_DATA)

    def test_scenario_snr_histogram(self) -> None:
        """The scenario SNR histogram view should return a valid status code."""
        check_view(self, "model_scenario_snr_histogram", view_kwargs=self.SCENARIO_KWARGS, data=FAST_DATA)

    def test_scenario_snr_ubarf_rstar(self) -> None:
        r"""The scenario SNR view in the $(\bar{U}_f, r_*)$ plane should return a valid status code."""
        check_view(self, "model_scenario_snr_ubarf_rstar", view_kwargs=self.SCENARIO_KWARGS, data=FAST_DATA)

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
