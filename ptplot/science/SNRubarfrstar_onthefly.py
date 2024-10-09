#!/usr/bin/env python3

"""Create the UbarfRstar plot

This file contains all the functions related to producing the UbarfRstar plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).

Contains the following function:
    * get_SNR_image - creates the UbarfRstar plot
"""

import math
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import numpy as np
import os.path
import io
import sys
import time

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:
    import matplotlib.figure
    from espinosa import kappav, ubarf
    from SNR_precompute import get_SNRcurve
    from precomputed import available_labels
    root = './'
else:
    from .espinosa import kappav, ubarf
    from .SNR_precompute import get_SNRcurve
    from django.conf import settings
    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')

def get_SNR_image(vw_list=[[0.5]], alpha_list=[[0.1]], BetaoverH_list=[[100]],
                  Tstar=100,
                  gstar=100,
                  adiabaticRatio=4.0/3.0,
                  label_list=None,
                  title_list=None,
                  MissionProfile=0,
                  usetex=False,
                  hugeAlpha=False):
    """Produce the UbarfRstar plot

    Parameters
    ----------
    vw_list : list[float]
        List of wall velocities
    alpha_list : list[float]
        List of phase transition strengths
    BetaoverH_list : list[float]
        List of inverse phase transition durations
    Tstar : float
        Transition temperature (default to 100)
    gstar : float
        Degrees of freedom (default to 100)
    adiabaticRatio : float
        Adiabatic index (Gamma) (default to 4.0/3.0)
    label_list : list[string]
        List of labels
    title_list : list[string]
        List of titles
    MissionProfile : int
        Which sensitivity curve to use
    usetex : bool
        Flag for using latex (default to False)
    hugeAlpha : bool
        Flag for if alpha is very large (default to False)

    Returns
    -------
    sio : bytes
        svg plot of UbarfRstar
    """

    color_tuple = plt.cm.plasma_r(np.linspace(0.1, 1, 6))

    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')

    if hugeAlpha:
        ubarfmax = 1000
    else:
        ubarfmax = 1

    tshHn, snr, log10HnRstar, log10Ubarf = get_SNRcurve(Tstar, gstar, MissionProfile, ubarfmax)
    
    levels = np.array([1,5,10,20,50,100])
    levels_tsh = np.array([0.001,0.01,0.1,1,10,100])
    # Only if hugeAlpha in play
    levels_tsh_hugeAlpha = np.array([0.0000001,0.000001,0.00001,0.0001])
    
    # Where to put contour label, based on y-coordinate and contour value
    def find_place(snr, wantedy, wantedcontour):
        nearesty = (np.abs(log10HnRstar-wantedy)).argmin()
        nearestx = (np.abs(snr[nearesty,:]-wantedcontour)).argmin()

        return (log10Ubarf[nearestx],wantedy)

    # Location of contour labels
    locs = [find_place(snr, -2.5, wantedcontour) for wantedcontour in levels]
    locs_tsh = [(-1.8,-3.5), (-1.8,-2.5), (-1.8,-1.8), (-1.8,-0.5)]

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)
    
    CS = ax.contour(log10Ubarf, log10HnRstar, snr, levels, linewidths=1,
                    colors=color_tuple,
                     extent=(log10Ubarf[0], log10Ubarf[-1],
                             log10HnRstar[0], log10HnRstar[-1]))
    CStsh = ax.contour(log10Ubarf, log10HnRstar, tshHn, levels_tsh, linewidths=1,
                       linestyles='dashed', colors='k',
                       extent=(log10Ubarf[0], log10Ubarf[-1],
                               log10HnRstar[0], log10HnRstar[-1]))

    if hugeAlpha:
        # These don't get annotated with labels
        CStsh_hugeAlpha = ax.contour(log10Ubarf, log10HnRstar, tshHn, levels_tsh_hugeAlpha, linewidths=1,
                                     linestyles='dashed', colors='k',
                                     extent=(log10Ubarf[0], log10Ubarf[-1],
                                             log10HnRstar[0], log10HnRstar[-1]))

    # CSturb = ax.contourf(log10Ubarf, log10HnRstar, tshHn, [0.00001, 1], colors=('gray'), alpha=0.3,
    CSturb = ax.contourf(log10Ubarf, log10HnRstar, tshHn, [0.0001, 1],
                         colors=('white'), alpha=0.2, hatches='x',
                         extent=(log10Ubarf[0], log10Ubarf[-1],
                                 log10HnRstar[0], log10HnRstar[-1]))

    ax.clabel(CS, inline=1, fontsize=8, fmt="%.0f", manual=locs)
    ax.clabel(CStsh, inline=1, fontsize=8, fmt="%g", manual=locs_tsh)
    # plt.title(r'SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs')
    # plt.xlabel(r'$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $',fontsize=16)
    ax.set_ylabel(r'$H_{\rm n} R_* $', fontsize=14)
    ax.set_xlabel(r'$\overline{U}_{\rm f}$', fontsize=14)
    ax.set_xlim(min(log10Ubarf),max(log10Ubarf))
    ax.set_ylim(min(log10HnRstar),max(log10HnRstar))

    for i, (vw_set, BetaoverH_set, alpha_set) in enumerate(zip(vw_list, BetaoverH_list,
                                                               alpha_list)):

        Rstar_set = [math.log10(math.pow(8.0*math.pi,1.0/3.0)*vw/BetaoverH) \
                      for vw, BetaoverH in zip(vw_set, BetaoverH_set)]

        ubarf_set = [math.log10(ubarf(vw, alpha, adiabaticRatio)) \
                      for vw, alpha in zip(vw_set, alpha_set)]

        benchmarks = ax.plot(ubarf_set, Rstar_set, '.')

        if label_list:
            label_set = label_list[i]
            for x,y,label in zip(ubarf_set, Rstar_set, label_set):
                ax.annotate(label, xy=(x,y), xycoords='data', xytext=(5,0),
                            textcoords='offset points')

    if title_list:
        legends = title_list
        leg = ax.legend(legends, loc='lower left', framealpha=0.9)

    # Old attempts at getting the ticks in the right place
    # xtickpos = [min(log10Ubarf)] \
    #     + list(range(int(round(min(log10Ubarf))),
    #                  int(round(max(log10Ubarf))+1))) \
    #     + [max(log10Ubarf)]
    # xticklabels = [r'$10^{%.2g}$' % min(log10Ubarf)] \
    #     + [r'$10^{%d}$' % ind
    #        for ind in list(range(int(round(min(log10Ubarf))),
    #                              int(round(max(log10Ubarf))+1)))] \
    #     + [r'$10^{%.2g}$' % max(log10Ubarf)]

    # ytickpos = [min(log10HnRstar)] \
    #     + list(range(int(math.ceil(min(log10HnRstar))),
    #                  int(round(max(log10HnRstar))+1))) \
    #     + [max(log10HnRstar)]
    # yticklabels = [r'$10^{%.2g}$' % min(log10HnRstar)] \
    #     + [r'$10^{%d}$' % ind
    #        for ind in list(range(int(math.ceil(min(log10HnRstar))),
    #                              int(round(max(log10HnRstar))+1)))] \
    #     + [r'$10^{%.2g}$' % max(log10HnRstar)]

    if hugeAlpha:
        xtickpos = [-2, -1, 0, 1, 2, 3]
        xticklabels = [ r'$10^{-2}$', r'$10^{-1}$', r'$1$',
                        r'$10$', r'$10^2$', r'$10^3$']
    else:
        xtickpos = list(range(int(math.ceil(min(log10Ubarf))),
                    int(math.floor(max(log10Ubarf))+1)))
        xticklabels = [r'$10^{%d}$' % ind
                for ind in list(range(int(math.ceil(min(log10Ubarf))),
                                        int(math.floor(max(log10Ubarf))+1)))]

    ytickpos = list(range(int(math.ceil(min(log10HnRstar))),
                        int(math.floor(max(log10HnRstar))+1)))
    yticklabels = [r'$10^{%d}$' % ind
                    for ind in list(
                            range(int(math.ceil(min(log10HnRstar))),
                                    int(math.floor(max(log10HnRstar))+1)))]

    # Find location for minor ticks
    def make_minorticks(min, max):
        minorticks = np.array([])
        for i in range(min,max):
            minorticks = np.append(minorticks, np.linspace(10**i, 10**(i+1), 9, endpoint=False))
        return np.log10(minorticks)

    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.set_xticks(ticks=make_minorticks(int(math.ceil(min(log10Ubarf))),
                                        int(math.floor(max(log10Ubarf)))), minor=True)
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)
    ax.set_yticks(ticks=make_minorticks(int(math.ceil(min(log10HnRstar))),
                                        int(math.floor(max(log10HnRstar)))), minor=True)

    # July 2023: No longer watermark with LISACosWG
    # # position bottom right
    # fig.text(0.95, 0.05, 'LISACosWG',
    #          fontsize=50, color='gray',
    #          ha='right', va='bottom', alpha=0.4)

    # position top left
    fig.text(0.13, 0.87, time.asctime(),
             fontsize=8, color='black',
             ha='left', va='top', alpha=1.0)

    sio = io.BytesIO()
    fig.savefig(sio, format="svg")
    sio.seek(0)
        
    return sio

# If this is used standalone, check the right amount of arguments are being
# passed. If not, show the user the expected input.
if __name__ == '__main__':
    if len(sys.argv) == 7:
        vw = float(sys.argv[1])
        alpha = float(sys.argv[2])
        betaoverh = float(sys.argv[3])
        T = float(sys.argv[4])
        g = float(sys.argv[5])
        MissionProfile = int(sys.argv[6])
        b = get_SNR_image([[vw]], [[alpha]], [[betaoverh]], T, g, MissionProfile=MissionProfile)
        print(b.read().decode("utf-8"))
    else:
        sys.stderr.write('Usage: %s <vw> <alpha> <Beta/H> <T*> <g*> <MissionProfile>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n\n')
        sys.stderr.write('Available sensitivity curves:\n')
        for number,label in enumerate(available_labels):
            sys.stderr.write('%d: %s\n' % (number, label))
