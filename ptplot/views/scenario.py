from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Scenario
from ptplot.science.SNRalphabeta_onthefly import get_SNR_alphabeta_image
from ptplot.science.SNRubarfrstar_onthefly import get_SNR_image


def model_scenario_plot(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["model__scenarios", "points"],
        model__id=model_id,
        number=scenario_id
    )
    return render(request, "model_scenario_plot.html", {"scenario": scenario})


def model_scenario_snr(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    scenario: Scenario = get_object_or_404_related(
        Scenario,
        related=["model"],
        prefetch=["points"],
        model__id=model_id,
        number=scenario_id
    )
    points = scenario.points.all()
    vws = [
        scenario.model.vw if point.vw is None else point.vw
        for point in points
    ]
    fig = get_SNR_image(
        vw_list=[vws],
        alpha_list=[[point.alpha for point in points]],
        beta_over_H_list=[[point.beta_over_H for point in points]],
        T_star=scenario.T_star_value,
        g_star=scenario.model.g_star,
        label_list=[[point.short_label for point in points]],
        title_list=[scenario.model.name],
        mission_profile=scenario.model.mission_profile,
        huge_alpha=scenario.model.huge_alpha
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

    fig = get_SNR_alphabeta_image(
        vw=scenario.model.vw,
        alpha_list=[[point.alpha for point in points]],
        beta_over_H_list=[[point.beta_over_H for point in points]],
        T_star=scenario.T_star_value,
        g_star=scenario.model.g_star,
        labels=[[point.short_label for point in points]],
        titles=[scenario.model.name],
        mission_profile=scenario.model.mission_profile,
        huge_alpha=scenario.model.huge_alpha
    )
    return fig_to_response(fig)
