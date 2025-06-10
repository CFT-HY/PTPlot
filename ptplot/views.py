import logging
import os

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
import dulwich.porcelain
from dulwich.repo import Repo
from matplotlib.figure import Figure

from ptplot.forms import *
from ptplot.science.SNRubarfrstar_onthefly import get_SNR_image
from ptplot.science.SNRalphabeta_onthefly import get_SNR_alphabeta_image
from ptplot.science.plot_powerspectrum import get_PS_image, get_PS_data
from ptplot.science.plot_utils import fig_to_svg
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
# Utility functions
# -----

def fig_to_response(fig: Figure) -> HttpResponse:
    return HttpResponse(fig_to_svg(fig), content_type="image/svg+xml")


# -----
# CSV view
# -----

def csv(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    vw = form.cleaned_data["vw"]
    alpha = form.cleaned_data["alpha"]
    beta_over_H = form.cleaned_data["beta_over_H"]
    mission_profile = int(form.cleaned_data["mission_profile"])
    T_star = form.cleaned_data["T_star"]
    g_star = form.cleaned_data["g_star"]

    csv = get_PS_data(
        T_star=T_star,
        g_star=g_star,
        vw=vw,
        alpha=alpha,
        beta_over_H=beta_over_H,
        mission_profile=mission_profile
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

    vw = form.cleaned_data["vw"]
    alpha = form.cleaned_data["alpha"]
    beta_over_H = form.cleaned_data["beta_over_H"]
    mission_profile = int(form.cleaned_data["mission_profile"])
    Tstar = form.cleaned_data["T_star"]
    gstar = form.cleaned_data["g_star"]

    fig = get_PS_image(
        T_star=Tstar,
        g_star=gstar,
        vw=vw,
        alpha=alpha,
        beta_over_H=beta_over_H,
        mission_profile=mission_profile
    )
    return fig_to_response(fig)


def snr_image(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    vw = form.cleaned_data["vw"]
    alpha = form.cleaned_data["alpha"]
    beta_over_H = form.cleaned_data["beta_over_H"]

    mission_profile = int(form.cleaned_data["mission_profile"])
    # SNRfilename = precomputed_filenames[MissionProfile]

    T_star = form.cleaned_data["T_star"]
    g_star = form.cleaned_data["g_star"]
    fig = get_SNR_image(
        T_star=T_star,
        g_star=g_star,
        vw_list=[[vw]],
        alpha_list=[[alpha]],
        beta_over_H_list=[[beta_over_H]],
        mission_profile=mission_profile
    )
    return fig_to_response(fig)


def snr_alphabeta_image(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = PTPlotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest()

    vw = form.cleaned_data["vw"]
    alpha = form.cleaned_data["alpha"]
    beta_over_H = form.cleaned_data["beta_over_H"]

    mission_profile = int(form.cleaned_data["mission_profile"])
    # SNRfilename = precomputed_filenames[MissionProfile]

    T_star = form.cleaned_data["T_star"]
    g_star = form.cleaned_data["g_star"]

    fig = get_SNR_alphabeta_image(
        vw=vw,
        alpha_list=[[alpha]],
        beta_over_H_list=[[beta_over_H]],
        T_star=T_star,
        g_star=g_star,
        mission_profile=mission_profile
    )
    return fig_to_response(fig)


def model(request: HttpRequest) -> HttpResponse:
    models_list = Model.objects.all()
    return render(request, "models.html", {"models_list": models_list})


def model_detail(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id)
    scenario_list = Scenario.objects.filter(model__id=model_id) if model.has_scenarios else None

   # for i in range(len(point_list)):
   #     point_list[i].update_snrchoice()

    context = {
        "model": model,
        "point_list": point_list,
        "scenario_list": scenario_list,
        "mission_profile_label": AVAILABLE_LABELS[model.mission_profile]
    }
    return render(request, "model_detail.html", context)


def model_detail_plot(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id)
    scenario_list = Scenario.objects.filter(model__id=model_id) if model.has_scenarios else None

   # for i in range(len(point_list)):
   #     point_list[i].update_snrchoice()

    context = {
        "model": model,
        "point_list": point_list,
        "scenario_list": scenario_list,
        "mission_profile_label": AVAILABLE_LABELS[model.mission_profile]
    }
    return render(request, "model_detail_plot.html", context)


def model_point_plot(request: HttpRequest, model_id: int, point_id: int):
    model = get_object_or_404(Model, pk=model_id)
    point = get_object_or_404(ParameterChoice, model__id=model_id, id=point_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id)
    scenario_list = Scenario.objects.filter(model__id=model_id) if model.has_scenarios else None

    context = {
        "model": model,
        "point": point,
        "point_list": point_list,
        "scenario_list": scenario_list,
        "mission_profile_label": AVAILABLE_LABELS[model.mission_profile]
    }
    return render(request, "model_point_plot.html", context)


def model_point_snr(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    point = get_object_or_404(ParameterChoice, model__id=model_id, number=point_id)

    mission_profile = model.mission_profile
    alpha = point.alpha
    beta_over_H = point.beta_over_H
    vw = point.vw if point.vw else model.vw
    T_star = point.T_star if point.T_star else model.T_star
    g_star = point.g_star if point.g_star else model.g_star

    label = point.short_label
    huge_alpha = model.huge_alpha
    
    fig = get_SNR_image(
        T_star=T_star,
        g_star=g_star,
        vw_list=[[vw]],
        alpha_list=[[alpha]],
        beta_over_H_list=[[beta_over_H]],
        label_list=[[label]],
        mission_profile=mission_profile,
        huge_alpha=huge_alpha
    )
    return fig_to_response(fig)


def model_point_snr_alphabeta(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    point = get_object_or_404(ParameterChoice, model__id=model_id, number=point_id)

    mission_profile = model.mission_profile
    alpha = point.alpha
    beta_over_H = point.beta_over_H
    vw = point.vw if point.vw else model.vw
    T_star = point.T_star if point.T_star else model.T_star
    g_star = point.g_star if point.g_star else model.g_star

    label = point.short_label
    huge_alpha = model.huge_alpha
        
    fig = get_SNR_alphabeta_image(
        T_star=T_star,
        g_star=g_star,
        vw=vw,
        alpha_list=[[alpha]],
        beta_over_H_list=[[beta_over_H]],
        labels=[[label]],
        mission_profile=mission_profile,
        huge_alpha=huge_alpha
    )
    return fig_to_response(fig)


def model_point_csv(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    point = get_object_or_404(ParameterChoice, model__id=model_id, number=point_id)

    mission_profile = model.mission_profile
    alpha = point.alpha
    beta_over_H = point.beta_over_H
    vw = point.vw if point.vw else model.vw
    T_star = point.T_star if point.T_star else model.T_star
    g_star = point.g_star if point.g_star else model.g_star

    csv = get_PS_data(
        T_star=T_star,
        g_star=g_star,
        vw=vw,
        alpha=alpha,
        beta_over_H=beta_over_H,
        mission_profile=mission_profile
    )
    return HttpResponse(csv, content_type="text/csv")


def model_point_ps(request, model_id, point_id):
    model = get_object_or_404(Model, pk=model_id)
    point = get_object_or_404(ParameterChoice, model__id=model_id, number=point_id)

    mission_profile = model.mission_profile
    alpha = point.alpha
    beta_over_H = point.beta_over_H
    vw = point.vw if point.vw else model.vw
    T_star = point.T_star if point.T_star else model.T_star
    g_star = point.g_star if point.g_star else model.g_star

    fig = get_PS_image(
        T_star=T_star,
        g_star=g_star,
        vw=vw,
        alpha=alpha,
        beta_over_H=beta_over_H,
        mission_profile=mission_profile
    )
    return fig_to_response(fig)


def model_scenario_plot(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    scenario = get_object_or_404(Scenario, model__id=model_id, number=scenario_id)
    scenario_list = Scenario.objects.filter(model__id=model_id) if model.has_scenarios else None
    point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__number=scenario_id)

    mission_profile_label = AVAILABLE_LABELS[model.mission_profile]
    context = {
        "model": model,
        "selected_scenario": scenario,
        "scenario_list": scenario_list,
        "point_list": point_list,
        "mission_profile_label": mission_profile_label
    }
    return render(request, "model_scenario_plot.html", context)


def model_scenario_snr(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    selected_scenario = get_object_or_404(Scenario, model__id=model_id, number=scenario_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__number=scenario_id)

    vw_list = [
        model.vw if point.vw is None else point.vw
        for point in point_list
    ]
    alpha_list = [point.alpha for point in point_list]
    beta_over_H_list = [point.beta_over_H for point in point_list]
    label_list = [point.short_label for point in point_list]

    T_star = selected_scenario.T_star if selected_scenario.T_star else model.T_star

    fig = get_SNR_image(
        vw_list=[vw_list],
        alpha_list=[alpha_list],
        beta_over_H_list=[beta_over_H_list],
        T_star=T_star,
        g_star=model.g_star,
        label_list=[label_list],
        title_list=[model.name],
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha
    )
    return fig_to_response(fig)


def model_scenario_snr_alphabeta(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    selected_scenario = get_object_or_404(Scenario, model__id=model_id, number=scenario_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__number=scenario_id)

    alpha_list = [point.alpha for point in point_list]
    BetaoverH_list = [point.beta_over_H for point in point_list]
    label_list = [point.short_label for point in point_list]

    T_star = selected_scenario.T_star if selected_scenario.T_star else model.T_star

    fig = get_SNR_alphabeta_image(
        vw=model.vw,
        alpha_list=[alpha_list],
        beta_over_H_list=[BetaoverH_list],
        T_star=T_star,
        g_star=model.g_star,
        labels=[label_list],
        titles=[model.name],
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha
    )
    return fig_to_response(fig)


def model_snr(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)

    if model.has_scenarios:
        scenario_list = Scenario.objects.filter(model__id=model_id)
        vw_list = []
        alpha_list = []
        beta_over_H_list = []
        label_list = []
        title_list = []

        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__id=scenario.id)
            vw_list.append([model.vw if point.vw is None else point.vw for point in point_list])
            alpha_list.append([point.alpha for point in point_list])
            beta_over_H_list.append([point.beta_over_H for point in point_list])
            label_list.append([point.short_label for point in point_list])
            title_list.append(scenario.name)
    else:
        point_list = ParameterChoice.objects.filter(model__id=model_id)
        vw_list=[[model.vw] * len(point_list)]
        alpha_list = [[point.alpha for point in point_list]]
        beta_over_H_list = [[point.beta_over_H for point in point_list]]
        label_list = [[point.short_label for point in point_list]]
        title_list = [model.name]

    fig = get_SNR_image(
        vw_list=vw_list,
        alpha_list=alpha_list,
        beta_over_H_list=beta_over_H_list,
        T_star=model.T_star,
        g_star=model.g_star,
        label_list=label_list,
        title_list=title_list,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha
    )
    return fig_to_response(fig)


def model_snr_alphabeta(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)

    if model.has_scenarios:
        scenario_list = Scenario.objects.filter(model__id=model_id)

        alpha_list = []
        beta_over_H_list = []
        label_list = []
        title_list = []

        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__id=scenario.id)
            alpha_list.append([point.alpha for point in point_list])
            beta_over_H_list.append([point.beta_over_H for point in point_list])
            label_list.append([point.short_label for point in point_list])
            title_list.append(scenario.name)

    else:
        point_list = ParameterChoice.objects.filter(model__id=model_id)
        alpha_list = [[point.alpha for point in point_list]]
        beta_over_H_list = [[point.beta_over_H for point in point_list]]
        label_list = [[point.short_label for point in point_list]]
        title_list = [model.name]

    fig = get_SNR_alphabeta_image(
        vw=model.vw,
        alpha_list=alpha_list,
        beta_over_H_list=beta_over_H_list,
        T_star=model.T_star,
        g_star=model.g_star,
        labels=label_list,
        titles=title_list,
        mission_profile=model.mission_profile,
        huge_alpha=model.huge_alpha
    )
    return fig_to_response(fig)


def parameterchoice_form(request: HttpRequest) -> HttpResponse:
    model = Model.objects.all()[0]
    point_list = ParameterChoice.objects.filter(model__name=model.name)

    form = ParameterChoiceForm()
    context = {
        "model": model.name,
        "form": form,
        "point_list": point_list
    }
    return render(request, "parameterchoice.html", context)


def multiple(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = MultipleForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            # querystring = request.GET.urlencode()
            # usetex = form.cleaned_data["usetex"]

            vw = form.cleaned_data["vw"]
            T_star = form.cleaned_data["T_star"]
            g_star = form.cleaned_data["g_star"]
            mission_profile = int(form.cleaned_data["mission_profile"])
            table = form.cleaned_data["table"]

            # SNRfilename = precomputed_filenames[MissionProfile]

            table_lines = table.splitlines()

            alpha_list = []
            BetaoverH_list = []
            label_list = []

            read_lines = 0

            for line in table_lines:
                line = line.strip()
                if len(line) == 0 or line[0] == "#":
                    continue

                read_lines += 1

                bits = line.split(",")
                alpha_list.append(float(bits[0]))
                BetaoverH_list.append(float(bits[1]))
                try:
                    label_list.append(bits[2].strip())
                except IndexError:
                    pass

            if not len(label_list) == read_lines:
                label_list_final = None
            else:
                label_list_final = [label_list]

            sio_SNR = get_SNR_alphabeta_image(
                vw=vw,
                alpha_list=[alpha_list],
                beta_over_H_list=[BetaoverH_list],
                T_star=T_star,
                g_star=g_star,
                mission_profile=mission_profile,
                labels=label_list_final
            )
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")
    # Form not valid or not filled out
    return render(request, "multiple.html", {"form": MultipleForm()})


def single(request: HttpRequest) -> HttpResponse:
    querystring = request.GET.urlencode()

    # if this is a POST request we need to process the form data
    if request.method == "GET" and not (querystring==""):
        # create a form instance and populate it with data from the request:
        form = PTPlotForm(request.GET)

        # check whether it's valid:
        if form.is_valid():
            # usetex = form.cleaned_data["usetex"]

            vw = form.cleaned_data["vw"]
            alpha = form.cleaned_data["alpha"]
            beta_over_H = form.cleaned_data["beta_over_H"]

            mission_profile = int(form.cleaned_data["mission_profile"])
            mission_profile_label = AVAILABLE_LABELS[mission_profile]
            T_star = form.cleaned_data["T_star"]
            g_star = form.cleaned_data["g_star"]

            context = {
                "form": form,
                "querystring": querystring,
                "vw": vw,
                "alpha": alpha,
                "beta_over_H": beta_over_H,
                "T_star": T_star,
                "g_star": g_star,
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
