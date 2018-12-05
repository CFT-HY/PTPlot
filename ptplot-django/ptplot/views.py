
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

# Image views
def ps_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            HoverBeta = form.cleaned_data['HoverBeta']
            Senscurve = int(form.cleaned_data['Senscurve'])
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']
                
            sio_PS = get_PS_image_threaded(Tstar=Tstar,
                                           gstar=gstar,
                                           vw=vw,
                                           alpha=alpha,
                                           HoverBeta=HoverBeta,
                                           Senscurve=Senscurve)
            
            return HttpResponse(sio_PS.read(), content_type="image/svg+xml")

def snr_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            HoverBeta = form.cleaned_data['HoverBeta']

            Senscurve = int(form.cleaned_data['Senscurve'])
            SNRfilename = precomputed_filenames[Senscurve]

            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']

            sio_SNR = get_SNR_image_threaded(Tstar=Tstar,
                                             gstar=gstar,
                                             vw_list=[vw],
                                             alpha_list=[alpha],
                                             HoverBeta_list=[HoverBeta],
                                             Senscurve=Senscurve)
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def snr_alphabeta_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            HoverBeta = form.cleaned_data['HoverBeta']

            Senscurve = int(form.cleaned_data['Senscurve'])
            SNRfilename = precomputed_filenames[Senscurve]
            
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']


            sio_SNR = get_SNR_alphabeta_image_threaded(vw_list=[vw],
                                                       alpha_list=[alpha],
                                                       HoverBeta_list=[HoverBeta],
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

    point_list = ParameterChoice.objects.filter(theory__id=theory_id)

    for i in range(len(point_list)):
        point_list[i].update_snrchoice()
    
    template = loader.get_template('ptplot/theory_detail.html')
    
    context = {'theory': theory,
               'point_list': point_list}
    return HttpResponse(template.render(context, request))



def theory_detail_plot(request, theory_id):
    
    theory = Theory.objects.get(pk=theory_id)
    point_list = ParameterChoice.objects.filter(theory__id=theory_id)

    for i in range(len(point_list)):
        point_list[i].update_snrchoice()

        
    template = loader.get_template('ptplot/theory_detail_plot.html')
    
    context = {'theory': theory,
               'point_list': point_list}
    return HttpResponse(template.render(context, request))


def theory_snr(request, theory_id):


    theory = Theory.objects.get(pk=theory_id)

    point_list = ParameterChoice.objects.filter(theory__id=theory_id)

    title = theory.theory_name
    vw_list = [point.vw for point in point_list]
    alpha_list = [point.alpha for point in point_list]
    HoverBeta_list = [point.HoverBeta for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]
    SNRfilename = precomputed_filenames[point_list[0].Senscurve]
    
    sio_SNR = get_SNR_image_threaded(vw_list,
                                     alpha_list,
                                     HoverBeta_list,
                                     Tstar, gstar,
                                     label_list,
                                     title)
    return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")


def theory_snr_alphabeta(request, theory_id):


    theory = Theory.objects.get(pk=theory_id)

    point_list = ParameterChoice.objects.filter(theory__id=theory_id)

    title = theory.theory_name
    vw_list = [point.vw for point in point_list]
    alpha_list = [point.alpha for point in point_list]
    HoverBeta_list = [point.HoverBeta for point in point_list]
    label_list = [point.point_shortlabel for point in point_list]
    SNRfilename = precomputed_filenames[point_list[0].Senscurve]
    
    sio_SNR = get_SNR_alphabeta_image_threaded(vw_list,
                                               alpha_list,
                                               HoverBeta_list,
                                               SNRfilename,
                                               label_list,
                                               title)
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
            Senscurve = int(form.cleaned_data['Senscurve'])
            table = form.cleaned_data['table']

            table_lines = string.split(table,'\n')
            alpha_list = []
            betaoverH_list = []
            label_list = []
            for line in table_lines:
                bits = string.split(line,',')
                alpha_list.append(float(bits[0]))
                betaoverH_list.append(float(bits[1]))
                label_list.append(bits[2])
            
            template = loader.get_template('ptplot/multiple_result.html')

            context = {'form': form,
                       'vw': vw,
                       'alpha_list': alpha,
                       'betaoverH_list': betaoverH_list,
                       'label_list': label_list}
            return HttpResponse(template.render(context, request))


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
            HoverBeta = form.cleaned_data['HoverBeta']

            Senscurve = int(form.cleaned_data['Senscurve'])
            Tstar = form.cleaned_data['Tstar']
            gstar = form.cleaned_data['gstar']

            template = loader.get_template('ptplot/single_result.html')

            context = {'form': form,
                       'querystring': querystring,
                       'vw': vw,
                       'alpha': alpha,
                       'HoverBeta': HoverBeta,
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
    
