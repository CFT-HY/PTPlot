#!/usr/bin/env python3

"""Create the AlphaBeta plot

This file contains all the functions related to producing the AlphaBeta plot.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015). SNR plots for PTPlot by David Weir (Feb 2018).

Contains the following function:
    * get_SNR_alphabeta_image - creates the AlphaBeta plot
"""

import math
import matplotlib
matplotlib.use('Agg')
import numpy as np
import os.path
import io
import time

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:
    import matplotlib.figure
    from espinosa import kappav, ubarf, ubarf_to_alpha
    from SNR_precompute import get_SNRcurve
    from calculate_powerspectrum import rstar_to_beta
    from precomputed import available_labels
    root = './'
    from snr import *
else:
    from .espinosa import kappav, ubarf, ubarf_to_alpha
    from .SNR_precompute import get_SNRcurve
    from .calculate_powerspectrum import rstar_to_beta
    from django.conf import settings
    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')
    from .snr import *

def get_SNR_alphabeta_image(vw, alpha_list=[[0.1]], BetaoverH_list=[[100]],
                            Tstar=180,
                            gstar=100,
                            adiabaticRatio=4.0/3.0,
                            label_list=None,
                            title_list=None,
                            MissionProfile=0,
                            usetex=False,
                            hugeAlpha=False):
    """Produce the AlphaBeta plot

    Parameters
    ----------
    vw : float
        Wall velocity
    alpha_list : list[float]
        List of phase transition strengths
    BetaoverH_list : list[float]
        List of inverse phase transition durations
    Tstar : float
        Transition temperature (default to 180)
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
        svg plot of AlphaBeta
    """

    red = np.array([1,0,0])
    darkgreen = np.array([0,0.7,0])
    color_tuple = tuple([tuple(0.5*(np.tanh((0.5-f)*10)+1)*red
                               + f**0.5*darkgreen)  for f in (np.arange(6)*0.2)])

    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')

    if hugeAlpha:
        ubarfmax = 0.866
    else:
        ubarfmax = 0.6

    tshHn, snr, log10HnRstar, log10Ubarf = get_SNRcurve(Tstar, gstar, MissionProfile, ubarfmax)
    log10BetaOverH = np.log10(rstar_to_beta(np.power(10.0,
                                                     log10HnRstar),
                                                     vw))
    log10alpha = np.log10(ubarf_to_alpha(vw, np.power(10.0, log10Ubarf), adiabaticRatio))

    levels = np.array([1,5,10,20,50,100])
    levels_tsh = np.array([0.001,0.01,0.1,1,10,100])
    levels_tsh_hugeAlpha = np.array([0.0000001,0.000001,0.00001,0.0001])
    
    # Where to put contour label, based on y-coordinate and contour value
    def find_place(snr, wantedy, wantedcontour):
        nearesty = (np.abs(log10BetaOverH-wantedy)).argmin()
        nearestx = (np.abs(snr[nearesty,:]-wantedcontour)).argmin()

        return (log10alpha[nearestx],wantedy)

    # location of contour labels
    locs = [find_place(snr, 2, wantedcontour) for wantedcontour in levels]
    locs_tsh = [(int(math.ceil(min(log10alpha))) + 0.2,x) \
                for x in range(int(math.ceil(min(log10BetaOverH))),
                               int(math.floor(max(log10BetaOverH))+1))]

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)
    
    CS = ax.contour(log10alpha, log10BetaOverH, snr, levels, linewidths=1,
                    colors=color_tuple,
                     extent=(log10alpha[0], log10alpha[-1],
                             log10BetaOverH[0], log10BetaOverH[-1]))
    CStsh = ax.contour(log10alpha, log10BetaOverH,
                       tshHn, levels_tsh, linewidths=1,
                       linestyles='dashed', colors='k',
                       extent=(log10alpha[0], log10alpha[-1],
                               log10BetaOverH[0], log10BetaOverH[-1]))

    if hugeAlpha:
        CStsh_hugeAlpha = ax.contour(log10alpha, log10BetaOverH,
                           tshHn, levels_tsh_hugeAlpha, linewidths=1,
                           linestyles='dashed', colors='k',
                           extent=(log10alpha[0], log10alpha[-1],
                                   log10BetaOverH[0], log10BetaOverH[-1]))

    CSturb = ax.contourf(log10alpha, log10BetaOverH, tshHn, [1, 1000], colors=('gray'), alpha=0.5,
                          extent=(log10alpha[0], log10alpha[-1],
                                  log10BetaOverH[0], log10BetaOverH[-1]))

    ax.clabel(CS, inline=1, fontsize=8, fmt="%.0f", manual=locs)
    ax.clabel(CStsh, inline=1, fontsize=8, fmt="%g", manual=locs_tsh)
    # plt.title(r'SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs')
    # plt.xlabel(r'$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $',fontsize=16)
    ax.set_ylabel(r'$ \beta/H_* $', fontsize=14)
    ax.set_xlabel(r'$\alpha$', fontsize=14)

    ax.set_xlim(min(log10alpha),max(log10alpha))
    ax.set_ylim(min(log10BetaOverH),max(log10BetaOverH))

    for i, (BetaoverH_set, alpha_set) in enumerate(zip(BetaoverH_list,
                                                       alpha_list)):
        BetaOverH_log_set = [math.log10(BetaoverH) \
                         for BetaoverH in BetaoverH_set]

        alpha_log_set = [math.log10(alpha) for alpha in alpha_set]
        benchmarks = ax.plot(alpha_log_set, BetaOverH_log_set, '.')

        if label_list:
            label_set = label_list[i]
            for x,y,label in zip(alpha_log_set, BetaOverH_log_set, label_set):
                ax.annotate(label, xy=(x,y), xycoords='data', xytext=(5,0),
                        textcoords='offset points')

    if title_list:
        legends = title_list
        leg = ax.legend(legends, loc='lower left', framealpha=0.9)

    # Old attempts at getting the ticks in the right place
    # xtickpos = [min(log10alpha)] \
    #     + list(range(int(math.ceil(min(log10alpha))),
    #                  int(math.floor(max(log10alpha))+1))) \
    #     + [max(log10alpha)]
    # xticklabels = [r'$10^{%.2g}$' % min(log10alpha)] \
    #     + [r'$10^{%d}$' % ind
    #        for ind in list(range(int(math.ceil(min(log10alpha))),
    #                              int(math.floor(max(log10alpha))+1)))] \
    #     + [r'$10^{%.2g}$' % max(log10alpha)]

    # xtickpos = [-2, -1, 0, 1]
    # xticklabels = [ r'$10^{-2}$', r'$10^{-1}$', r'$10^{0}$', r'$10^{1}$']
    # ytickpos = [min(log10BetaOverH)] \
    #     + list(range(int(math.ceil(min(log10BetaOverH))),
    #               int(math.floor(max(log10BetaOverH))+1))) \
    #     + [max(log10BetaOverH)]
    # yticklabels = [r'$10^{%.2g}$' % min(log10BetaOverH)] \
    #     + [r'$10^{%d}$' % ind
    #        for ind in list(range(int(math.ceil(min(log10BetaOverH))),
    #                              int(math.floor(max(log10BetaOverH))+1)))] \
    #     + [r'$10^{%.2g}$' % max(log10BetaOverH)]

    # ytickpos = [0, 1, 2, 3, 4]
    # yticklabels = [r'$10^{0}$', r'$10^{1}$', r'$10^{2}$', r'$10^{3}$', r'$10^{4}$']

    # # Remove if too close together
    # if xtickpos[1]/xtickpos[0] < 3:
    #     xtickpos = xtickpos[1:]
    #     xticklabels = xticklabels[1:]

    xtickpos = list(range(int(math.ceil(min(log10alpha))),
                     int(math.floor(max(log10alpha))+1)))
    xticklabels = [r'$10^{%d}$' % ind
           for ind in list(range(int(math.ceil(min(log10alpha))),
                                 int(math.floor(max(log10alpha))+1)))]

    ytickpos = list(range(int(math.ceil(min(log10BetaOverH))),
                     int(math.floor(max(log10BetaOverH))+1)))
    yticklabels = [r'$10^{%d}$' % ind
                   for ind in list(
                           range(int(math.ceil(min(log10BetaOverH))),
                                 int(math.floor(max(log10BetaOverH))+1)))]    

    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())

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
    fig.savefig(sio, format="svg") # , bbox_inches='tight')
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
        b = get_SNR_alphabeta_image(vw, [alpha], [betaoverh], T, g, MissionProfile=MissionProfile)
        print(b.read().decode("utf-8"))
    else:
        sys.stderr.write('Usage: %s <vw> <alpha> <Beta/H> <T*> <g*> <MissionProfile>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n\n')
        sys.stderr.write('Available sensitivity curves:\n')
        for number,label in enumerate(available_labels):
            sys.stderr.write('%d: %s\n' % (number, label))