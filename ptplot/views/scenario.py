"""Views for scenarios."""

from django.db.models import Prefetch
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from ptplot.forms import BenchmarkForm
from ptplot.methods import fig_to_response, get_object_or_404_related, related_stats
from ptplot.models import Model, Scenario
from ptplot.science.spectrum import Engine
from ptplot.views.model import model_stats_context


def model_scenario_plot(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    """Display a group of scenario points on the SNR plots."""
    # The model is fetched with its scenarios instead of fetching the scenario with its model,
    # so that the statistics of the model, which are shown on the same page, can be annotated.
    model: Model = get_object_or_404_related(
        Model,
        annotate=Model.stats_annotations(),
        prefetch=[
            "points",
            Prefetch("scenarios", queryset=Scenario.objects.annotate(**Scenario.stats_annotations())),
            "scenarios__points"
        ],
        id=model_id
    )
    scenario = next((scenario for scenario in model.scenarios.all() if scenario.number == scenario_id), None)
    if scenario is None:
        raise Http404("No Scenario matches the given query.")

    form = BenchmarkForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return render(
        request,
        "model_scenario_plot.html",
        {
            "model": model,
            "scenario": scenario,
            "form": form,
            "scenario_point_stats": related_stats(scenario, "points"),
            **model_stats_context(model)
        }
    )


def model_scenario_snr_alpha_beta(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    r"""Display a group of scenario points on the $\alpha, \beta/H$ SNR plot."""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    form = BenchmarkForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        scenario.snr_figure_alpha_beta(
            grid=scenario.snr_grid_alpha_beta(
                engine=form.cleaned_data["engine"], noise=form.noise,
                legacy_nucleation_cs_max=form.cleaned_data["legacy_nucleation_cs_max"]
            )
        )
    )


def model_scenario_snr_comparison(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    """Compare the SNR of different engines for a scenario."""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    form = BenchmarkForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    engine = form.cleaned_data["engine"]
    return fig_to_response(
        scenario.snr_comparison(
            grid1=scenario.snr_grid_alpha_beta(
                engine=Engine.BPL2020, noise=form.noise,
                legacy_nucleation_cs_max=form.cleaned_data["legacy_nucleation_cs_max"]
            ),
            grid2=scenario.snr_grid_alpha_beta(
                engine=Engine.DBPL2021 if engine == Engine.BPL2020 else engine,
                noise=form.noise,
                legacy_nucleation_cs_max=form.cleaned_data["legacy_nucleation_cs_max"]
            )
        )
    )


def model_scenario_snr_histogram(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    """Display a histogram of the SNR values of the model points."""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    form = BenchmarkForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(scenario.snr_histogram(
        noise=form.noise,
        legacy_nucleation_cs_max=form.cleaned_data["legacy_nucleation_cs_max"]
    ))


def model_scenario_snr_ubarf_rstar(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    r"""Display a group of scenario points on the $\bar{U}_f, r_*$ SNR plot."""
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    form = BenchmarkForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(f"Invalid form data: {request.GET}")

    return fig_to_response(
        scenario.snr_figure_ubarf_rstar(
            grid=scenario.snr_grid_ubarf_rstar(
                engine=form.cleaned_data["engine"], noise=form.noise,
                legacy_nucleation_cs_max=form.cleaned_data["legacy_nucleation_cs_max"]
            )
        )
    )
