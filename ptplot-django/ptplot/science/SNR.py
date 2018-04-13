

#!/usr/bin/env python3

# ExampleUseSNR1.py v 0.3 (Antoine Petiteau 15/05/2015)
# \-> Broken power law (Mark Hindmarsh Sep 2015)
#   \-> SNR plots for PTPlot (David Weir Feb 2018)


import math
import matplotlib
matplotlib.use('Agg')
# import matplotlib.pyplot as plt
import numpy as np
import os.path
import io
import sys

from django.conf import settings


from .espinosa import kappav, ubarf

BASE_DIR = getattr(settings, "BASE_DIR", None)
root = os.path.join(BASE_DIR, 'ptplot', 'science')

def get_SNR_image(Tstar=100, vw=0.95, alpha=0.1, HoverBeta=100, usetex=False):
    config = 'L6A2M5N2P2D28'

    red = np.array([1,0,0])
    darkgreen = np.array([0,0.7,0])
    color_tuple = tuple([tuple(0.5*(np.tanh((0.5-f)*10)+1)*red
                               + f**0.5*darkgreen)  for f in (np.arange(6)*0.2)])

    # print color_tuple

    ## Values of log10 Ubarf to scan
    log10Ubarf = np.arange(-2,0.025,0.025)
    #log10Ubarf = np.arange(-2,0.025,0.2)

    ## Values of log10 HnRstar to scan
    log10HnRstar = np.arange(-4,0.025,0.025)
    #log10HnRstar = np.arange(-4,0.025,0.2)

    xtickpos = [-2, -1, 0]
    xticklabels = [ r'$10^{-2}$', r'$10^{-1}$', r'$1$']

    ytickpos = [-4, -3, -2, -1, 0]
    yticklabels = [r'$10^{-4}$', r'$10^{-3}$', r'$10^{-2}$', r'$10^{-1}$', r'$1$']

    # Model parameters
    Omtil = 1.2e-2 # GW efficiency parameter
    zp = 10        # Peak kR*

#    Tn = 100.      # Nucleation temp in GeV
    hstar = 100    # d.o.f.
    AdInd = 4./3.  # Adiabatic index

    Tn = Tstar
    
    # Hubble rate redshifted to now
    Hn0 = 16.5e-6 * (Tn/100) * (hstar/100)**(1./6) # Hz

    # GW dilution factor now
    Fgw0 = 2 * 1.64e-5 * (Tn/100) * (hstar/100)**(1./6)


    
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    
    
    precomputed_filehandle = open(os.path.join(root, 'snr_' + config + '_precomputed.npz'), 'rb')
    npz_result = np.load(precomputed_filehandle)

    
    tshHn = npz_result['tshHn']
    snr = npz_result['snr']
    log10HnRstar = npz_result['log10HnRstar']
    log10Ubarf = npz_result['log10Ubarf']

    levels = np.array([1,5,10,20,50,100])
    levels_tsh = np.array([0.01,0.1,1,10])


    # Where to put contour label, based on y-coordinate and contour value
    def find_place(snr, wantedy, wantedcontour):
        nearesty = (np.abs(log10HnRstar-wantedy)).argmin()
        nearestx = (np.abs(snr[nearesty,:]-wantedcontour)).argmin()


        # print (wantedx,log10Ubarf[nearesty])
        return (log10Ubarf[nearestx],wantedy)

    
    # location of contour labels
    locs = [find_place(snr, -3.2, wantedcontour) for wantedcontour in levels]
    locs_tsh = [(-1.8,-3.5), (-1.8,-2.5), (-1.8,-1.8), (-1.8,-0.5)]

    fig = matplotlib.figure.Figure()
    ax = fig.add_subplot(111)
    
    CS = ax.contour(snr, levels, linewidths=1,colors=color_tuple,
                     extent=(log10Ubarf[0], log10Ubarf[-1], log10HnRstar[0], log10HnRstar[-1]))
    CStsh = ax.contour(tshHn, levels_tsh, linewidths=1, linestyles='dashed', colors='k',
                        extent=(log10Ubarf[0], log10Ubarf[-1], log10HnRstar[0], log10HnRstar[-1]))

    legends = []


    CSturb = ax.contourf(tshHn, [1,100], colors=('gray'), alpha=0.5,
                          extent=(log10Ubarf[0], log10Ubarf[-1], log10HnRstar[0], log10HnRstar[-1]))

    # proxy
#    for pc in CSturb.collections:
#        matplotlib.patches.Rectangle((0,0),1,1,fc = pc.get_facecolor()[0])



    
    ax.clabel(CS, inline=1, fontsize=8, fmt="%.0f", manual=locs)
    ax.clabel(CStsh, inline=1, fontsize=8, fmt="%g",manual=locs_tsh)
    #    plt.title(r'SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs')
    #    plt.xlabel(r'$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $',fontsize=16)
    ax.set_ylabel(r'$H_{\rm n} R_* $',fontsize=14)
    ax.set_xlabel(r'$\overline{U}_{\rm f}$',fontsize=14)
    #    plt.grid()


    #    alpha_list = [0.09,0.12,0.17,0.20]
    #    beta_list = [47.35,29.96,12.54,6.42]
    #    vw_list = [0.95,0.95,0.95,0.95]

    alpha_list = [alpha]
    beta_list = [1.0/HoverBeta]
    vw_list = [vw]
    

    Rstar_list = [math.log(math.pow(8.0*math.pi,1.0/3.0)*vel/beta) \
                  for vel, beta in zip(vw_list, beta_list)]


    ubarf_list = [math.log(ubarf(vw, alpha)) \
                  for vw, alpha in zip(vw_list, alpha_list)]

    sys.stderr.write('ubarf is %g, vw %g, alpha %g\n' % (math.exp(ubarf_list[0]), vw, alpha))
    
    singlet = ax.plot(ubarf_list, Rstar_list, '-o')

    legends.append(r'Your point')

    leg = ax.legend(legends, loc='lower left', framealpha=0.9)
    
    #    leg.get_frame().set_alpha(0.9)

#    plt.annotate('A', xy=(ubarf_list[0], Rstar_list[0]), xycoords='data',
#                 xytext=(5, -5), textcoords='offset points')

#    plt.annotate('B', xy=(ubarf_list[1], Rstar_list[1]), xycoords='data',
#                 xytext=(5, -5), textcoords='offset points')

#    plt.annotate('C', xy=(ubarf_list[2], Rstar_list[2]), xycoords='data',
#                 xytext=(5, -10), textcoords='offset points')

#    plt.annotate('D', xy=(ubarf_list[3], Rstar_list[3]), xycoords='data',
#                 xytext=(5, 0), textcoords='offset points')


    #    plt.arrow(-2.9,-1.8, -0.5, 0.2,
    #              head_width=0.05, head_length=0.1, fc='k', ec='k')

    #    plt.arrow(-2.6, -0.75, 0.3, 0.3,
    #              head_width=0.05, head_length=0.1, fc='k', ec='k')

    #    plt.annotate(r'\textbf{More turbulent}',
    #                 xy=(-3.77,-1.85), xycoords='data')
    #    plt.annotate(r'\textbf{Easier to detect}',
    #                 xy=(-2.25,-0.32), xycoords='data')

    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)

    
    sio = io.BytesIO()

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    canvas = FigureCanvas(fig)
    
    fig.savefig(sio, format="svg")

    sio.seek(0)
    

    
    # figfilename = "/tmp/SNR-Ubarf-Rstar-" + config + "-contour-cgi.png"
    # plt.savefig(figfilename, format="png")


    
    return sio
    
    
    #print "Saving figfile " + figfilename
    
    
    #plt.show()



if __name__ == '__main__':
    get_SNR_image()

