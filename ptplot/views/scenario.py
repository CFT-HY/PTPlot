"""Views for scenarios"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Scenario
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar


def model_scenario_plot(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    """Display a group of scenario points on the SNR plots"""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["model__scenarios", "points"],
        model__id=model_id,
        number=scenario_id
    )

    form = BenchmarkForm(request.GET, scenario=scenario)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return render(
        request,
        "model_scenario_plot.html",
        {"model": scenario.model, "scenario": scenario, "form": form}
    )


def model_scenario_snr_alpha_beta(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    r"""Display a group of scenario points on the $\alpha, \beta/H$ SNR plot"""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    form = BenchmarkForm(request.GET, scenario=scenario)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    data = scenario.point_data()
    fig = snr_figure_alpha_beta(
        v_wall_snr=scenario.model.vw,
        T_star_snr=scenario.T_star_value,
        g_star_snr=scenario.model.g_star,
        alphas=data["alpha_n"].values,
        beta_over_Hs=data["beta_over_H"].values,
        labels=data["label"].to_list(),
        titles=scenario.name,
        mission_profile=form.mission_profile,
        huge_alpha=scenario.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


def model_scenario_snr_ubarf_rstar(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    r"""Display a group of scenario points on the $\bar{U}_f, r_*$ SNR plot"""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    form = BenchmarkForm(request.GET, scenario=scenario)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    data = scenario.point_data()
    fig = snr_figure_ubarf_rstar(
        v_wall_snr=scenario.model.vw,
        T_star_snr=scenario.T_star_value,
        g_star_snr=scenario.model.g_star,
        v_walls=data["v_wall"].values,
        alphas=data["alpha_n"].values,
        beta_over_Hs=data["beta_over_H"].values,
        labels=data["label"].to_list(),
        titles=scenario.name,
        mission_profile=form.mission_profile,
        huge_alpha=scenario.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)
