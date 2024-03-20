#!/usr/bin/env python3

"""Create the power spectrum plot

This file contains all the functions related to producing the power spectrum plot.

Contains the following functions:
    * get_PS_data - gets the data for the power spectrum plot and stores it
    * get_PS_image - creates the power spectrum plot
"""

import math
import matplotlib
matplotlib.use('Agg')
import numpy as np
import io
import os.path
import time

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:
    import matplotlib.figure
    from calculate_powerspectrum import PowerSpectrum
    from precomputed import available_sensitivitycurves, available_labels, available_durations
    root = './'
    from snr import *
else:
    from .calculate_powerspectrum import PowerSpectrum
    from .precomputed import available_sensitivitycurves, available_labels, available_durations
    from django.conf import settings
    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')
    from .snr import *
sensitivity_root = os.path.join(root, 'sensitivity')

def get_PS_data(vw=0.9,
                alpha=0.1,
                BetaoverH=10,
                Tstar=180,
                gstar=100,
                adiabaticRatio=4.0/3.0,
                MissionProfile=0,
                usetex=False,
                sw_only=True):
    """Retrieve the data for the power spectrum plot

    Note that this is not then used to create the plot, this stores the data,
    to be exported as a csv if requested.

    Parameters
    ----------
    vw : float
        Wall velocity (default to 0.9)
    Tstar : float
        Transition temperature (default to 180)
    gstar : float
        Degrees of freedom (default to 100)
    alpha : float
        Phase transition strength (default to 0.1)
    BetaoverH : float
        Inverse phase transition duration relative to H (default to 10)
    adiabaticRatio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    MissionProfile : int
        Which sensitivity curve to use
    usetex : bool
        Flag for using latex (default to False)
    sw_only : bool
        Flag to decide if we want to ignore turbulence (default to True)

    Returns
    -------
    res : string
        String containing all the data to reproduce the power spectrum plot
    """

    sensitivity_file=available_sensitivitycurves[MissionProfile]
    
    curves_ps = PowerSpectrum(vw=vw,
                              Tstar=Tstar,
                              alpha=alpha,
                              BetaoverH=BetaoverH,
                              gstar=gstar,
                              adiabaticRatio=adiabaticRatio)

    sensitivity_curve = os.path.join(sensitivity_root, sensitivity_file)
    sens_filehandle = open(sensitivity_curve)
    f, sensitivity \
        = np.loadtxt(sens_filehandle,usecols=[0,2],unpack=True)

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

def get_PS_image(vw=0.9,
                 alpha=0.1,
                 BetaoverH=10,
                 Tstar=180,
                 gstar=100,
                 adiabaticRatio=4.0/3.0,
                 MissionProfile=0,
                 usetex=False,
                 sw_only=True):
    """Produce the power spectrum plot

    Parameters
    ----------
    vw : float
        Wall velocity (default to 0.9)
    Tstar : float
        Transition temperature (default to 180)
    gstar : float
        Degrees of freedom (default to 100)
    alpha : float
        Phase transition strength (default to 0.1)
    BetaoverH : float
        Inverse phase transition duration relative to H (default to 10)
    adiabaticRatio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    MissionProfile : int
        Which sensitivity curve to use
    usetex : bool
        Flag for using latex (default to False)
    sw_only : bool
        Flag to decide if we want to ignore turbulence (default to True)

    Returns
    -------
    sio : bytes
        svg plot of the power spectrum
    """

    sensitivity_file=available_sensitivitycurves[MissionProfile]
    
    curves_ps = PowerSpectrum(vw=vw,
                              Tstar=Tstar,
                              alpha=alpha,
                              BetaoverH=BetaoverH,
                              gstar=gstar,
                              adiabaticRatio=adiabaticRatio)

    # Uncomment to set up latex plotting
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    # Uncomment to make font size bigger
    # matplotlib.rcParams.update({'font.size': 16})
    # Uncomment to make legend smaller
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
    ax.set_yscale('log', nonpositive='clip')
    ax.set_xscale('log', nonpositive='clip')
    ax.legend(loc='upper right')

    # July 2023: No longer watermark with LISACosWG
    # # position bottom right
    # fig.text(0.95, 0.05, 'LISACosWG',
    #          fontsize=50, color='gray',
    #          ha='right', va='bottom', alpha=0.4)

    # position top left
    fig.text(0.13, 0.87, r'%s [$\mathrm{SNR}_\mathrm{sw} = %g$]' % (time.asctime(), snr),
             fontsize=8, color='black',
             ha='left', va='top', alpha=1.0)

    
    sio = io.BytesIO()
    fig.savefig(sio, format="svg")
    sio.seek(0)

    return sio

# If this is used standalone, check the right amount of arguments are being
# passed. If not, show the user the expected input.
if __name__ == '__main__':
    if len(sys.argv) == 6:
        vw = float(sys.argv[1])
        alpha = float(sys.argv[2])
        BetaoverH = float(sys.argv[3])
        Tstar = float(sys.argv[4])
        gstar = float(sys.argv[5])
        sys.stderr.write('vw=%g, alpha=%g, BetaoverH=%g, Tstar=%g, gstar=%g\n'
                         % (vw, alpha, BetaoverH, Tstar, gstar))
        b = get_PS_image(vw, alpha, BetaoverH, Tstar, gstar)
        print(b.read().decode("utf-8"))
    else:
        sys.stderr.write('Usage: %s <vw> <alpha> <Beta/H> <Tstar> <gstar>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n')