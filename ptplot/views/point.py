from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import ParameterChoice
from ptplot.science.plot_powerspectrum import get_ps_data, get_ps_image
from ptplot.science.snr_alphabeta_onthefly import get_snr_alphabeta_image
from ptplot.science.snr_ubarfrstar_onthefly import get_snr_image


def model_point_plot(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        prefetch=["model__points", "model__scenarios"],
        model__id=model_id,
        number=point_id
    )
    return render(request, "model_point_plot.html", {"point": point})


def model_point_snr(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    fig = get_snr_image(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vws=point.vw_value,
        alphas=point.alpha,
        beta_over_Hs=point.beta_over_H,
        labels=point.short_label,
        mission_profile=point.model.mission_profile,
        huge_alpha=point.model.huge_alpha
    )
    return fig_to_response(fig)


def model_point_snr_alphabeta(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    fig = get_snr_alphabeta_image(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw=point.vw_value,
        alphas=point.alpha,
        beta_over_Hs=point.beta_over_H,
        labels=point.short_label,
        mission_profile=point.model.mission_profile,
        huge_alpha=point.model.huge_alpha
    )
    return fig_to_response(fig)


def model_point_csv(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    csv = get_ps_data(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw=point.vw_value,
        alpha=point.alpha,
        beta_over_H=point.beta_over_H,
        mission_profile=point.model.mission_profile
    )
    return HttpResponse(csv, content_type="text/csv")


def model_point_ps(request, model_id, point_id) -> HttpResponse:
    point: ParameterChoice = get_object_or_404_related(
        ParameterChoice,
        related=["model"],
        model__id=model_id,
        number=point_id
    )
    fig = get_ps_image(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw=point.vw_value,
        alpha=point.alpha,
        beta_over_H=point.beta_over_H,
        mission_profile=point.model.mission_profile
    )
    return fig_to_response(fig)
