from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

import base64
import time

from .forms import PTPlotForm



from .SNR import get_SNR_image
from .powerspectrum import get_PS_image

def inline_image(image_sio):

#    return base64.b64encode(image_sio.read()).decode()

    return image_sio.read()
    
#    imgStr = "data:image/svg+xml;base64,"

#    imgStr += base64.b64encode(image_sio.read()).decode()

#    return("""
#    <img src="%s"></img>
#    """ % (imgStr))

def ps_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            tstar = form.cleaned_data['tstar']

            sio_PS = get_PS_image(Tstar=tstar, vw=vw) # , usetex=usetex)
            ps = inline_image(sio_PS)
            return HttpResponse(ps, content_type="image/svg+xml")

        
def snr_image(request):
    if request.method == 'GET':
        form = PTPlotForm(request.GET)

        if form.is_valid():
            vw = form.cleaned_data['vw']
            tstar = form.cleaned_data['tstar']

            sio_SNR = get_SNR_image(Tstar=tstar, vw=vw) # , usetex=usetex)
            snr = inline_image(sio_SNR)
            return HttpResponse(snr, content_type="image/svg+xml")
    
def ptplot_form(request):
    # if this is a POST request we need to process the form data
    if request.method == 'GET':
        # create a form instance and populate it with data from the request:
        form = PTPlotForm(request.GET)

        # check whether it's valid:
        if form.is_valid():
            vw = form.cleaned_data['vw']
            tstar = form.cleaned_data['tstar']
            querystring = request.GET.urlencode()
            #            usetex = form.cleaned_data['usetex']

#            start = time.time()
            



#            took = "{0:0.1f}".format(time.time() - start)
            
            template = loader.get_template('ptplot/ptplotresult.html')
            context = {'form': form,
                       'querystring': querystring}
            return HttpResponse(template.render(context, request))


        
    template = loader.get_template('ptplot/ptplot.html')
    form = PTPlotForm()
    context = {'form': form}
    return HttpResponse(template.render(context, request))

    
