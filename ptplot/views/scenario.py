"""Views for scenarios"""

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Scenario
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar


def model_scenario_plot(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
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


def model_scenario_snr(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    points = scenario.points.all()

    form = BenchmarkForm(request.GET, scenario=scenario)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    vws = [
        scenario.model.vw if point.vw is None else point.vw
        for point in points
    ]
    fig = snr_figure_ubarf_rstar(
        vws=vws,
        alphas=[point.alpha for point in points],
        beta_over_Hs=[point.beta_over_H for point in points],
        T_star=scenario.T_star_value,
        g_star=scenario.model.g_star,
        labels=[point.short_label for point in points],
        titles=scenario.name,
        mission_profile=form.mission_profile,
        huge_alpha=scenario.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)


def model_scenario_snr_alphabeta(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    points = scenario.points.all()

    form = BenchmarkForm(request.GET, scenario=scenario)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    fig = snr_figure_alpha_beta(
        v_wall=scenario.model.vw,
        alphas=[point.alpha for point in points],
        beta_over_Hs=[point.beta_over_H for point in points],
        T_star=scenario.T_star_value,
        g_star=scenario.model.g_star,
        labels=[point.short_label for point in points],
        titles=scenario.name,
        mission_profile=form.mission_profile,
        huge_alpha=scenario.model.huge_alpha,
        engine=form.cleaned_data["engine"]
    )
    return fig_to_response(fig)
