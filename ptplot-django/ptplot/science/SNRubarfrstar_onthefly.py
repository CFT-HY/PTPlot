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
import multiprocessing
import time

# Fix some things if running standalone
if __name__ == "__main__" and __package__ is None:

    import matplotlib.figure

    from espinosa import kappav, ubarf
    from SNR_precompute import get_SNRcurve                                      
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
                  label_list=None,
                  title_list=None,
                  MissionProfile=0,
                  usetex=False):


    
    red = np.array([1,0,0])
    darkgreen = np.array([0,0.7,0])
    color_tuple = tuple([tuple(0.5*(np.tanh((0.5-f)*10)+1)*red
                               + f**0.5*darkgreen)  for f in (np.arange(6)*0.2)])
    
    # matplotlib.rc('text', usetex=usetex)
    matplotlib.rc('font', family='serif')
    matplotlib.rc('mathtext', fontset='dejavuserif')
    

    tshHn, snr, log10HnRstar, log10Ubarf = get_SNRcurve(Tstar, gstar, MissionProfile)
    
    levels = np.array([1,5,10,20,50,100])
    levels_tsh = np.array([0.001,0.01,0.1,1,10,100])


    # Where to put contour label, based on y-coordinate and contour value
    def find_place(snr, wantedy, wantedcontour):
        nearesty = (np.abs(log10HnRstar-wantedy)).argmin()
        nearestx = (np.abs(snr[nearesty,:]-wantedcontour)).argmin()


        # print (wantedx,log10Ubarf[nearesty])
        return (log10Ubarf[nearestx],wantedy)

    
    # location of contour labels
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

#     CSturb = ax.contourf(log10Ubarf, log10HnRstar, tshHn, [0.00001, 1], colors=('gray'), alpha=0.3,
    CSturb = ax.contourf(log10Ubarf, log10HnRstar, tshHn, [1, 100], colors=('gray'), alpha=0.5,
                          extent=(log10Ubarf[0], log10Ubarf[-1],
                                  log10HnRstar[0], log10HnRstar[-1]))

    # proxy
#    for pc in CSturb.collections:
#        matplotlib.patches.Rectangle((0,0),1,1,fc = pc.get_facecolor()[0])



    
    ax.clabel(CS, inline=1, fontsize=8, fmt="%.0f", manual=locs)
    ax.clabel(CStsh, inline=1, fontsize=8, fmt="%g", manual=locs_tsh)
    #    plt.title(r'SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs')
    #    plt.xlabel(r'$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $',fontsize=16)
    ax.set_ylabel(r'$H_{\rm n} R_* $', fontsize=14)
    ax.set_xlabel(r'$\overline{U}_{\rm f}$', fontsize=14)
    ax.set_xlim(min(log10Ubarf),max(log10Ubarf))
    ax.set_ylim(min(log10HnRstar),max(log10HnRstar))
    #    plt.grid()


    for i, (vw_set, BetaoverH_set, alpha_set) in enumerate(zip(vw_list, BetaoverH_list,
                                                             alpha_list)):

        # H_n*R_* = (8*pi)^{1/3}*vw/BetaoverH
        Rstar_set = [math.log10(math.pow(8.0*math.pi,1.0/3.0)*vw/BetaoverH) \
                      for vw, BetaoverH in zip(vw_set, BetaoverH_set)]


        ubarf_set = [math.log10(ubarf(vw, alpha)) \
                      for vw, alpha in zip(vw_set, alpha_set)]

        #    benchmarks = ax.plot(ubarf_list, Rstar_list, '.')
        benchmarks = ax.plot(ubarf_set, Rstar_set, '.')



        if label_list:
            label_set = label_list[i]
            for x,y,label in zip(ubarf_set, Rstar_set, label_set):
                ax.annotate(label, xy=(x,y), xycoords='data', xytext=(5,0),
                            textcoords='offset points')

    if title_list:
        legends = title_list

#        legends = []
#        legends.append(title)
            
        leg = ax.legend(legends, loc='lower left', framealpha=0.9)
#        leg = ax.legend(legends, loc='upper left', framealpha=0.9)
    
        #    leg.get_frame().set_alpha(0.9)


    # xtickpos = [min(log10Ubarf)] \
    #     + list(range(int(round(min(log10Ubarf))),
    #                  int(round(max(log10Ubarf))+1))) \
    #     + [max(log10Ubarf)]
    # xticklabels = [r'$10^{%.2g}$' % min(log10Ubarf)] \
    #     + [r'$10^{%d}$' % ind
    #        for ind in list(range(int(round(min(log10Ubarf))),
    #                              int(round(max(log10Ubarf))+1)))] \
    #     + [r'$10^{%.2g}$' % max(log10Ubarf)]
  
    xtickpos = [-2, -1, 0]
    xticklabels = [ r'$10^{-2}$', r'$10^{-1}$', r'$1$']



    # ytickpos = [min(log10HnRstar)] \
    #     + list(range(int(math.ceil(min(log10HnRstar))),
    #                  int(round(max(log10HnRstar))+1))) \
    #     + [max(log10HnRstar)]
    # yticklabels = [r'$10^{%.2g}$' % min(log10HnRstar)] \
    #     + [r'$10^{%d}$' % ind
    #        for ind in list(range(int(math.ceil(min(log10HnRstar))),
    #                              int(round(max(log10HnRstar))+1)))] \
    #     + [r'$10^{%.2g}$' % max(log10HnRstar)]



    ytickpos = [-4, -3, -2, -1, 0]
    yticklabels = [r'$10^{-4}$', r'$10^{-3}$', r'$10^{-2}$', r'$10^{-1}$', r'$1$']
    
    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)

    # position bottom right
    fig.text(0.95, 0.05, 'LISACosWG',
             fontsize=50, color='gray',
             ha='right', va='bottom', alpha=0.4)

    # position top left
    fig.text(0.13, 0.87, time.asctime(),
             fontsize=8, color='black',
             ha='left', va='top', alpha=1.0)
    
    
    sio = io.BytesIO()

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    canvas = FigureCanvas(fig)

    fig.savefig(sio, format="svg") # , bbox_inches='tight')
    # fig.savefig("snr.png", format="png", dpi=400)

    sio.seek(0)
        
    return sio

def worker(queue, vw_list=[0.5], alpha_list=[0.1], BetaoverH_list=[100],
           Tstar=100,
           gstar=100,
           label_list=None,
           title_list=None,
           MissionProfile=0,
           usetex=False):
    queue.put(get_SNR_image(vw_list, alpha_list, BetaoverH_list,
                            Tstar, gstar,
                            label_list, title_list, MissionProfile, usetex))
    


def get_SNR_image_threaded(vw_list=[0.5], alpha_list=[0.1], BetaoverH_list=[100],
                           Tstar=100,
                           gstar=100,
                           label_list=None,
                           title_list=None,
                           MissionProfile=0,
                           usetex=False):

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker, args=(q, vw_list, alpha_list, BetaoverH_list,
                                                     Tstar, gstar,
                                                     label_list, title_list, MissionProfile, usetex))
    p.start()
    return_res = q.get()
    p.join()
    return return_res


if __name__ == '__main__':
    if len(sys.argv) == 5:
        vw = float(sys.argv[1])
        alpha = float(sys.argv[2])
        betaoverh = float(sys.argv[3])
        snrcurve = sys.argv[4]
        b = get_SNR_image([vw], [alpha], [betaoverh], snrcurve)
        print(b.read().decode("utf-8"))
    else:
        sys.stderr.write('Usage: %s <vw> <alpha> <Beta/H> <SNR file>\n'
                         % sys.argv[0])
        sys.stderr.write('Writes a scalable vector graphic to stdout.\n')

    # Tn, alpha, betaoverh = np.loadtxt('foo', usecols=[0,1,2], delimiter=',', unpack=True)
    # vw = [0.5]*len(Tn)
    # b = get_SNR_image(vw, alpha, 1.0/betaoverh, "ScienceRequirements_Tn_100.0_gstar_100.0_precomputed.npz")
    # b = get_SNR_image([0.95,0.95,0.95,0.95], [0.09,0.12,0.17,0.20], [1.0/47.35, 1.0/29.96, 1.0/12.54, 1.0/6.42], "ScienceRequirements_Tn_100.0_gstar_100.0_precomputed.npz", label_list=['A','B','C','D'], title='Singlet benchmarks')
    # from SNRalphabeta import  get_SNR_alphabeta_image
    # get_SNR_alphabeta_image(vw, alpha, 1.0/betaoverh, "ScienceRequirements_Tn_100.0_gstar_100.0_precomputed.npz")
    
