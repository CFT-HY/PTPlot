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
import scipy.interpolate
import multiprocessing

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:
    
    import matplotlib.figure

    from espinosa import kappav, ubarf, ubarf_to_alpha
    from curves import PowerSpectrum
    
    root = './'

    
    # eLISATools from Antoine
    from eLISATools import *
    
else:

    from .espinosa import kappav, ubarf, ubarf_to_alpha
    from curves import PowerSpectrum
    
    from django.conf import settings
    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')


    # eLISATools from Antoine
    from .eLISATools import *    
    
def hn_rstar_to_beta(hn_rstar, vw):
    return math.pow(8.0*math.pi,1.0/3.0)*vw/hn_rstar


def get_SNRcurve(Tn, gstar):
    duration = 5*yr
    
    ## Values of log10 Ubarf to scan
    log10Ubarf = np.arange(-2,0.025,0.025)

    ## Values of log10 HnRstar to scan
    log10HnRstar = np.arange(-4,0.025,0.025)

    # Model parameters
    Omtil = 1.2e-1 # GW efficiency parameter
    zp = 10        # Peak kR*

#    Tn = 100.      # Nucleation temp in GeV
#    gstar = 100    # d.o.f.
    AdInd = 4./3.  # Adiabatic index

    # Hubble rate redshifted to now - equation 42
    Hn0 = 16.5e-6 * (Tn/100) * (gstar/100)**(1./6) # Hz


    sensitivity_curve='ScienceRequirementsLite.txt'
    fS, OmEff = LoadFile(sensitivity_curve, 2)
    
    ### Computation of SNR map as a function of GW Amplitude and Peak frequency
    snr = np.zeros(( len(log10HnRstar), len(log10Ubarf) ))

    tshHn = np.zeros((len(log10HnRstar), len(log10Ubarf)  ))

    for i in range(len(log10HnRstar)):
        for j in range(len(log10Ubarf)):
            Ubarf = 10.**log10Ubarf[j]
            HnRstar = 10.**log10HnRstar[i]
            # Peak amplitude and peak frequency, equation 45
            OmMax = 0.68 * AdInd**2 * Ubarf**4 * Omtil * HnRstar
            # GW dilution factor now - equation 44
            Fgw0 = 3.57e-5* (100.0/gstar)**(1./3)
            
            # equation 43, peak frequency
            fp = 26.0e-6*(1.0/HnRstar)*(zp/10)*(Tn/100)* (gstar/100)**(1.0/6.0)

            s = fS/fp # frequency scaled to peak
            OmGW0 = Fgw0*PowerSpectrum().Ssw(s, OmMax)
            snr[i,j], frange = StockBkg_ComputeSNR(fS, OmEff, fS, OmGW0, duration, 1.e-6, 1.)
            tshHn[i,j] = HnRstar/Ubarf
        #print('Rstar number', i, "/", len(log10HnRstar))

    return tshHn, snr, log10HnRstar, log10Ubarf

def get_SNR_alphabeta_image(vw_list=[0.5], alpha_list=[0.1], HoverBeta_list=[0.01],
                            Tn=100,
                            gstar=100,
                            label_list=None,
                            title=None,
                            usetex=False):


    
    red = np.array([1,0,0])
    darkgreen = np.array([0,0.7,0])
    color_tuple = tuple([tuple(0.5*(np.tanh((0.5-f)*10)+1)*red
                               + f**0.5*darkgreen)  for f in (np.arange(6)*0.2)])




    
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    
    
    
    tshHn, snr, log10HnRstar, log10Ubarf = get_SNRcurve(Tn, gstar)
    
    log10BetaOverH = np.log10(hn_rstar_to_beta(np.power(10.0, log10HnRstar),vw_list[0]))
    log10alpha = np.log10(ubarf_to_alpha(vw_list[0], np.power(10.0, log10Ubarf)))

    a = ubarf_to_alpha(vw_list[0], np.power(10.0, log10Ubarf))
    b = np.power(10.0, log10Ubarf)
    
    levels = np.array([1,5,10,20,50,100])
    levels_tsh = np.array([0.001,0.01,0.1,1,10,100])

    
    
    # Where to put contour label, based on y-coordinate and contour value
    def find_place(snr, wantedy, wantedcontour):
        nearesty = (np.abs(log10BetaOverH-wantedy)).argmin()
        nearestx = (np.abs(snr[nearesty,:]-wantedcontour)).argmin()

        return (log10alpha[nearestx],wantedy)

    
    # location of contour labels
    locs = [find_place(snr, 2, wantedcontour) for wantedcontour in levels]

    locs_tsh = [(-1.5,1), (-1.5,2), (-1.5,3), (-1.5,4)]

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

    CSturb = ax.contourf(log10alpha, log10BetaOverH, tshHn, [1, 100], colors=('gray'), alpha=0.5,
                          extent=(log10alpha[0], log10alpha[-1],
                                  log10BetaOverH[0], log10BetaOverH[-1]))

    # proxy
#    for pc in CSturb.collections:
#        matplotlib.patches.Rectangle((0,0),1,1,fc = pc.get_facecolor()[0])



    
    ax.clabel(CS, inline=1, fontsize=8, fmt="%.0f", manual=locs)
    ax.clabel(CStsh, inline=1, fontsize=8, fmt="%g", manual=locs_tsh)
    #    plt.title(r'SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs')
    #    plt.xlabel(r'$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $',fontsize=16)
    ax.set_ylabel(r'$ \beta/H_* $', fontsize=14)
    ax.set_xlabel(r'$\alpha$', fontsize=14)

    #    plt.grid()

    BetaOverH_list = [math.log10(1.0/HoverBeta) \
                      for HoverBeta in HoverBeta_list]


#    ubarf_list = [math.log10(ubarf(vw, alpha)) \
#                  for vw, alpha in zip(vw_list, alpha_list)]


    alpha_log_list = [math.log10(alpha) for alpha in alpha_list]
    
#    benchmarks = ax.plot(alpha_log_list, BetaOverH_list, '.')
    benchmarks = ax.plot(alpha_log_list, BetaOverH_list, '-o')

    if label_list:
        for x,y,label in zip(alpha_log_list, BetaOverH_list, label_list):
            ax.annotate(label, xy=(x,y), xycoords='data', xytext=(5,0),
                        textcoords='offset points')


    if title:
        legends = []
        
        legends.append(title)
            
        leg = ax.legend(legends, loc='lower left', framealpha=0.9)

        #    leg.get_frame().set_alpha(0.9)

    xtickpos = [min(log10alpha)] \
        + list(range(int(round(min(log10alpha))),
                     int(round(max(log10alpha))+1))) \
        + [max(log10alpha)]
    xticklabels = [r'$10^{%.2g}$' % min(log10alpha)] \
        + [r'$10^{%d}$' % ind
           for ind in list(range(int(round(min(log10alpha))),
                                 int(round(max(log10alpha))+1)))] \
        + [r'$10^{%.2g}$' % max(log10alpha)]
    
#    xtickpos = [-2, -1, 0, 1]
#    xticklabels = [ r'$10^{-2}$', r'$10^{-1}$', r'$10^{0}$', r'$10^{1}$']

    ytickpos = [min(log10BetaOverH)] \
        + list(range(int(math.ceil(min(log10BetaOverH))),
                     int(round(max(log10BetaOverH))+1))) \
        + [max(log10BetaOverH)]
    yticklabels = [r'$10^{%.2g}$' % min(log10BetaOverH)] \
        + [r'$10^{%d}$' % ind
           for ind in list(range(int(math.ceil(min(log10BetaOverH))),
                                 int(round(max(log10BetaOverH))+1)))] \
        + [r'$10^{%.2g}$' % max(log10BetaOverH)]


#    ytickpos = [0, 1, 2, 3, 4]
#    yticklabels = [r'$10^{0}$', r'$10^{1}$', r'$10^{2}$', r'$10^{3}$', r'$10^{4}$']
        
    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)

    # position bottom right
    fig.text(0.95, 0.05, 'LISACosWG',
             fontsize=50, color='gray',
             ha='right', va='bottom', alpha=0.4)
    
    
    sio = io.BytesIO()

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    canvas = FigureCanvas(fig)

#    fig.savefig("snralphabeta.png", format="png", dpi=400)
    fig.savefig(sio, format="svg")

    sio.seek(0)
        
    return sio
    


def worker(queue, vw_list=[0.5], alpha_list=[0.1], HoverBeta_list=[0.01],
           Tn=100,
           gstar=100,
           label_list=None,
           title=None,
           usetex=False):
    queue.put(get_SNR_alphabeta_image(vw_list, alpha_list, HoverBeta_list,
                                      Tn, gstar, label_list, title, usetex))

def get_SNR_alphabeta_image_threaded(vw_list=[0.5], alpha_list=[0.1], HoverBeta_list=[0.01],
                                     Tn=100,
                                     gstar=100,
                                     label_list=None,
                                     title=None,
                                     usetex=False):

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker, args=(q, vw_list, alpha_list, HoverBeta_list,
                                                     Tn, gstar, label_list, title, usetex))
    p.start()
    return_res = q.get()
    p.join()
    return return_res
    
    
if __name__ == '__main__':
    if len(sys.argv) == 6:
        vw = float(sys.argv[1])
        alpha = float(sys.argv[2])
        hoverbeta = float(sys.argv[3])
        T = float(sys.argv[4])
        g = float(sys.argv[5])
        b = get_SNR_alphabeta_image([vw], [alpha], [hoverbeta], T, g)
        print(b.read().decode("utf-8"))
   
    else:
        sys.stderr.write('Usage: %s <vw> <alpha> <H/Beta> <T*> <g*>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n')
        
    # Tn, alpha, betaoverh = np.loadtxt('foo', usecols=[0,1,2], delimiter=',', unpack=True)
    # vw = [0.1]*len(Tn)
    # get_SNR_alphabeta_image(vw, alpha, 1.0/betaoverh, "ScienceRequirements_Tn_100.0_gstar_100.0_precomputed.npz")
