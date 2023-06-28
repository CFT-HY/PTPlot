
# Django core stuff
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.template import loader

# Django app stuff
from .forms import *

# Science
from .science.SNRubarfrstar_onthefly import get_SNR_image_threaded
from .science.SNRalphabeta_onthefly import get_SNR_alphabeta_image_threaded
from .science.powerspectrum import get_PS_image_threaded, get_PS_data
from .science.precomputed import *

import sys, string
import numpy as np

# Retrieve git version
from dulwich.repo import Repo
import dulwich.porcelain
import os

git_description = 'unknown'
have_gitver = False

try:
     this_file_dir = os.path.dirname(__file__)
     git_description = dulwich.porcelain.describe(Repo.discover(this_file_dir))
     have_gitver = True
except dulwich.errors.NotGitRepository as err:
     pass

# CSV view
def csv(request):
    
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']
            MissionProfile = int(form.cleaned_data['MissionProfile'])
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']
                
            csv = get_PS_data(Tstar=Tstar,
                              gstar=gstar,
                              vw=vw,
                              alpha=alpha,
                              BetaoverH=BetaoverH,
                              MissionProfile=MissionProfile)
            
            return HttpResponse(csv, content_type="text/csv")
        
# Image views
def ps_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']
            MissionProfile = int(form.cleaned_data['MissionProfile'])
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']
                
            sio_PS = get_PS_image_threaded(Tstar=Tstar,
                                           gstar=gstar,
                                           vw=vw,
                                           alpha=alpha,
                                           BetaoverH=BetaoverH,
                                           MissionProfile=MissionProfile)
            
            return HttpResponse(sio_PS.read(), content_type="image/svg+xml")

def snr_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']

            MissionProfile = int(form.cleaned_data['MissionProfile'])
#            SNRfilename = precomputed_filenames[MissionProfile]

            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']
            sio_SNR = get_SNR_image_threaded(Tstar=Tstar,
                                             gstar=gstar,
                                             vw_list=[[vw]],
                                             alpha_list=[[alpha]],
                                             BetaoverH_list=[[BetaoverH]],
                                             MissionProfile=MissionProfile)
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def snr_alphabeta_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']

            MissionProfile = int(form.cleaned_data['MissionProfile'])
#            SNRfilename = precomputed_filenames[MissionProfile]
            
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']


            sio_SNR = get_SNR_alphabeta_image_threaded(vw=vw,
                                                       alpha_list=[[alpha]],
                                                       BetaoverH_list=[[BetaoverH]],
                                                       Tstar=Tstar,
                                                       gstar=gstar,
                                                       MissionProfile=MissionProfile)
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")

        
def model(request):

    models_list = Model.objects.all()
    
    template = loader.get_template('ptplot/models.html')
    
    context = {'models_list': models_list}
    return HttpResponse(template.render(context, request))

def model_detail(request, model_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)
        
    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)
    else:
        scenario_list = None
        
    point_list = ParameterChoice.objects.filter(model__id=model_id)

#    for i in range(len(point_list)):
#        point_list[i].update_snrchoice()
    
    template = loader.get_template('ptplot/model_detail.html')

    MissionProfile_label = available_labels[model.model_MissionProfile]
    
    context = {'model': model,
               'point_list': point_list,
               'scenario_list': scenario_list,
               'MissionProfile_label': MissionProfile_label}

    return HttpResponse(template.render(context, request))



def model_detail_plot(request, model_id):
    

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    point_list = ParameterChoice.objects.filter(model__id=model_id)

    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)
    else:
        scenario_list = None
    
#    for i in range(len(point_list)):
#        point_list[i].update_snrchoice()

    MissionProfile_label = available_labels[model.model_MissionProfile]
    
    template = loader.get_template('ptplot/model_detail_plot.html')
    
    context = {'model': model,
               'point_list': point_list,
               'scenario_list': scenario_list,
               'MissionProfile_label': MissionProfile_label}
    
    return HttpResponse(template.render(context, request))

def model_point_plot(request, model_id, point_id):
    
    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)
    else:
        scenario_list = None

    point_list = ParameterChoice.objects.filter(model__id=model_id)

    try:
        point = ParameterChoice.objects.get(model__id=model_id,
                                            number=point_id)
    except ParameterChoice.DoesNotExist:
        raise Http404("Parameter choice pont id=%d for model id=%d does not exist" % (point_id,model_id))

    MissionProfile_label = available_labels[model.model_MissionProfile]
        
    template = loader.get_template('ptplot/model_point_plot.html')
    
    context = {'model': model,
               'point_list': point_list,
               'scenario_list': scenario_list,
               'point': point,
               'MissionProfile_label': MissionProfile_label}
    return HttpResponse(template.render(context, request))



def model_point_snr(request, model_id, point_id):
    

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    try:
        point = ParameterChoice.objects.get(model__id=model_id,
                                            number=point_id)
    except ParameterChoice.DoesNotExist:
        raise Http404("Parameter choice pont id=%d for model id=%d does not exist" % (point_id,model_id))

    


    MissionProfile = model.model_MissionProfile
    
    alpha = point.alpha
    BetaoverH = point.BetaoverH


    if point.vw:
        vw = point.vw
    else:
        vw = model.model_vw
    
    if point.Tstar:
        Tstar = point.Tstar
    else:
        Tstar = model.model_Tstar

    if point.gstar:
        gstar = point.gstar
    else:
        gstar = model.model_gstar

    label = point.point_shortlabel

    hugeAlpha = model.model_hugeAlpha
    
    sio_SNR = get_SNR_image_threaded(Tstar=Tstar,
                                     gstar=gstar,
                                     vw_list=[[vw]],
                                     alpha_list=[[alpha]],
                                     BetaoverH_list=[[BetaoverH]],
                                     label_list=[[label]],
                                     MissionProfile=MissionProfile,
                                     hugeAlpha=hugeAlpha)
    
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")

def model_point_snr_alphabeta(request, model_id, point_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    try:
        point = ParameterChoice.objects.get(model__id=model_id,
                                            number=point_id)
    except ParameterChoice.DoesNotExist:
        raise Http404("Parameter choice pont id=%d for model id=%d does not exist" % (point_id,model_id))

    MissionProfile = model.model_MissionProfile
    
    alpha = point.alpha
    BetaoverH = point.BetaoverH


    if point.vw:
        vw = point.vw
    else:
        vw = model.model_vw
    
    if point.Tstar:
        Tstar = point.Tstar
    else:
        Tstar = model.model_Tstar

    if point.gstar:
        gstar = point.gstar
    else:
        gstar = model.model_gstar

    label = point.point_shortlabel

    hugeAlpha = model.model_hugeAlpha
        
    sio_SNR = get_SNR_alphabeta_image_threaded(Tstar=Tstar,
                                               gstar=gstar,
                                               vw=vw,
                                               alpha_list=[[alpha]],
                                               BetaoverH_list=[[BetaoverH]],
                                               label_list=[[label]],
                                               MissionProfile=MissionProfile,
                                               hugeAlpha=hugeAlpha)
    
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")

    

def model_point_csv(request, model_id, point_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    try:
        point = ParameterChoice.objects.get(model__id=model_id,
                                            number=point_id)
    except ParameterChoice.DoesNotExist:
        raise Http404("Parameter choice pont id=%d for model id=%d does not exist" % (point_id,model_id))
    

    MissionProfile = model.model_MissionProfile
    
    alpha = point.alpha
    BetaoverH = point.BetaoverH


    if point.vw:
        vw = point.vw
    else:
        vw = model.model_vw
    
    if point.Tstar:
        Tstar = point.Tstar
    else:
        Tstar = model.model_Tstar

    if point.gstar:
        gstar = point.gstar
    else:
        gstar = model.model_gstar

    label = point.point_shortlabel
        
    
    csv = get_PS_data(Tstar=Tstar,
                      gstar=gstar,
                      vw=vw,
                      alpha=alpha,
                      BetaoverH=BetaoverH,
                      MissionProfile=MissionProfile)
            
    return HttpResponse(csv, content_type="text/csv")




def model_point_ps(request, model_id, point_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    try:
        point = ParameterChoice.objects.get(model__id=model_id,
                                            number=point_id)
    except ParameterChoice.DoesNotExist:
        raise Http404("Parameter choice pont id=%d for model id=%d does not exist" % (point_id,model_id))
    

    MissionProfile = model.model_MissionProfile
    
    alpha = point.alpha
    BetaoverH = point.BetaoverH


    if point.vw:
        vw = point.vw
    else:
        vw = model.model_vw
    
    if point.Tstar:
        Tstar = point.Tstar
    else:
        Tstar = model.model_Tstar

    if point.gstar:
        gstar = point.gstar
    else:
        gstar = model.model_gstar

    label = point.point_shortlabel
        
    
    sio_PS = get_PS_image_threaded(Tstar=Tstar,
                                   gstar=gstar,
                                   vw=vw,
                                   alpha=alpha,
                                   BetaoverH=BetaoverH,
                                   MissionProfile=MissionProfile)
            
    return HttpResponse(sio_PS.read(), content_type="image/svg+xml")


def model_scenario_plot(request, model_id, scenario_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)


    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)
    else:
        scenario_list = None

    try:
        selected_scenario = Scenario.objects.get(scenario_model__id=model_id, scenario_number=scenario_id)
        point_list = ParameterChoice.objects.filter(model__id=model_id,
                                                    scenario__scenario_number=scenario_id)
    except Scenario.DoesNotExist:
        raise Http404("Scenario id=%d does not exist for model id=%d" % (scenario_id,model_id))        
    
    MissionProfile_label = available_labels[model.model_MissionProfile]
        
    template = loader.get_template('ptplot/model_scenario_plot.html')
    
    context = {'model': model,
               'selected_scenario': selected_scenario,
               'scenario_list': scenario_list,
               'point_list': point_list,
               'MissionProfile_label': MissionProfile_label}
    return HttpResponse(template.render(context, request))



def model_scenario_snr(request, model_id, scenario_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    try:
        selected_scenario = Scenario.objects.get(scenario_model__id=model_id, scenario_number=scenario_id)
    except Scenario.DoesNotExist:
        raise Http404("Scenario id=%d does not exist for model id=%d" % (scenario_id,model_id))
        
    point_list = ParameterChoice.objects.filter(model__id=model_id,
                                                scenario__scenario_number=scenario_id)

    vw_list = [model.model_vw if point.vw == None else point.vw for point in point_list]
    alpha_list = [point.alpha for point in point_list]
    BetaoverH_list = [point.BetaoverH for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]

    Tstar = model.model_Tstar
    if selected_scenario.scenario_Tstar:
        Tstar = selected_scenario.scenario_Tstar
        
    
    sio_SNR = get_SNR_image_threaded(vw_list=[vw_list],
                                     alpha_list=[alpha_list],
                                     BetaoverH_list=[BetaoverH_list],
                                     Tstar=Tstar,
                                     gstar=model.model_gstar,
                                     label_list=[label_list],
                                     title_list=[model.model_name],
                                     MissionProfile=model.model_MissionProfile,
                                     hugeAlpha=model.model_hugeAlpha)
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def model_scenario_snr_alphabeta(request, model_id, scenario_id):
    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)

    try:
        selected_scenario = Scenario.objects.get(scenario_model__id=model_id, scenario_number=scenario_id)
    except Scenario.DoesNotExist:
        raise Http404("Scenario id=%d does not exist for model id=%d" % (scenario_id,model_id))

    point_list = ParameterChoice.objects.filter(model__id=model_id,
                                                scenario__scenario_number=scenario_id)

    alpha_list = [point.alpha for point in point_list]
    BetaoverH_list = [point.BetaoverH for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]
    

    Tstar = model.model_Tstar
    if selected_scenario.scenario_Tstar:
        Tstar = selected_scenario.scenario_Tstar

    
    sio_SNR = get_SNR_alphabeta_image_threaded(vw=model.model_vw,
                                     alpha_list=[alpha_list],
                                     BetaoverH_list=[BetaoverH_list],
                                     Tstar=Tstar,
                                     gstar=model.model_gstar,
                                     label_list=[label_list],
                                     title_list=[model.model_name],
                                     MissionProfile=model.model_MissionProfile,
                                     hugeAlpha=model.model_hugeAlpha)

    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


    



def model_snr(request, model_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)


    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)

        vw_list = []
        alpha_list = []
        BetaoverH_list = []
        label_list = []
        title_list = []
        
        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(model__id=model_id,
                                                        scenario__id=scenario.id)
            vw_list.append([model.model_vw if point.vw == None else point.vw for point in point_list])
            alpha_list.append([point.alpha for point in point_list])
            BetaoverH_list.append([point.BetaoverH for point in point_list])
            label_list.append([point.point_shortlabel for point in point_list])
            title_list.append(scenario.scenario_name)


    else:
        scenario_list = None
    
        point_list = ParameterChoice.objects.filter(model__id=model_id)

        vw_list=[[model.model_vw]*len(point_list)]
        alpha_list = [[point.alpha for point in point_list]]
        BetaoverH_list = [[point.BetaoverH for point in point_list]]
        label_list = [[point.point_shortlabel for point in point_list]]
        title_list = [model.model_name]
        
    sio_SNR = get_SNR_image_threaded(vw_list=vw_list,
                                     alpha_list=alpha_list,
                                     BetaoverH_list=BetaoverH_list,
                                     Tstar=model.model_Tstar,
                                     gstar=model.model_gstar,
                                     label_list=label_list,
                                     title_list=title_list,
                                     MissionProfile=model.model_MissionProfile,
                                     hugeAlpha=model.model_hugeAlpha)
                                     
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def model_snr_alphabeta(request, model_id):

    try:
        model = Model.objects.get(pk=model_id)
    except Model.DoesNotExist:
        raise Http404("Model id=%d does not exist" % model_id)



    if model.model_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_model__id=model_id)

        alpha_list = []
        BetaoverH_list = []
        label_list = []
        title_list = []
        
        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(model__id=model_id,
                                                        scenario__id=scenario.id)
            alpha_list.append([point.alpha for point in point_list])
            BetaoverH_list.append([point.BetaoverH for point in point_list])
            label_list.append([point.point_shortlabel for point in point_list])
            title_list.append(scenario.scenario_name)

    else:
        scenario_list = None

        point_list = ParameterChoice.objects.filter(model__id=model_id)

        alpha_list = [[point.alpha for point in point_list]]
        BetaoverH_list = [[point.BetaoverH for point in point_list]]
        label_list = [[point.point_shortlabel for point in point_list]]
        title_list = [model.model_name]
        
    sio_SNR = get_SNR_alphabeta_image_threaded(vw=model.model_vw,
                                               alpha_list=alpha_list,
                                               BetaoverH_list=BetaoverH_list,
                                               Tstar=model.model_Tstar,
                                               gstar=model.model_gstar,
                                               label_list=label_list,
                                               title_list=title_list,
                                               MissionProfile=model.model_MissionProfile,
                                               hugeAlpha=model.model_hugeAlpha)                                               
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


        
def parameterchoice_form(request):
    
    model = Model.objects.all()[0]
    
    point_list = ParameterChoice.objects.filter(model__model_name
                                                = model.model_name)

    
    template = loader.get_template('ptplot/parameterchoice.html')
    form = ParameterChoiceForm()
    
    context = {'model': model.model_name,
               'form': form,
               'point_list': point_list}
    return HttpResponse(template.render(context, request))

    

def multiple(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = MultipleForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
#            querystring = request.GET.urlencode()
#            usetex = form.cleaned_data['usetex']


            vw = form.cleaned_data['vw']
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']
            MissionProfile = int(form.cleaned_data['MissionProfile'])
            table = form.cleaned_data['table']

#            SNRfilename = precomputed_filenames[MissionProfile]

            
            table_lines = table.splitlines()

            alpha_list = []
            BetaoverH_list = []
            label_list = []

            read_lines = 0
            
            for line in table_lines:
                line = line.strip()
                if len(line) == 0 or line[0] == '#':
                    continue

                read_lines += 1
                
                bits = line.split(',')
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
                
            sio_SNR = get_SNR_alphabeta_image_threaded(vw=vw,
                                                       alpha_list=[alpha_list],
                                                       BetaoverH_list=[BetaoverH_list],
                                                       Tstar=Tstar,
                                                       gstar=gstar,
                                                       MissionProfile=MissionProfile,
                                                       label_list=label_list_final)
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")
    # Form not valid or not filled out
    template = loader.get_template('ptplot/multiple.html')
    form = MultipleForm()
    context = {'form': form}
    return HttpResponse(template.render(context, request))

    

def single(request):

    querystring = request.GET.urlencode()
    
    # if this is a POST request we need to process the form data
    if request.method == 'GET' and not (querystring==''):
        # create a form instance and populate it with data from the request:
        form = PTPlotForm(request.GET)
        
        # check whether it's valid:
        if form.is_valid():
            
#            usetex = form.cleaned_data['usetex']


            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']

            MissionProfile = int(form.cleaned_data['MissionProfile'])
            MissionProfile_label = available_labels[MissionProfile]
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']

            template = loader.get_template('ptplot/single_result.html')

            context = {'form': form,
                       'querystring': querystring,
                       'vw': vw,
                       'alpha': alpha,
                       'BetaoverH': BetaoverH,
                       'Tstar': Tstar,
                       'gstar': gstar,
                       'MissionProfile_label': MissionProfile_label}
            return HttpResponse(template.render(context, request))

        # Form not valid
        template = loader.get_template('ptplot/single.html')
        context = {'form': form}
        return HttpResponse(template.render(context, request))

            
        
    # No form yet
    template = loader.get_template('ptplot/single.html')
    form = PTPlotForm()
    context = {'form': form}
    return HttpResponse(template.render(context, request))

    

def index(request):
    context = {}

    if have_gitver:
        context['git_description'] = git_description
    
    template = loader.get_template('ptplot/index.html')
    return HttpResponse(template.render(context, request))
    
