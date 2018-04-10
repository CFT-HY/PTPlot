#!/usr/bin/env python
# Broken power law (Mark Hindmarsh Sep 2015)
#
# Hacked from
#   ExampleUseSNR1.py v 0.3 (Antoine Petiteau 15/05/2015)

############################## Import modules ##############################
from eLISATools import *
import math

PI = np.pi

############################## Functions ##############################

def GWSpecAcoustic(s, OmMax) :
    """
        Function returning the spectrum corresponding to a causal broken power spectrum
        OmMax * s**3 (7/(4 + 3 * s**2))**(3.5)
        """
    GW = OmMax * s**3 * (7./(4. + 3.*s**2))**3.5
    return GW

############################## Main ##############################

## Info for Loading sensitivity data

sens_file_path = './'

config_list = ['L6A2M5N2P2D28'] #,
#               'L6A5M5N2P2D40']

duration_list = [5*yr] # ,
#                 5*yr]

#label_list = ['28cm-mirror',
#              '40cm-mirror']

label_list = config_list


red = np.array([1,0,0])
darkgreen = np.array([0,0.7,0])
color_tuple = tuple([tuple(0.5*(np.tanh((0.5-f)*10)+1)*red + f**0.5*darkgreen)  for f in (np.arange(6)*0.2)])

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

for config, duration, label in zip(config_list,duration_list,label_list):

    fNSens = "Sens_" + config + ".txt"
    fS, OmEff = LoadFile(sens_file_path + fNSens, 2)

    ### Computation of SNR map as a function of GW Amplitude and Peak frequency
    snr = np.zeros(( len(log10HnRstar), len(log10Ubarf) ))

    tshHn = np.zeros((len(log10HnRstar), len(log10Ubarf)  ))

    for i in xrange(len(log10HnRstar)):
        for j in xrange(len(log10Ubarf)):
            Ubarf = 10.**log10Ubarf[j]
            HnRstar = 10.**log10HnRstar[i]
            # Peak amplitude and peak frequency
            OmMax = 3. * AdInd**2 * Ubarf**4 * Omtil * HnRstar
            fp = (zp/(2*PI*HnRstar)) * Hn0
            s = fS/fp # frequency scaled to peak
            OmGW0 = Fgw0*GWSpecAcoustic(s, OmMax)
            snr[i,j], frange = StockBkg_ComputeSNR(fS, OmEff, fS, OmGW0, duration, 1.e-6, 1.)
            tshHn[i,j] = HnRstar/Ubarf
        print 'Rstar number', i, "/", len(log10HnRstar)

    np.savez('snr_' + label + '_precomputed.npz',
             tshHn=tshHn,
             snr=snr,
             log10HnRstar=log10HnRstar,
             log10Ubarf=log10Ubarf)
        





