#!/usr/bin/env python3


import math, sys, string

import matplotlib
matplotlib.use('Agg')
import numpy as np
import io, base64
import cgi
import os.path
import sys
import multiprocessing

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:

    import matplotlib.figure

    from curves import PowerSpectrum

    root = './'

    # eLISATools from Antoine
    from eLISATools import *
    
else:

    from .curves import PowerSpectrum

    from django.conf import settings

    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')


    # eLISATools from Antoine
    from .eLISATools import *




def get_PS_image(vw=0.95,
                 Tstar=100,
                 Gstar=100,
                 alpha=0.1,
                 HoverBeta=100,
                 sensitivity='ScienceRequirements.txt',
                 usetex=False):

    curves_ps = PowerSpectrum(vw=vw,
                              Tstar=Tstar,
                              alpha=alpha,
                              HoverBeta=HoverBeta,
                              gstar=Gstar)

    # setup latex plotting
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    # make font size bigger
    # matplotlib.rcParams.update({'font.size': 16})
    # but make legend smaller
    # matplotlib.rcParams.update({'legend.fontsize': 14})

    sensitivity_curve = os.path.join(root,sensitivity)
    sens_filehandle = open(sensitivity_curve)
    f, sensitivity \
        = np.loadtxt(sens_filehandle,usecols=[0,2],unpack=True)

    f_more = np.logspace(math.log(min(f)), math.log(max(f)), num=len(f)*10)

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)


    fS, OmEff = LoadFile(sensitivity_curve, 2)
    duration = 5*yr
    snr, frange = StockBkg_ComputeSNR(fS,
                                      OmEff,
                                      fS,
                                      curves_ps.power_spectrum(fS),
                                      duration,
                                      1.e-6,
                                      1)

    sys.stderr.write('snr = %g\n' % snr)
    
    ax.fill_between(f, sensitivity, 1, alpha=0.3, label=r'LISA sensitivity')

    ax.plot(f_more, curves_ps.power_spectrum_sw(f_more), 'r',
            label=r'$\Omega_\mathrm{sw}$')
    ax.plot(f_more, curves_ps.power_spectrum_turb(f_more), 'b',
            label=r'$\Omega_\mathrm{turb}$')
    ax.plot(f_more, curves_ps.power_spectrum(f_more), 'k',
            label=r'Total')

    ax.set_xlabel(r'$f\; \mathrm{(Hz)}$', fontsize=14)
    ax.set_ylabel(r'$h^2 \, \Omega_\mathrm{GW}(f)$', fontsize=14)
    ax.set_xlim([1e-5,0.1])
    ax.set_ylim([1e-16,1e-8])
    ax.set_yscale('log', nonposy='clip')
    ax.set_xscale('log', nonposx='clip')
    ax.legend(loc='upper right')



    # position bottom right
    fig.text(0.95, 0.05, 'LISACosWG',
             fontsize=50, color='gray',
             ha='right', va='bottom', alpha=0.4)

    sio = io.BytesIO()

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    canvas = FigureCanvas(fig)
    
    fig.savefig(sio, format="svg")
    sio.seek(0)

    return sio




def worker(queue,
           vw=0.95,
           Tstar=100,
           Gstar=100,
           alpha=0.1,
           HoverBeta=100,
           sensitivity='Sens_L6A2M5N2P2D28.txt',
           usetex=False):

    queue.put(get_PS_image(vw,
                           Tstar,
                           Gstar,
                           alpha,
                           HoverBeta,
                           sensitivity,
                           usetex))
    


def get_PS_image_threaded(vw=0.95,
                          Tstar=100,
                          Gstar=100,
                          alpha=0.1,
                          HoverBeta=100,
                          sensitivity='Sens_L6A2M5N2P2D28.txt',
                          usetex=False):

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker,
                                args=(q,
                                      vw,
                                      Tstar,
                                      Gstar,
                                      alpha,
                                      HoverBeta,
                                      sensitivity,
                                      usetex))
    p.start()
    return_res = q.get()
    p.join()
    return return_res


if __name__ == '__main__':
    if len(sys.argv) == 6:
        vw = float(sys.argv[1])
        Tstar = float(sys.argv[2])
        Gstar = float(sys.argv[3])
        alpha = float(sys.argv[4])
        HoverBeta = float(sys.argv[5]) 
        sys.stderr.write('vw=%g, Tstar=%g, Gstar=%g, alpha=%g, HoverBeta=%g\n'
                         % (vw, Tstar, Gstar, alpha, HoverBeta))
        b = get_PS_image(vw, Tstar, Gstar, alpha, HoverBeta)
        print(b.read().decode("utf-8"))
    else:
        sys.stderr.write('Usage: %s <vw> <Tstar> <alpha> <H/Beta>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n')
