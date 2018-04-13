

#!/usr/bin/env python
# Broken power law (Mark Hindmarsh Sep 2015)
#
# Hacked from
#   ExampleUseSNR1.py v 0.3 (Antoine Petiteau 15/05/2015)

############################## Import modules ##############################
import math, sys

# eLISATools from Antoine
from eLISATools import *


from curves import PowerSpectrum

############################## Functions ##############################


def main(sensitivity_curve):
    duration = 5*yr
    
    ## Values of log10 Ubarf to scan
    log10Ubarf = np.arange(-2,0.025,0.2)

    ## Values of log10 HnRstar to scan
    log10HnRstar = np.arange(-4,0.025,0.2)

    # Model parameters
    Omtil = 1.2e-1 # GW efficiency parameter
    zp = 10        # Peak kR*

    Tn = 100.      # Nucleation temp in GeV
    hstar = 100    # d.o.f.
    AdInd = 4./3.  # Adiabatic index

    # Hubble rate redshifted to now - equation 42
    Hn0 = 16.5e-6 * (Tn/100) * (hstar/100)**(1./6) # Hz



    fS, OmEff = LoadFile(sensitivity_curve, 2)

    ### Computation of SNR map as a function of GW Amplitude and Peak frequency
    snr = np.zeros(( len(log10HnRstar), len(log10Ubarf) ))

    tshHn = np.zeros((len(log10HnRstar), len(log10Ubarf)  ))

    for i in xrange(len(log10HnRstar)):
        for j in xrange(len(log10Ubarf)):
            Ubarf = 10.**log10Ubarf[j]
            HnRstar = 10.**log10HnRstar[i]
            # Peak amplitude and peak frequency, equation 45
            OmMax = 0.68 * AdInd**2 * Ubarf**4 * Omtil * HnRstar
            # GW dilution factor now - equation 44
            Fgw0 = 3.57e-5* (100.0/hstar)**(1./3)
            
            # equation 43, peak frequency - not working!
            fp = 26.0e-6*(1.0/HnRstar)*(zp/10)*(Tn/100)* (hstar/100)**(1.0/6.0)

            s = fS/fp # frequency scaled to peak
            OmGW0 = Fgw0*PowerSpectrum().Ssw(s, OmMax)
            snr[i,j], frange = StockBkg_ComputeSNR(fS, OmEff, fS, OmGW0, duration, 1.e-6, 1.)
            tshHn[i,j] = HnRstar/Ubarf
        print('Rstar number', i, "/", len(log10HnRstar))

    destination = sensitivity_curve + '_precomputed.npz'
        
    np.savez(destination,
             tshHn=tshHn,
             snr=snr,
             log10HnRstar=log10HnRstar,
             log10Ubarf=log10Ubarf)

    sys.stderr.write('Wrote sensitivity curve to %s\n'
                     % destination)

    
if __name__ == '__main__':

    if not len(sys.argv) == 2:
        sys.stderr.write("Usage: %s <sensitivity curve>\n"
                         "\n"
                         "Note: duration defaults to 5 years\n"
                         % sys.argv[0])
        sys.exit(1)

    main(sys.argv[1])
