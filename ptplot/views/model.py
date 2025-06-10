from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Model
from ptplot.science.snr_alphabeta_onthefly import get_snr_alphabeta_image
from ptplot.science.snr_ubarfrstar_onthefly import get_snr_image


def models(request: HttpRequest) -> HttpResponse:
    return render(request, "models.html", {"models": Model.objects.all()})


def model_detail(request: HttpRequest, model_id: int) -> HttpResponse:
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["points", "scenarios"],
        id=model_id
    )
    return render(request, "model_detail.html", {"model": model})


def model_detail_plot(request: HttpRequest, model_id: int) -> HttpResponse:
    model: Model = get_object_or_404_related(
        Model,
        prefetch=["points", "scenarios"],
        id=model_id
    )
    return render(request, "model_detail_plot.html", {"model": model})


def model_snr(request: HttpRequest, model_id: int) -> HttpResponse:
    model: Model = get_object_or_404(Model, pk=model_id)

    if model.has_scenarios:
        scenarios = model.scenarios.prefetch_related("points").all()
        vws = []
        alphas = []
        beta_over_Hs = []
        labels = []
        titles = []

        for scenario in scenarios:
            points = scenario.points.all()
            vws.append([model.vw if point.vw is None else point.vw for point in points])
            alphas.append([point.alpha for point in points])
            beta_over_Hs.append([point.beta_over_H for point in points])
            labels.append([point.short_label for point in points])
            titles.append(scenario.name)
    else:
        points = model.points.all()
        vws=[[model.vw] * len(points)]
        alphas = [[point.alpha for point in points]]
        beta_over_Hs = [[point.beta_over_H for point in points]]
        labels = [[point.short_label for point in points]]
        titles = [model.name]

    fig = get_snr_image(
        vw_list=vws,
        alpha_list=alphas,
        beta_over_H_list=beta_over_Hs,
        T_star=model.T_star,
        g_star=model.g_star,
        label_list=labels,
        title_list=titles,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha
    )
    return fig_to_response(fig)


def model_snr_alphabeta(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)

    if model.has_scenarios:
        scenarios = model.scenarios.prefetch_related("points").all()
        alphas = []
        beta_over_Hs = []
        labels = []
        titles = []

        for scenario in scenarios:
            points = scenario.points.all()
            alphas.append([point.alpha for point in points])
            beta_over_Hs.append([point.beta_over_H for point in points])
            labels.append([point.short_label for point in points])
            titles.append(scenario.name)

    else:
        points = model.points.all()
        alphas = [[point.alpha for point in points]]
        beta_over_Hs = [[point.beta_over_H for point in points]]
        labels = [[point.short_label for point in points]]
        titles = [model.name]

    fig = get_snr_alphabeta_image(
        vw=model.vw,
        alpha_list=alphas,
        beta_over_H_list=beta_over_Hs,
        T_star=model.T_star,
        g_star=model.g_star,
        labels=labels,
        titles=titles,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha
    )
    return fig_to_response(fig)
