#!/usr/bin/env python

# ExampleUseSNR1.py v 0.3 (Antoine Petiteau 15/05/2015)
# \-> Broken power law (Mark Hindmarsh Sep 2015)
#   \-> SNR plots for PTPlot (David Weir Feb 2018)

import math
import numpy as np
import matplotlib.pyplot as plt

config = 'L6A2M5N2P2D28'

red = np.array([1,0,0])
darkgreen = np.array([0,0.7,0])
color_tuple = tuple([tuple(0.5*(np.tanh((0.5-f)*10)+1)*red
                           + f**0.5*darkgreen)  for f in (np.arange(6)*0.2)])

print color_tuple

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

Tn = 100.      # Nucleation temp in GeV
hstar = 100    # d.o.f.
AdInd = 4./3.  # Adiabatic index

# Hubble rate redshifted to now
Hn0 = 16.5e-6 * (Tn/100) * (hstar/100)**(1./6) # Hz

# GW dilution factor now
Fgw0 = 2 * 1.64e-5 * (Tn/100) * (hstar/100)**(1./6)


plt.rc('text', usetex=True)
plt.rc('font', family='serif')

npz_result = np.load('snr_' + config + '_precomputed.npz')
    
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
    
CS = plt.contour(snr, levels, linewidths=1,colors=color_tuple,
                     extent=(log10Ubarf[0], log10Ubarf[-1], log10HnRstar[0], log10HnRstar[-1]))
CStsh = plt.contour(tshHn, levels_tsh, linewidths=1, linestyles='dashed', colors='k',
                     extent=(log10Ubarf[0], log10Ubarf[-1], log10HnRstar[0], log10HnRstar[-1]))

legends = []
collections = []
    
    
CSturb = plt.contourf(tshHn, [1,100], colors=('gray'), alpha=0.5,
                      extent=(log10Ubarf[0], log10Ubarf[-1], log10HnRstar[0], log10HnRstar[-1]))

legends.append(r'Turbulence never develops')
collections = collections + CSturb.collections
    
plt.clabel(CS, inline=1, fontsize=10, fmt="%.0f", manual=locs)
plt.clabel(CStsh, inline=1, fontsize=10, fmt="%g",manual=locs_tsh)
#    plt.title(r'SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs')
#    plt.xlabel(r'$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $',fontsize=16)
plt.ylabel(r'$H_{\rm n} R_* $',fontsize=16)
plt.xlabel(r'$\bar{U}_{\rm f}$',fontsize=16)
#    plt.grid()


alpha_list = [0.09,0.12,0.17,0.20]
beta_list = [47.35,29.96,12.54,6.42]
vw_list = [0.95,0.95,0.95,0.95]

from espinosa import kappav, ubarf
    
Rstar_list = [math.log(math.pow(8.0*math.pi,1.0/3.0)*vel/beta) \
              for vel, beta in zip(vw_list, beta_list)]

        
ubarf_list = [math.log(ubarf(vw, alpha)) \
              for vw, alpha in zip(vw_list, alpha_list)]

#    print kappav(0.92,0.0046)
    
singlet = plt.plot(ubarf_list, Rstar_list, '-o')

legends.append('Singlet benchmark points')
    
proxy = [plt.Rectangle((0,0),1,1,fc = pc.get_facecolor()[0])
         for pc in collections] + singlet

leg = plt.legend(proxy, legends, loc='lower left', framealpha=0.9)
#    leg.get_frame().set_alpha(0.9)

plt.annotate('A', xy=(ubarf_list[0], Rstar_list[0]), xycoords='data',
             xytext=(5, -5), textcoords='offset points')

plt.annotate('B', xy=(ubarf_list[1], Rstar_list[1]), xycoords='data',
             xytext=(5, -5), textcoords='offset points')

plt.annotate('C', xy=(ubarf_list[2], Rstar_list[2]), xycoords='data',
             xytext=(5, -10), textcoords='offset points')

plt.annotate('D', xy=(ubarf_list[3], Rstar_list[3]), xycoords='data',
             xytext=(5, 0), textcoords='offset points')


#    plt.arrow(-2.9,-1.8, -0.5, 0.2,
#              head_width=0.05, head_length=0.1, fc='k', ec='k')

#    plt.arrow(-2.6, -0.75, 0.3, 0.3,
#              head_width=0.05, head_length=0.1, fc='k', ec='k')

#    plt.annotate(r'\textbf{More turbulent}',
#                 xy=(-3.77,-1.85), xycoords='data')
#    plt.annotate(r'\textbf{Easier to detect}',
#                 xy=(-2.25,-0.32), xycoords='data')
    
plt.xticks(xtickpos, xticklabels)
plt.yticks(ytickpos, yticklabels)

figfilename = "SNR-Ubarf-Rstar-" + config + "-contour.pdf"
print "Saving figfile " + figfilename
plt.savefig(figfilename)
    
#plt.show()
plt.close()





