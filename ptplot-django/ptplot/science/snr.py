# Inspired by Antoine Petiteau's eLISAToolBox aka eLISATools.py but
# just the minimum functions we need.
#
# - LoadFile is copied directly, for now.
# - StockBkg_ComputeSNR is adapted to use a trapezium rule integration
#   with nonuniform interval.
#
import sys, os, re
import numpy as np
import matplotlib.pyplot as plt
from numpy import pi


############################## DEFINITION OF CONSTANTS ##############################

c=299792458.           # light speed in m/s
G=6.67384e-11         # Gravitational constant
MSun=1.989e30         # Solar mass in kg
MSuns=(MSun*G)/(c**3) # Solar mass in seconds
pc=3.08567758e16      # parsec in meter 
pcs=pc/c              # parsec in seconds
kpc=1000.*pcs          # kiloparsec in second
yr=365.25*86400.      # year in s
au=1.49597870660e11   # astronomical unit in meter
R=au/c                # Distance Sun eLISA barycenter in seconds
H0ref = 100./3.08568025e19           # 100 Mpc/s/km
Std2hOm = 4*np.pi**2/(3.*H0ref**2)  # factor for converting standard sensitivity to energy density


def LoadFile(fNIn, iCol):
    """
    Load first column and column iCol of a file 
    Inputs : 
        - fNIn [req] : input file name
        - iCol [req] : index of the column containing the data (column 0 is the reference)
    Output :
        - 2 arrays : reference and data
    """

    fIn = open(fNIn,'r')
    lines = fIn.readlines()
    fIn.close()

    Nd = 0
    for line in lines :
        if line[0]!='#' and len(line)>0 :
            Nd += 1

    x  = np.zeros(Nd)
    y = np.zeros(Nd)
    iL = 0
    for line in lines :
        if line[0]!='#' and len(line)>0 :
            w = re.split("\s+",line)
            x[iL] = float(w[0])
            y[iL] = float(w[iCol])
            iL += 1
    return x,y



############################################
# FOR STOCHASTIC BAKGROUND
############################################

def StockBkg_ComputeSNR(SensFr, SensOm, GWFr, GWOm, Tobs, fmin=-1, fmax=-1) :
    """ 
    Compute Signal to Noise Ratio and the used frequency range fmin and fmax
    for a given sensitivity defined by the two numpy array (same size) SensFr for frequency 
    and SensOm for sensitivity in Omega unit,  a given spectrum defined  by the two numpy array (same size) GWFr for frequency 
    and GWOm for GW in Omega unit, and a given observation time Tobs in years. 
    If frange is not defined, the frequency range will be adjust on the two frequency arrays.

    Inputs : 
        - SensFr [req] : numpy array of frequency in Hz corresponding to SensOm 
        - SensOm [req] : numpy numpy of sensitivity in Omega unit
        - GWFr   [req] : numpy numpy of frequency in Hz corresponding to GWOm
        - GWOm   [req] : numpy numpy of GW stochastic background
        - Tobs   [req] : observation time in seconds

    Output : 
        - Signal To Noise  
    """

#    sys.stderr.write('%g %g\n' % (fmin, fmax))    
    
    ### Frequency range
    if fmin < 0 :
        fmin = max(SensFr[0], GWFr[0])
    if fmax < 0 :
        fmax = min(SensFr[-1], GWFr[-1])

    ifmin = np.argmax(SensFr >= fmin)
    ifmax = np.argmax(SensFr >= fmax)

#    sys.stderr.write('%d %g %d %g\n' % (ifmin, fmin, ifmax, fmax))
    
    fr = SensFr[ifmin:ifmax]

#    sys.stderr.write('%g %g\n' % (fr[0], fr[-1]))
        
    OmEff = SensOm[ifmin:ifmax]
    
    ### Make an interpolated data series, interpolate GWOm onto same
    ### series as OmEff
    OmGWi = 10.**np.interp(np.log10(fr),np.log10(GWFr),np.log10(GWOm))
    
    ### Numerical integration over frequency
    rat = OmGWi**2 / OmEff**2

    Itg = 0.
    for i in range(len(fr) - 1):
        dfr = fr[i+1] - fr[i]
        Itg = Itg + dfr*(rat[i] + rat[i+1])/2.0
    Itg = Itg 

    snr = np.sqrt(Tobs*Itg)
    
    return snr, [fmin,fmax]








