from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

import base64
import time

from .forms import PTPlotForm



from .SNR import get_SNR_image
from .powerspectrum import get_PS_image

def inline_image(image_sio):

    return base64.b64encode(image_sio.read()).decode()
    
#    imgStr = "data:image/svg+xml;base64,"

#    imgStr += base64.b64encode(image_sio.read()).decode()

#    return("""
#    <img src="%s"></img>
#    """ % (imgStr))
    

def ptplot_form(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PTPlotForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            vw = form.cleaned_data['vw']
            tstar = form.cleaned_data['tstar']
            usetex = form.cleaned_data['usetex']

            start = time.time()
            
            sio_PS = get_PS_image(Tstar=tstar, vw=vw, usetex=usetex)
            ps = inline_image(sio_PS)
            sio_SNR = get_SNR_image(Tstar=tstar, vw=vw, usetex=usetex)
            snr = inline_image(sio_SNR)

            took = "{0:0.1f}".format(time.time() - start)
            
            template = loader.get_template('ptplot/ptplotresult.html')
            context = {'form': form, 'ps': ps, 'snr': snr, 'took': took}
            return HttpResponse(template.render(context, request))


    # if a GET (or any other method) we'll create a blank form
    else:
        template = loader.get_template('ptplot/ptplot.html')
        form = PTPlotForm()
        context = {'form': form}
        return HttpResponse(template.render(context, request))

    
