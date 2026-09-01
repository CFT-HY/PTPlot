"""Views for scenarios"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Scenario
from ptplot.science.spectrum import Engine


def model_scenario_plot(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    """Display a group of scenario points on the SNR plots"""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["model__points", "model__scenarios", "points"],
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

    return fig_to_response(
        scenario.snr_figure_alpha_beta(
            grid=scenario.snr_grid_alpha_beta(
                engine=form.cleaned_data["engine"], mission_profile=form.mission_profile
            )
        )
    )


def model_scenario_snr_comparison(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    """Compare the SNR of different engines for a scenario"""
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

    engine = form.cleaned_data["engine"]
    return fig_to_response(
        scenario.snr_comparison(
            grid1=scenario.snr_grid_alpha_beta(engine=Engine.BPL, mission_profile=form.mission_profile),
            grid2=scenario.snr_grid_alpha_beta(
                engine=Engine.DBPL if engine == Engine.BPL else engine,
                mission_profile=form.mission_profile
            )
        )
    )


def model_scenario_snr_histogram(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    """Display a histogram of the SNR values of the model points"""
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

    return fig_to_response(scenario.snr_histogram(mission_profile=form.mission_profile))


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

    return fig_to_response(
        scenario.snr_figure_ubarf_rstar(
            grid=scenario.snr_grid_ubarf_rstar(
                engine=form.cleaned_data["engine"], mission_profile=form.mission_profile
            )
        )
    )
