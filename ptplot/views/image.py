from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest

from ptplot.forms import PTPlotForm
from ptplot.methods import fig_to_response
from ptplot.science.plot_powerspectrum import get_PS_image
from ptplot.science.snr_alphabeta_onthefly import get_SNR_alphabeta_image
from ptplot.science.snr_ubarfrstar_onthefly import get_SNR_image


def ps_image(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    fig = get_PS_image(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        vw=form.cleaned_data["vw"],
        alpha=form.cleaned_data["alpha"],
        beta_over_H=form.cleaned_data["beta_over_H"],
        mission_profile=int(form.cleaned_data["mission_profile"])
    )
    return fig_to_response(fig)


def snr_image(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    fig = get_SNR_image(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        vw_list=[[form.cleaned_data["vw"]]],
        alpha_list=[[form.cleaned_data["alpha"]]],
        beta_over_H_list=[[form.cleaned_data["beta_over_H"]]],
        mission_profile=int(form.cleaned_data["mission_profile"])
    )
    return fig_to_response(fig)


def snr_alphabeta_image(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    fig = get_SNR_alphabeta_image(
        vw=form.cleaned_data["vw"],
        alpha_list=[[form.cleaned_data["alpha"]]],
        beta_over_H_list=[[form.cleaned_data["beta_over_H"]]],
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        mission_profile=int(form.cleaned_data["mission_profile"])
    )
    return fig_to_response(fig)
