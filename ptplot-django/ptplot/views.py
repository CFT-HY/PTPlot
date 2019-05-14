
# Django core stuff
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

# Django app stuff
from .forms import *

# Science
from .science.SNRubarfrstar_onthefly import get_SNR_image_threaded
from .science.SNRalphabeta_onthefly import get_SNR_alphabeta_image_threaded
from .science.powerspectrum import get_PS_image_threaded
from .science.precomputed import *

import sys, string
import numpy as np

# Image views
def ps_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']
            Senscurve = int(form.cleaned_data['Senscurve'])
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']
                
            sio_PS = get_PS_image_threaded(Tstar=Tstar,
                                           gstar=gstar,
                                           vw=vw,
                                           alpha=alpha,
                                           BetaoverH=BetaoverH,
                                           Senscurve=Senscurve)
            
            return HttpResponse(sio_PS.read(), content_type="image/svg+xml")

def snr_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']

            Senscurve = int(form.cleaned_data['Senscurve'])
            SNRfilename = precomputed_filenames[Senscurve]

            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']
            sio_SNR = get_SNR_image_threaded(Tstar=Tstar,
                                             gstar=gstar,
                                             vw_list=[[vw]],
                                             alpha_list=[[alpha]],
                                             BetaoverH_list=[[BetaoverH]],
                                             Senscurve=Senscurve)
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def snr_alphabeta_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            BetaoverH = form.cleaned_data['BetaoverH']

            Senscurve = int(form.cleaned_data['Senscurve'])
            SNRfilename = precomputed_filenames[Senscurve]
            
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']


            sio_SNR = get_SNR_alphabeta_image_threaded(vw=vw,
                                                       alpha_list=[[alpha]],
                                                       BetaoverH_list=[[BetaoverH]],
                                                       Tstar=Tstar,
                                                       gstar=gstar,
                                                       Senscurve=Senscurve)
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")

        
def theory(request):

    theories_list = Theory.objects.all()
    
    template = loader.get_template('ptplot/theories.html')
    
    context = {'theories_list': theories_list}
    return HttpResponse(template.render(context, request))

def theory_detail(request, theory_id):
    
    theory = Theory.objects.get(pk=theory_id)

    if theory.theory_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_theory__id=theory_id)
    else:
        scenario_list = None
        
    point_list = ParameterChoice.objects.filter(theory__id=theory_id)

#    for i in range(len(point_list)):
#        point_list[i].update_snrchoice()
    
    template = loader.get_template('ptplot/theory_detail.html')

    sensitivity_curve_label = available_labels[theory.theory_Senscurve]
    
    context = {'theory': theory,
               'point_list': point_list,
               'scenario_list': scenario_list,
               'sensitivity_curve_label': sensitivity_curve_label}
    return HttpResponse(template.render(context, request))



def theory_detail_plot(request, theory_id):
    
    theory = Theory.objects.get(pk=theory_id)
    point_list = ParameterChoice.objects.filter(theory__id=theory_id)

    if theory.theory_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_theory__id=theory_id)
    else:
        scenario_list = None
    
#    for i in range(len(point_list)):
#        point_list[i].update_snrchoice()

    sensitivity_curve_label = available_labels[theory.theory_Senscurve]
        
    template = loader.get_template('ptplot/theory_detail_plot.html')
    
    context = {'theory': theory,
               'point_list': point_list,
               'scenario_list': scenario_list,
               'sensitivity_curve_label': sensitivity_curve_label}
    return HttpResponse(template.render(context, request))

def theory_point_plot(request, theory_id, point_id):
    
    theory = Theory.objects.get(pk=theory_id)

    if theory.theory_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_theory__id=theory_id)
    else:
        scenario_list = None

    point_list = ParameterChoice.objects.filter(theory__id=theory_id)
    point = ParameterChoice.objects.get(theory__id=theory_id,
                                             number=point_id)
    
    sensitivity_curve_label = available_labels[theory.theory_Senscurve]
        
    template = loader.get_template('ptplot/theory_point_plot.html')
    
    context = {'theory': theory,
               'point_list': point_list,
               'scenario_list': scenario_list,
               'point': point,
               'sensitivity_curve_label': sensitivity_curve_label}
    return HttpResponse(template.render(context, request))



def theory_point_snr(request, theory_id, point_id):
    
    theory = Theory.objects.get(pk=theory_id)
    point = ParameterChoice.objects.get(theory__id=theory_id,
                                             number=point_id)

    Senscurve = theory.theory_Senscurve
    
    alpha = point.alpha
    BetaoverH = point.BetaoverH


    if point.vw:
        vw = point.vw
    else:
        vw = theory.theory_vw
    
    if point.Tstar:
        Tstar = point.Tstar
    else:
        Tstar = theory.theory_Tstar

    if point.gstar:
        gstar = point.gstar
    else:
        gstar = theory.theory_gstar

    label = point.point_shortlabel
        
    sio_SNR = get_SNR_image_threaded(Tstar=Tstar,
                                     gstar=gstar,
                                     vw_list=[[vw]],
                                     alpha_list=[[alpha]],
                                     BetaoverH_list=[[BetaoverH]],
                                     label_list=[[label]],
                                     Senscurve=Senscurve)
    
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")

def theory_point_snr_alphabeta(request, theory_id, point_id):
    theory = Theory.objects.get(pk=theory_id)
    point = ParameterChoice.objects.get(theory__id=theory_id,
                                             number=point_id)

    Senscurve = theory.theory_Senscurve
    
    alpha = point.alpha
    BetaoverH = point.BetaoverH


    if point.vw:
        vw = point.vw
    else:
        vw = theory.theory_vw
    
    if point.Tstar:
        Tstar = point.Tstar
    else:
        Tstar = theory.theory_Tstar

    if point.gstar:
        gstar = point.gstar
    else:
        gstar = theory.theory_gstar

    label = point.point_shortlabel
        
    sio_SNR = get_SNR_alphabeta_image_threaded(Tstar=Tstar,
                                               gstar=gstar,
                                               vw=vw,
                                               alpha_list=[[alpha]],
                                               BetaoverH_list=[[BetaoverH]],
                                               label_list=[[label]],
                                               Senscurve=Senscurve)
    
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")

    

def theory_point_ps(request, theory_id, point_id):

    theory = Theory.objects.get(pk=theory_id)
    point = ParameterChoice.objects.get(theory__id=theory_id,
                                             number=point_id)

    Senscurve = theory.theory_Senscurve
    
    alpha = point.alpha
    BetaoverH = point.BetaoverH


    if point.vw:
        vw = point.vw
    else:
        vw = theory.theory_vw
    
    if point.Tstar:
        Tstar = point.Tstar
    else:
        Tstar = theory.theory_Tstar

    if point.gstar:
        gstar = point.gstar
    else:
        gstar = theory.theory_gstar

    label = point.point_shortlabel
        
    
    sio_PS = get_PS_image_threaded(Tstar=Tstar,
                                   gstar=gstar,
                                   vw=vw,
                                   alpha=alpha,
                                   BetaoverH=BetaoverH,
                                   Senscurve=Senscurve)
            
    return HttpResponse(sio_PS.read(), content_type="image/svg+xml")


def theory_scenario_plot(request, theory_id, scenario_id):


    
    theory = Theory.objects.get(pk=theory_id)

    if theory.theory_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_theory__id=theory_id)
    else:
        scenario_list = None

    selected_scenario = Scenario.objects.get(scenario_theory__id=theory_id, scenario_number=scenario_id)
    point_list = ParameterChoice.objects.filter(theory__id=theory_id,
                                                scenario__scenario_number=scenario_id)
    
    sensitivity_curve_label = available_labels[theory.theory_Senscurve]
        
    template = loader.get_template('ptplot/theory_scenario_plot.html')
    
    context = {'theory': theory,
               'selected_scenario': selected_scenario,
               'scenario_list': scenario_list,
               'point_list': point_list,
               'sensitivity_curve_label': sensitivity_curve_label}
    return HttpResponse(template.render(context, request))



def theory_scenario_snr(request, theory_id, scenario_id):
    
    theory = Theory.objects.get(pk=theory_id)
    selected_scenario = Scenario.objects.get(scenario_theory__id=theory_id, scenario_number=scenario_id)
    point_list = ParameterChoice.objects.filter(theory__id=theory_id,
                                                scenario__scenario_number=scenario_id)

    vw_list = [theory.theory_vw if point.vw == None else point.vw for point in point_list]
    alpha_list = [point.alpha for point in point_list]
    BetaoverH_list = [point.BetaoverH for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]

    Tstar = theory.theory_Tstar
    if selected_scenario.scenario_Tstar:
        Tstar = selected_scenario.scenario_Tstar
        
    
    sio_SNR = get_SNR_image_threaded(vw_list=[vw_list],
                                     alpha_list=[alpha_list],
                                     BetaoverH_list=[BetaoverH_list],
                                     Tstar=Tstar,
                                     gstar=theory.theory_gstar,
                                     label_list=[label_list],
                                     title_list=[theory.theory_name],
                                     Senscurve=theory.theory_Senscurve)
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def theory_scenario_snr_alphabeta(request, theory_id, scenario_id):
    theory = Theory.objects.get(pk=theory_id)
    selected_scenario = Scenario.objects.get(scenario_theory__id=theory_id, scenario_number=scenario_id)
    point_list = ParameterChoice.objects.filter(theory__id=theory_id,
                                                scenario__scenario_number=scenario_id)

    alpha_list = [point.alpha for point in point_list]
    BetaoverH_list = [point.BetaoverH for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]
    

    Tstar = theory.theory_Tstar
    if selected_scenario.scenario_Tstar:
        Tstar = selected_scenario.scenario_Tstar

    
    sio_SNR = get_SNR_alphabeta_image_threaded(vw=theory.theory_vw,
                                     alpha_list=[alpha_list],
                                     BetaoverH_list=[BetaoverH_list],
                                     Tstar=Tstar,
                                     gstar=theory.theory_gstar,
                                     label_list=[label_list],
                                     title_list=[theory.theory_name],
                                     Senscurve=theory.theory_Senscurve)
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


    



def theory_snr(request, theory_id):

    theory = Theory.objects.get(pk=theory_id)

    if theory.theory_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_theory__id=theory_id)

        vw_list = []
        alpha_list = []
        BetaoverH_list = []
        label_list = []
        title_list = []
        
        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(theory__id=theory_id,
                                                        scenario__id=scenario.id)
            vw_list.append([theory.theory_vw if point.vw == None else point.vw for point in point_list])
            alpha_list.append([point.alpha for point in point_list])
            BetaoverH_list.append([point.BetaoverH for point in point_list])
            label_list.append([point.point_shortlabel for point in point_list])
            title_list.append(scenario.scenario_name)


    else:
        scenario_list = None
    
        point_list = ParameterChoice.objects.filter(theory__id=theory_id)

        vw_list=[[theory.theory_vw]*len(point_list)]
        alpha_list = [[point.alpha for point in point_list]]
        BetaoverH_list = [[point.BetaoverH for point in point_list]]
        label_list = [[point.point_shortlabel for point in point_list]]
        title_list = [theory.theory_name]
        
    sio_SNR = get_SNR_image_threaded(vw_list=vw_list,
                                     alpha_list=alpha_list,
                                     BetaoverH_list=BetaoverH_list,
                                     Tstar=theory.theory_Tstar,
                                     gstar=theory.theory_gstar,
                                     label_list=label_list,
                                     title_list=title_list,
                                     Senscurve=theory.theory_Senscurve)
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def theory_snr_alphabeta(request, theory_id):


    theory = Theory.objects.get(pk=theory_id)

    if theory.theory_hasScenarios:
        scenario_list = Scenario.objects.filter(scenario_theory__id=theory_id)

        alpha_list = []
        BetaoverH_list = []
        label_list = []
        title_list = []
        
        for scenario in scenario_list:
            point_list = ParameterChoice.objects.filter(theory__id=theory_id,
                                                        scenario__id=scenario.id)
            alpha_list.append([point.alpha for point in point_list])
            BetaoverH_list.append([point.BetaoverH for point in point_list])
            label_list.append([point.point_shortlabel for point in point_list])
            title_list.append(scenario.scenario_name)

    else:
        scenario_list = None

        point_list = ParameterChoice.objects.filter(theory__id=theory_id)

        alpha_list = [[point.alpha for point in point_list]]
        BetaoverH_list = [[point.BetaoverH for point in point_list]]
        label_list = [[point.point_shortlabel for point in point_list]]
        title_list = [theory.theory_name]
        
    sio_SNR = get_SNR_alphabeta_image_threaded(vw=theory.theory_vw,
                                               alpha_list=alpha_list,
                                               BetaoverH_list=BetaoverH_list,
                                               Tstar=theory.theory_Tstar,
                                               gstar=theory.theory_gstar,
                                               label_list=label_list,
                                               title_list=title_list,
                                               Senscurve=theory.theory_Senscurve)
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


        
def parameterchoice_form(request):
    
    theory = Theory.objects.all()[0]
    
    point_list = ParameterChoice.objects.filter(theory__theory_name
                                                = theory.theory_name)

    
    template = loader.get_template('ptplot/parameterchoice.html')
    form = ParameterChoiceForm()
    
    context = {'theory': theory.theory_name,
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
            Senscurve = int(form.cleaned_data['Senscurve'])
            table = form.cleaned_data['table']

#            SNRfilename = precomputed_filenames[Senscurve]

            
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
                label_list = None
                
            sio_SNR = get_SNR_alphabeta_image_threaded(vw=vw,
                                                       alpha_list=[alpha_list],
                                                       BetaoverH_list=[BetaoverH_list],
                                                       Tstar=Tstar,
                                                       gstar=gstar,
                                                       Senscurve=Senscurve,
                                                       label_list=[label_list])
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

            Senscurve = int(form.cleaned_data['Senscurve'])
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']

            template = loader.get_template('ptplot/single_result.html')

            context = {'form': form,
                       'querystring': querystring,
                       'vw': vw,
                       'alpha': alpha,
                       'BetaoverH': BetaoverH,
                       'Tstar': Tstar,
                       'gstar': gstar}
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
    template = loader.get_template('ptplot/index.html')
    return HttpResponse(template.render({}, request))
    
