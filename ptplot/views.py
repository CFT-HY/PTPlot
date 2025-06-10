import logging
import os

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
import dulwich.porcelain
from dulwich.repo import Repo

from ptplot.forms import MultipleForm, ParameterChoiceForm, PTPlotForm
from ptplot.methods import fig_to_response, get_object_or_404_related
from ptplot.models import Model, ParameterChoice, Scenario
from ptplot.science.SNRubarfrstar_onthefly import get_SNR_image
from ptplot.science.SNRalphabeta_onthefly import get_SNR_alphabeta_image
from ptplot.science.plot_powerspectrum import get_PS_image, get_PS_data
from ptplot.science.precomputed import *

logger = logging.getLogger(__name__)
GIT_DESCRIPTION: str = "unknown"
HAVE_GITVER: bool = False

try:
     THIS_FILE_DIR = os.path.realpath(os.path.dirname(__file__))
     GIT_DESCRIPTION = dulwich.porcelain.describe(Repo.discover(THIS_FILE_DIR))
     HAVE_GITVER = True
except dulwich.errors.NotGitRepository as err:
     logger.exception("Could not load git repository info.", exc_info=err)


# -----
# CSV view
# -----

def csv(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    csv = get_PS_data(
        T_star=form.cleaned_data["T_star"],
        g_star=form.cleaned_data["g_star"],
        vw=form.cleaned_data["vw"],
        alpha=form.cleaned_data["alpha"],
        beta_over_H=form.cleaned_data["beta_over_H"],
        mission_profile=int(form.cleaned_data["mission_profile"])
    )
    return HttpResponse(csv, content_type="text/csv")


# -----
# Image views
# -----

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
    fig = get_SNR_image(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw_list=[[point.vw_value]],
        alpha_list=[[point.alpha]],
        beta_over_H_list=[[point.beta_over_H]],
        label_list=[[point.short_label]],
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
    fig = get_SNR_alphabeta_image(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw=point.vw_value,
        alpha_list=[[point.alpha]],
        beta_over_H_list=[[point.beta_over_H]],
        labels=[[point.short_label]],
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
    csv = get_PS_data(
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
    fig = get_PS_image(
        T_star=point.T_star_value,
        g_star=point.g_star_value,
        vw=point.vw_value,
        alpha=point.alpha,
        beta_over_H=point.beta_over_H,
        mission_profile=point.model.mission_profile
    )
    return fig_to_response(fig)


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

    fig = get_SNR_image(
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

    fig = get_SNR_alphabeta_image(
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


def parameterchoice_form(request: HttpRequest) -> HttpResponse:
    model = get_object_or_404_related(Model, prefetch=["points"], id=1)
    form = ParameterChoiceForm()
    context = {
        "model": model.name,
        "form": form,
    }
    return render(request, "parameterchoice.html", context)


def multiple(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = MultipleForm(request.POST)

        if form.is_valid():
            # querystring = request.GET.urlencode()
            # usetex = form.cleaned_data["usetex"]

            vw = form.cleaned_data["vw"]
            T_star = form.cleaned_data["T_star"]
            g_star = form.cleaned_data["g_star"]
            mission_profile = int(form.cleaned_data["mission_profile"])
            table_lines = form.cleaned_data["table"].splitlines()

            alphas = []
            beta_over_Hs = []
            labels = []

            read_lines = 0

            for line in table_lines:
                line = line.strip()
                if len(line) == 0 or line[0] == "#":
                    continue

                read_lines += 1

                bits = line.split(",")
                alphas.append(float(bits[0]))
                beta_over_Hs.append(float(bits[1]))
                try:
                    labels.append(bits[2].strip())
                except IndexError:
                    pass

            if not len(labels) == read_lines:
                label_list_final = None
            else:
                label_list_final = [labels]

            fig = get_SNR_alphabeta_image(
                vw=vw,
                alpha_list=[alphas],
                beta_over_H_list=[beta_over_Hs],
                T_star=T_star,
                g_star=g_star,
                mission_profile=mission_profile,
                labels=label_list_final
            )
            return fig_to_response(fig)
    # Form not valid or not filled out
    return render(request, "multiple.html", {"form": MultipleForm()})


def single(request: HttpRequest) -> HttpResponse:
    querystring = request.GET.urlencode()

    # If this is a POST request we need to process the form data
    if request.method == "GET" and querystring:
        form = PTPlotForm(request.GET)

        if form.is_valid():
            # usetex = form.cleaned_data["usetex"]

            mission_profile = int(form.cleaned_data["mission_profile"])
            mission_profile_label = AVAILABLE_LABELS[mission_profile]

            context = {
                "form": form,
                "querystring": querystring,
                "vw": form.cleaned_data["vw"],
                "alpha": form.cleaned_data["alpha"],
                "beta_over_H": form.cleaned_data["beta_over_H"],
                "T_star": form.cleaned_data["T_star"],
                "g_star": form.cleaned_data["g_star"],
                "mission_profile_label": mission_profile_label
            }
            return render(request, "single_result.html", context)

        # Form not valid
        return render(request, "single.html", {"form": form})

    # No form yet
    return render(request, "single.html", {"form": PTPlotForm()})


def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "index.html",
        context={"git_description": GIT_DESCRIPTION} if HAVE_GITVER else None
    )
