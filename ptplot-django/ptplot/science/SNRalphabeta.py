#!/usr/bin/env python3

# ExampleUseSNR1.py v 0.3 (Antoine Petiteau 15/05/2015)
# \-> Broken power law (Mark Hindmarsh Sep 2015)
#   \-> SNR plots for PTPlot (David Weir Feb 2018)


import math
import matplotlib
matplotlib.use('Agg')
import numpy as np
import os.path
import io
import sys

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:
    
    import matplotlib.figure

    from espinosa import kappav, ubarf

    root = './'

else:

    from .espinosa import kappav, ubarf

    from django.conf import settings
    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')

    
def hn_rstar_to_beta(hn_rstar, vw):
    return math.pow(8.0*math.pi,1.0/3.0)*vw/hn_rstar


def get_SNR_alphabeta_image(vw_list=[0.5], alpha_list=[0.1], HoverBeta_list=[0.01],
                  SNRcurve='Sens_L6A2M5N2P2D28_Tn_100.0_gstar_100.0_precomputed.npz',
                  label_list=None,
                  title=None,
                  usetex=False):

    red = np.array([1,0,0])
    darkgreen = np.array([0,0.7,0])
    color_tuple = tuple([tuple(0.5*(np.tanh((0.5-f)*10)+1)*red
                               + f**0.5*darkgreen)  for f in (np.arange(6)*0.2)])


    xtickpos = [-2, -1, 0]
    xticklabels = [ r'$10^{-2}$', r'$10^{-1}$', r'$1$']

    ytickpos = [0, 1, 2, 3, 4]
    yticklabels = [r'$10^{0}$', r'$10^{1}$', r'$10^{2}$', r'$10^{3}$', r'$10^{4}$']


    
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    
    
    precomputed_filehandle = open(os.path.join(root, SNRcurve), 'rb')
    npz_result = np.load(precomputed_filehandle)

    
    tshHn = npz_result['tshHn']
    snr = npz_result['snr']
    log10HnRstar = npz_result['log10HnRstar']

    log10BetaOverH = np.log10(hn_rstar_to_beta(np.power(10.0, log10HnRstar),vw_list[0]))

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
    
    CS = ax.contour(snr, levels, linewidths=1,
                    colors=color_tuple,
                     extent=(log10Ubarf[0], log10Ubarf[-1],
                             log10BetaOverH[0], log10BetaOverH[-1]))
    CStsh = ax.contour(tshHn, levels_tsh, linewidths=1,
                       linestyles='dashed', colors='k',
                       extent=(log10Ubarf[0], log10Ubarf[-1],
                               log10BetaOverH[0], log10BetaOverH[-1]))

    legends = []

    sys.stderr.write(str(log10Ubarf[0]) + ' '  + str(log10Ubarf[-1]) + ' '+ \
           str(log10BetaOverH[0]) + ' ' + str(log10BetaOverH[-1]) + '\n')

    CSturb = ax.contourf(tshHn, [1, 100], colors=('gray'), alpha=0.5,
                          extent=(log10Ubarf[0], log10Ubarf[-1],
                                  log10BetaOverH[0], log10BetaOverH[-1]))

    # proxy
#    for pc in CSturb.collections:
#        matplotlib.patches.Rectangle((0,0),1,1,fc = pc.get_facecolor()[0])



    
    ax.clabel(CS, inline=1, fontsize=8, fmt="%.0f", manual=locs)
    ax.clabel(CStsh, inline=1, fontsize=8, fmt="%g", manual=locs_tsh)
    #    plt.title(r'SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs')
    #    plt.xlabel(r'$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $',fontsize=16)
    ax.set_ylabel(r'$ \beta/H_* $', fontsize=14)
    ax.set_xlabel(r'$\overline{U}_{\rm f}$', fontsize=14)

    #    plt.grid()

    BetaOverH_list = [math.log10(1.0/HoverBeta) \
                      for HoverBeta in HoverBeta_list]


    ubarf_list = [math.log10(ubarf(vw, alpha)) \
                  for vw, alpha in zip(vw_list, alpha_list)]

    benchmarks = ax.plot(ubarf_list, BetaOverH_list, '-o')

    if title:
        legends.append(title)

    if label_list:
        for x,y,label in zip(ubarf_list, BetaOverH_list, label_list):
            ax.annotate(label, xy=(x,y), xycoords='data', xytext=(5,0),
                        textcoords='offset points')
    
    leg = ax.legend(legends, loc='lower left', framealpha=0.9)

    #    leg.get_frame().set_alpha(0.9)
    
    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)

    # position bottom right
    fig.text(0.95, 0.05, 'LISACosWG',
             fontsize=50, color='gray',
             ha='right', va='bottom', alpha=0.5)
    
    
    sio = io.BytesIO()

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    canvas = FigureCanvas(fig)
    
    fig.savefig(sio, format="svg")

    sio.seek(0)
        
    return sio
    

if __name__ == '__main__':
    if len(sys.argv) == 5:
        vw = float(sys.argv[1])
        alpha = float(sys.argv[2])
        hoverbeta = float(sys.argv[3])
        snrcurve = sys.argv[4]
        b = get_SNR_alphabeta_image([vw], [alpha], [hoverbeta], snrcurve)
        print(b.read().decode("utf-8"))
    else:
        sys.stderr.write('Usage: %s <vw> <alpha> <H/Beta> <SNR file>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n')
        
