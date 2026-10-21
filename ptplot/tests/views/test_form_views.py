"""Tests for the views of the forms."""

import typing as tp

from django.urls import reverse

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.tests.check import check_status_code, check_view
from ptplot.tests.const import FAST_DATA, GRID_AXES_DATA, SSM_SETTINGS_DATA
from ptplot.tests.views.base import ViewTestCase

#: Query data for the SSM with the sound speeds of the constant sound speed model
SOUND_SPEEDS: dict[str, tp.Any] = {"engine": Engine.SSM, "alpha": 0.2, "css2": "1/4", "csb2": 0.3}


class FormViewTest(ViewTestCase):
    """Tests for the views of the forms."""

    def test_form(self) -> None:
        """The form of the test parameters should be valid."""
        assert self.form.is_valid()

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

    def test_csv_sound_speeds(self) -> None:
        """The sound speeds should change the SSM spectrum."""
        url = reverse("csv")
        data = self.form_data(engine=Engine.SSM, alpha=0.2, **SSM_SETTINGS_DATA)
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

    def test_parameter_choice(self) -> None:
        """The parameter choice view should return a valid status code."""
        check_view(self, "parameter_choice")

    def test_csv_legacy_nucleation_cs_max(self) -> None:
        r"""The legacy option should change the spectrum only when $v_{\text{wall}} < c_s$."""
        url = reverse("csv")
        for v_wall, should_differ in ((0.3, True), (0.9, False)):
            data = self.form_data(v_wall=v_wall)
            legacy = self.csv_content(url, {**data, "legacy_nucleation_cs_max": True})
            default = self.csv_content(url, {**data, "legacy_nucleation_cs_max": False})
            assert (legacy != default) == should_differ, f"v_wall={v_wall}"

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

    def test_sound_speeds(self) -> None:
        """The plots of the single point page should accept the sound speeds of the SSM."""
        for view in ("csv", "ps", "snr_alpha_beta", "snr_ubarf_rstar"):
            check_view(self, view, form=self.form, data={**SOUND_SPEEDS, **FAST_DATA})

    def test_snr_grid_axes(self) -> None:
        """The SNR views should accept the size and the limits of the axes."""
        data = {
            **GRID_AXES_DATA,
            "alpha_min": 0.05, "alpha_max": 0.5, "beta_tilde_min": 10, "beta_tilde_max": 1000,
            "ubarf_min": 0.05, "ubarf_max": 0.5, "r_star_min": 1e-3, "r_star_max": 0.1
        }
        for view in ("snr_alpha_beta", "snr_ubarf_rstar"):
            check_view(self, view, form=self.form, data=data)
        check_view(self, "model_snr_alpha_beta", view_kwargs=self.MODEL_KWARGS, data=data)

    def test_snr_grid_axes_invalid(self) -> None:
        """Invalid sizes and limits of the axes should be rejected."""
        for data in (
                {"grid_size": const.DEFAULT_GRID_SIZE + 1},
                {"grid_size": 1},
                {"beta_tilde_min": 1000, "beta_tilde_max": 10}):
            for view in ("snr_alpha_beta", "snr_ubarf_rstar"):
                response = self.client.get(reverse(view), data=self.form_data(**data))
                assert response.status_code == 400, (view, data)  # noqa: PLR2004
            response = self.client.get(
                reverse("model_snr_alpha_beta", kwargs=self.MODEL_KWARGS), data=data)
            assert response.status_code == 400, data  # noqa: PLR2004
