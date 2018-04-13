


import math, sys, string

import matplotlib
matplotlib.use('Agg')
import numpy as np
import io, base64
import cgi
import os.path
import sys

from .curves import PowerSpectrum

from django.conf import settings

BASE_DIR = getattr(settings, "BASE_DIR", None)
root = os.path.join(BASE_DIR, 'ptplot', 'science')
# sys.stderr.write('root = ' + root + '\n')


import matplotlib.figure

def get_PS_image(vw=0.95, Tstar=100, alpha=0.1, HoverBeta=100, usetex=False):
    curves_ps = PowerSpectrum(vw=vw,
                              Tstar=Tstar,
                              alpha=alpha,
                              HoverBeta=HoverBeta)

    # setup latex plotting
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    # make font size bigger
    # matplotlib.rcParams.update({'font.size': 16})
    # but make legend smaller
    # matplotlib.rcParams.update({'legend.fontsize': 14})

    sens_filehandle = open(os.path.join(root,'Sens_L6A2M5N2P2D28.txt'))
    f, sensitivity \
        = np.loadtxt(sens_filehandle,usecols=[0,3],unpack=True)

    f_more = np.logspace(math.log(min(f)), math.log(max(f)), num=len(f)*10)

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)
    
    ax.fill_between(f,sensitivity,1,alpha=0.3, label=r'LISA sensitivity')
    ax.plot(f_more, curves_ps.power_spectrum_sw(f_more), 'r', label=r'$\Omega_\mathrm{sw}$')
    ax.plot(f_more, curves_ps.power_spectrum_turb(f_more), 'b', label=r'$\Omega_\mathrm{turb}$')
    ax.plot(f_more, curves_ps.power_spectrum(f_more), 'k', label=r'Total')
    ax.set_xlabel(r'$f\; \mathrm{(Hz)}$', fontsize=14)
    ax.set_ylabel(r'$h^2 \, \Omega_\mathrm{GW}(f)$', fontsize=14)
    ax.set_xlim([1e-5,0.1])
    ax.set_ylim([1e-16,1e-8])
    ax.set_yscale('log', nonposy='clip')
    ax.set_xscale('log', nonposx='clip')
    ax.legend(loc='upper right')
#    plt.tight_layout()

    sio = io.BytesIO()

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    canvas = FigureCanvas(fig)
    
    fig.savefig(sio, format="svg")
    sio.seek(0)
#    plt.close()
    return sio
