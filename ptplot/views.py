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
    beta_over_H = form.cleaned_data["BetaoverH"]
    mission_profile = int(form.cleaned_data["MissionProfile"])
    T_star = form.cleaned_data["Tstar"]
    g_star = form.cleaned_data["gstar"]

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
    beta_over_H = form.cleaned_data["BetaoverH"]
    mission_profile = int(form.cleaned_data["MissionProfile"])
    Tstar = form.cleaned_data["Tstar"]
    gstar = form.cleaned_data["gstar"]

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
    beta_over_H = form.cleaned_data["BetaoverH"]

    mission_profile = int(form.cleaned_data["MissionProfile"])
    # SNRfilename = precomputed_filenames[MissionProfile]

    Tstar = form.cleaned_data["Tstar"]
    gstar = form.cleaned_data["gstar"]
    fig = get_SNR_image(
        T_star=Tstar,
        g_star=gstar,
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
    beta_over_H = form.cleaned_data["BetaoverH"]

    mission_profile = int(form.cleaned_data["MissionProfile"])
    # SNRfilename = precomputed_filenames[MissionProfile]

    T_star = form.cleaned_data["Tstar"]
    g_star = form.cleaned_data["gstar"]

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
    scenario_list = Scenario.objects.filter(scenario_model__id=model_id) if model.model_hasScenarios else None

   # for i in range(len(point_list)):
   #     point_list[i].update_snrchoice()

    context = {
        "model": model,
        "point_list": point_list,
        "scenario_list": scenario_list,
        "MissionProfile_label": AVAILABLE_LABELS[model.model_MissionProfile]
    }
    return render(request, "model_detail.html", context)


def model_detail_plot(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id)
    scenario_list = Scenario.objects.filter(scenario_model__id=model_id) if model.model_hasScenarios else None

   # for i in range(len(point_list)):
   #     point_list[i].update_snrchoice()

    context = {
        "model": model,
        "point_list": point_list,
        "scenario_list": scenario_list,
        "MissionProfile_label": AVAILABLE_LABELS[model.model_MissionProfile]
    }
    return render(request, "model_detail_plot.html", context)


def model_point_plot(request: HttpRequest, model_id: int, point_id: int):
    model = get_object_or_404(Model, pk=model_id)
    point = get_object_or_404(ParameterChoice, model__id=model_id, id=point_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id)
    scenario_list = Scenario.objects.filter(scenario_model__id=model_id) if model.model_hasScenarios else None

    context = {
        "model": model,
        "point": point,
        "point_list": point_list,
        "scenario_list": scenario_list,
        "MissionProfile_label": AVAILABLE_LABELS[model.model_MissionProfile]
    }
    return render(request, "model_point_plot.html", context)


def model_point_snr(request: HttpRequest, model_id: int, point_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    point = get_object_or_404(ParameterChoice, model__id=model_id, number=point_id)

    mission_profile = model.model_MissionProfile
    alpha = point.alpha
    beta_over_H = point.BetaoverH
    vw = point.vw if point.vw else model.model_vw
    T_star = point.Tstar if point.Tstar else model.model_Tstar
    g_star = point.gstar if point.gstar else model.model_gstar

    label = point.point_shortlabel
    huge_alpha = model.model_hugeAlpha
    
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

    mission_profile = model.model_MissionProfile
    alpha = point.alpha
    beta_over_H = point.BetaoverH
    vw = point.vw if point.vw else model.model_vw
    T_star = point.Tstar if point.Tstar else model.model_Tstar
    g_star = point.gstar if point.gstar else model.model_gstar

    label = point.point_shortlabel
    huge_alpha = model.model_hugeAlpha
        
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

    mission_profile = model.model_MissionProfile
    alpha = point.alpha
    beta_over_H = point.BetaoverH
    vw = point.vw if point.vw else model.model_vw
    T_star = point.Tstar if point.Tstar else model.model_Tstar
    g_star = point.gstar if point.gstar else model.model_gstar

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

    mission_profile = model.model_MissionProfile
    alpha = point.alpha
    beta_over_H = point.BetaoverH
    vw = point.vw if point.vw else model.model_vw
    T_star = point.Tstar if point.Tstar else model.model_Tstar
    g_star = point.gstar if point.gstar else model.model_gstar

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
    scenario = get_object_or_404(Scenario, scenario_model__id=model_id, scenario_number=scenario_id)
    scenario_list = Scenario.objects.filter(scenario_model__id=model_id) if model.model_hasScenarios else None
    point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__scenario_number=scenario_id)

    mission_profile_label = AVAILABLE_LABELS[model.model_MissionProfile]
    context = {"model": model,
               "selected_scenario": scenario,
               "scenario_list": scenario_list,
               "point_list": point_list,
               "MissionProfile_label": mission_profile_label}
    return render(request, "model_scenario_plot.html", context)


def model_scenario_snr(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    selected_scenario = get_object_or_404(Scenario, scenario_model__id=model_id, scenario_number=scenario_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__scenario_number=scenario_id)

    vw_list = [
        model.model_vw if point.vw is None else point.vw
        for point in point_list
    ]
    alpha_list = [point.alpha for point in point_list]
    beta_over_H_list = [point.BetaoverH for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]

    T_star = selected_scenario.scenario_Tstar if selected_scenario.scenario_Tstar else model.model_Tstar

    fig = get_SNR_image(
        vw_list=[vw_list],
        alpha_list=[alpha_list],
        beta_over_H_list=[beta_over_H_list],
        T_star=T_star,
        g_star=model.model_gstar,
        label_list=[label_list],
        title_list=[model.model_name],
        mission_profile=model.model_MissionProfile,
        huge_alpha=model.model_hugeAlpha
    )
    return fig_to_response(fig)


def model_scenario_snr_alphabeta(request: HttpRequest, model_id: int, scenario_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)
    selected_scenario = get_object_or_404(Scenario, scenario_model__id=model_id, scenario_number=scenario_id)
    point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__scenario_number=scenario_id)

    alpha_list = [point.alpha for point in point_list]
    BetaoverH_list = [point.BetaoverH for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]

    T_star = selected_scenario.scenario_Tstar if selected_scenario.scenario_Tstar else model.model_Tstar

    fig = get_SNR_alphabeta_image(
        vw=model.model_vw,
        alpha_list=[alpha_list],
        beta_over_H_list=[BetaoverH_list],
        T_star=T_star,
        g_star=model.model_gstar,
        labels=[label_list],
        titles=[model.model_name],
        mission_profile=model.model_MissionProfile,
        huge_alpha=model.model_hugeAlpha
    )
    return fig_to_response(fig)


def model_snr(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)

    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)
        vw_list = []
        alpha_list = []
        beta_over_H_list = []
        label_list = []
        title_list = []

        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__id=scenario.id)
            vw_list.append([model.model_vw if point.vw is None else point.vw for point in point_list])
            alpha_list.append([point.alpha for point in point_list])
            beta_over_H_list.append([point.BetaoverH for point in point_list])
            label_list.append([point.point_shortlabel for point in point_list])
            title_list.append(scenario.scenario_name)
    else:
        point_list = ParameterChoice.objects.filter(model__id=model_id)
        vw_list=[[model.model_vw] * len(point_list)]
        alpha_list = [[point.alpha for point in point_list]]
        beta_over_H_list = [[point.BetaoverH for point in point_list]]
        label_list = [[point.point_shortlabel for point in point_list]]
        title_list = [model.model_name]

    fig = get_SNR_image(
        vw_list=vw_list,
        alpha_list=alpha_list,
        beta_over_H_list=beta_over_H_list,
        T_star=model.model_Tstar,
        g_star=model.model_gstar,
        label_list=label_list,
        title_list=title_list,
        mission_profile=model.model_MissionProfile,
        huge_alpha=model.model_hugeAlpha
    )
    return fig_to_response(fig)


def model_snr_alphabeta(request: HttpRequest, model_id: int) -> HttpResponse:
    model = get_object_or_404(Model, pk=model_id)

    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)

        alpha_list = []
        beta_over_H_list = []
        label_list = []
        title_list = []

        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(model__id=model_id, scenario__id=scenario.id)
            alpha_list.append([point.alpha for point in point_list])
            beta_over_H_list.append([point.BetaoverH for point in point_list])
            label_list.append([point.point_shortlabel for point in point_list])
            title_list.append(scenario.scenario_name)

    else:
        point_list = ParameterChoice.objects.filter(model__id=model_id)
        alpha_list = [[point.alpha for point in point_list]]
        beta_over_H_list = [[point.BetaoverH for point in point_list]]
        label_list = [[point.point_shortlabel for point in point_list]]
        title_list = [model.model_name]

    fig = get_SNR_alphabeta_image(
        vw=model.model_vw,
        alpha_list=alpha_list,
        beta_over_H_list=beta_over_H_list,
        T_star=model.model_Tstar,
        g_star=model.model_gstar,
        labels=label_list,
        titles=title_list,
        mission_profile=model.model_MissionProfile,
        huge_alpha=model.model_hugeAlpha
    )
    return fig_to_response(fig)


def parameterchoice_form(request: HttpRequest) -> HttpResponse:
    model = Model.objects.all()[0]
    point_list = ParameterChoice.objects.filter(model__model_name=model.model_name)

    form = ParameterChoiceForm()
    context = {
        "model": model.model_name,
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
            T_star = form.cleaned_data["Tstar"]
            g_star = form.cleaned_data["gstar"]
            mission_profile = int(form.cleaned_data["MissionProfile"])
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
            beta_over_H = form.cleaned_data["BetaoverH"]

            mission_profile = int(form.cleaned_data["MissionProfile"])
            mission_profile_label = AVAILABLE_LABELS[mission_profile]
            T_star = form.cleaned_data["Tstar"]
            g_star = form.cleaned_data["gstar"]

            context = {
                "form": form,
                "querystring": querystring,
                "vw": vw,
                "alpha": alpha,
                "BetaoverH": beta_over_H,
                "Tstar": T_star,
                "g_star": g_star,
                "MissionProfile_label": mission_profile_label
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
