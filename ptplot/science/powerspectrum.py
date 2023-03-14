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
import time

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:

    import matplotlib.figure

    from curves import PowerSpectrum
    from precomputed import available_sensitivitycurves, available_labels, available_durations
    
    root = './'

    # eLISATools from Antoine
    # from eLISATools import *
    from snr import *
    
else:

    from .curves import PowerSpectrum
    from .precomputed import available_sensitivitycurves, available_labels, available_durations

    from django.conf import settings

    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')


    # eLISATools from Antoine
    # from .eLISATools import *
    from .snr import *

sensitivity_root = os.path.join(root, 'sensitivity')


def get_PS_data(vw=0.95,
                 Tstar=100,
                 gstar=100,
                 alpha=0.1,
                 BetaoverH=100,
                 MissionProfile=0,
                 usetex=False,
                 sw_only=True):

    sensitivity_file=available_sensitivitycurves[MissionProfile]
    
    curves_ps = PowerSpectrum(vw=vw,
                              Tstar=Tstar,
                              alpha=alpha,
                              BetaoverH=BetaoverH,
                              gstar=gstar)


    sensitivity_curve = os.path.join(sensitivity_root, sensitivity_file)
    sens_filehandle = open(sensitivity_curve)
    f, sensitivity \
        = np.loadtxt(sens_filehandle,usecols=[0,2],unpack=True)

    f_more = np.logspace(math.log(min(f)), math.log(max(f)), num=len(f)*10)

    fS, OmEff = LoadFile(sensitivity_curve, 2)
    duration = yr*available_durations[MissionProfile]
    snr, frange = StockBkg_ComputeSNR(fS,
                                      OmEff,
                                      fS,
                                      curves_ps.power_spectrum_sw_conservative(fS),
                                      duration,
                                      1.e-6,
                                      1)


    
    res = ''

    if sw_only:
        res = res + 'f, omegaSens, omegaSW\n'
    else:
        res = res + 'f, omegaSens, omegaSW, omegaTurb, omegaTot\n'
        
    for x,y in zip(f, sensitivity):

        if sw_only:
            res = res + '%g, %g, %g\n' % (x,
                                          y,
                                          curves_ps.power_spectrum_sw_conservative(x))
        else:
            res = res + '%g, %g, %g, %g, %g\n' % (x,
                                                  y,
                                                  curves_ps.power_spectrum_sw_conservative(x),
                                                  curves_ps.power_spectrum_turb(x),
                                                  curves_ps.power_spectrum_conservative(x))

    return res

def get_PS_image(vw=0.95,
                 Tstar=100,
                 gstar=100,
                 alpha=0.1,
                 BetaoverH=100,
                 MissionProfile=0,
                 usetex=False,
                 sw_only=True):

    sensitivity_file=available_sensitivitycurves[MissionProfile]
    
    curves_ps = PowerSpectrum(vw=vw,
                              Tstar=Tstar,
                              alpha=alpha,
                              BetaoverH=BetaoverH,
                              gstar=gstar)

    # setup latex plotting
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    # make font size bigger
    # matplotlib.rcParams.update({'font.size': 16})
    # but make legend smaller
    # matplotlib.rcParams.update({'legend.fontsize': 14})

    sensitivity_curve = os.path.join(sensitivity_root, sensitivity_file)
    sens_filehandle = open(sensitivity_curve)
    f, sensitivity \
        = np.loadtxt(sens_filehandle,usecols=[0,2],unpack=True)

    f_more = np.logspace(math.log(min(f)), math.log(max(f)), num=len(f)*10)

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)


    fS, OmEff = LoadFile(sensitivity_curve, 2)
    duration = yr*available_durations[MissionProfile]
    snr, frange = StockBkg_ComputeSNR(fS,
                                      OmEff,
                                      fS,
                                      curves_ps.power_spectrum_sw_conservative(fS),
                                      duration,
                                      1.e-6,
                                      1)

#    sys.stderr.write('snr = %g\n' % snr)
    
    ax.fill_between(f, sensitivity, 1, alpha=0.3, label=r'LISA sensitivity')

    if sw_only:
        ax.plot(f_more, curves_ps.power_spectrum_sw_conservative(f_more), 'k',
                label=r'$\Omega_\mathrm{sw}$')
    else:
        ax.plot(f_more, curves_ps.power_spectrum_sw_conservative(f_more), 'r',
                label=r'$\Omega_\mathrm{sw}$')
        ax.plot(f_more, curves_ps.power_spectrum_turb(f_more), 'b',
                label=r'$\Omega_\mathrm{turb}$')
        ax.plot(f_more, curves_ps.power_spectrum_conservative(f_more), 'k',
                label=r'Total')
        
    ax.set_xlabel(r'$f\; \mathrm{(Hz)}$', fontsize=14)
    ax.set_ylabel(r'$h^2 \, \Omega_\mathrm{GW}(f)$', fontsize=14)
    ax.set_xlim([1e-5,0.1])
    ax.set_ylim([1e-16,1e-8])
    # the following lines could be simplified to one command, but we leave it like this for legacy reasons
    ax.set_yscale('log', nonpositive='clip')
    ax.set_xscale('log', nonpositive='clip')
    ax.legend(loc='upper right')



    # position bottom right
    fig.text(0.95, 0.05, 'LISACosWG',
             fontsize=50, color='gray',
             ha='right', va='bottom', alpha=0.4)

    # position top left
    fig.text(0.13, 0.87, r'%s [$\mathrm{SNR}_\mathrm{sw} = %g$]' % (time.asctime(), snr),
             fontsize=8, color='black',
             ha='left', va='top', alpha=1.0)

    
    sio = io.BytesIO()

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    canvas = FigureCanvas(fig)
    
    # fig.savefig("foo.png",format="png",dpi=400)
    fig.savefig(sio, format="svg")
    sio.seek(0)

    return sio




def worker(queue,
           vw=0.95,
           Tstar=100,
           gstar=100,
           alpha=0.1,
           BetaoverH=100,
           MissionProfile=0,
           usetex=False):

    try:
        queue.put(get_PS_image(vw,
                               Tstar,
                               gstar,
                               alpha,
                               BetaoverH,
                               MissionProfile,
                               usetex))
    except Exception as e:
        sys.stderr.write("Caught exception in powerspectrum worker: %s\n" % str(e))
        queue.put(None)


def get_PS_image_threaded(vw=0.95,
                          Tstar=100,
                          gstar=100,
                          alpha=0.1,
                          BetaoverH=100,
                          MissionProfile=0,
                          usetex=False):

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker,
                                args=(q,
                                      vw,
                                      Tstar,
                                      gstar,
                                      alpha,
                                      BetaoverH,
                                      MissionProfile,
                                      usetex))
    p.start()
    return_res = q.get()
    p.join()
    return return_res


if __name__ == '__main__':
    if len(sys.argv) == 6:
        vw = float(sys.argv[1])
        Tstar = float(sys.argv[2])
        gstar = float(sys.argv[3])
        alpha = float(sys.argv[4])
        BetaoverH = float(sys.argv[5]) 
        sys.stderr.write('vw=%g, Tstar=%g, gstar=%g, alpha=%g, BetaoverH=%g\n'
                         % (vw, Tstar, gstar, alpha, BetaoverH))
        b = get_PS_image(vw, Tstar, gstar, alpha, BetaoverH)
        print(b.read().decode("utf-8"))
    else:
        sys.stderr.write('Usage: %s <vw> <Tstar> <alpha> <Beta/H>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n')
