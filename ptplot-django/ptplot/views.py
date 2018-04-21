
# Django core stuff
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

# Django app stuff
from .forms import PTPlotForm

# Science
from .science.SNR import get_SNR_image
from .science.powerspectrum import get_PS_image
from .science.precomputed import *

import sys

# Image views
def ps_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            HoverBeta = form.cleaned_data['HoverBeta']

            SNRcurve = int(form.cleaned_data['SNRcurve'])
            
            SNRfilename = precomputed_filenames[SNRcurve]
            Tstar = precomputed_Tn[SNRcurve]
            hstar = precomputed_hstar[SNRcurve]
            
            sys.stderr.write('passing alpha %g\n' % alpha)
            sio_PS = get_PS_image(Tstar=Tstar, vw=vw,
                                  alpha=alpha, HoverBeta=HoverBeta)
            return HttpResponse(sio_PS.read(), content_type="image/svg+xml")

def snr_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            HoverBeta = form.cleaned_data['HoverBeta']

            SNRcurve = int(form.cleaned_data['SNRcurve'])

            SNRfilename = precomputed_filenames[SNRcurve]
            Tstar = precomputed_Tn[SNRcurve]
            hstar = precomputed_hstar[SNRcurve]

            sio_SNR = get_SNR_image(vw_list=[vw],
                                    alpha_list=[alpha],
                                    HoverBeta_list=[HoverBeta],
                                    SNRcurve=SNRfilename)
            return HttpResponse(sio_SNR.read(), content_type="image/svg+xml")
    
def ptplot_form(request):
    # if this is a POST request we need to process the form data
    if request.method == 'GET':
        # create a form instance and populate it with data from the request:
        form = PTPlotForm(request.GET)

        # check whether it's valid:
        if form.is_valid():
            querystring = request.GET.urlencode()
#            usetex = form.cleaned_data['usetex']


            vw = form.cleaned_data['vw']
            alpha = form.cleaned_data['alpha']
            HoverBeta = form.cleaned_data['HoverBeta']
            SNRcurve = int(form.cleaned_data['SNRcurve'])
            Tn = precomputed_Tn[SNRcurve]
            hstar = precomputed_hstar[SNRcurve]

                                            
            template = loader.get_template('ptplot/ptplotresult.html')

            context = {'form': form,
                       'querystring': querystring,
                       'vw': vw,
                       'alpha': alpha,
                       'HoverBeta': HoverBeta,
                       'Tn': Tn,
                       'hstar': hstar}
            return HttpResponse(template.render(context, request))

        
    # Form not valid or not filled out
    template = loader.get_template('ptplot/ptplot.html')
    form = PTPlotForm()
    context = {'form': form}
    return HttpResponse(template.render(context, request))

    
