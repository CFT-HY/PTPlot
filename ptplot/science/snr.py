"""SNR computation

This file contains all the functions related to the calculation of the
signal to noise ratio for a given sensitivity, spectrum and observation time.
These functions are inspired by the ones in Antoine Petiteau's eLISAToolBox aka
eLISATools.py, adapted to use a trapezium rule integration with nonuniform interval.

Contains the following functions:
    * LoadFile - reads arrays from a file
    * StockBkg_ComputeSNR - computes the SNR
"""

import sys, os, re
import numpy as np
import matplotlib.pyplot as plt
from numpy import pi
import scipy.integrate

# One year in seconds, needed to convert mission duration
yr=365.25*86400.

def LoadFile(fNIn, iCol):
    """Load first column and column iCol of a file

    Parameters
    ----------
    fNIn : string
        Input file name
    iCol : int
        Index of the column containing the data (column 0 is the reference)

    Returns
    -------
    x : np.ndarray
        Reference column
    y : np.ndarray
        Data read from file
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

def StockBkg_ComputeSNR(SensFr, SensOm, GWFr, GWOm, Tobs, fmin=-1, fmax=-1) :
    """Compute signal to noise ratio

    Compute signal to noise ratio and the used frequency range fmin and fmax for
    a given sensitivity, defined by the two numpy arrays (of the same size)
    SensFr (for frequency) and SensOm for sensitivity in Omega unit; a given
    spectrum, defined by the two numpy arrays (same size) GWFr for frequency
    and GWOm for GW in Omega units; and a given observation time Tobs in years.
    If the frequency range frange is not defined, the frequency range will be
    adjusted based on the two frequency arrays.

    Parameters
    ----------
    SensFr : np.ndarray
        Array of frequencies (in Hz) corresponding to SensOm
    SensOm : np.ndarray
        Array of sensitivities in Omega units
    GWFr : np.ndarray
        Array of frequencies (in Hz) corresponding to GWOm
    GWOm : np.ndarray
        Array of GW stochastic background
    Tobs : float
        Total observation time / mission duration (in seconds)
    fmin : float
        Minimum frequency for frange (in Hz)
    fmax : float
        Maximum frequency for frange (in Hz)

    Returns
    -------
    snr: float
        Signal to noise ratio
    """

    # If the frequency range has not been given, find it automatically
    if fmin < 0 :
        fmin = max(SensFr[0], GWFr[0])
    if fmax < 0 :
        fmax = min(SensFr[-1], GWFr[-1])

    ifmin = np.argmax(SensFr >= fmin)
    ifmax = np.argmax(SensFr >= fmax)

    fr = SensFr[ifmin:ifmax]
    OmEff = SensOm[ifmin:ifmax]
    
    # Make an interpolated data series, interpolate GWOm onto same series as OmEff
    OmGWi = 10.**np.interp(np.log10(fr),np.log10(GWFr),np.log10(GWOm))
    
    # Numerical integration over frequency
    rat = OmGWi**2 / OmEff**2
    Itg = scipy.integrate.trapezoid(rat, fr)

    # Calculate snr taking into account the observation time
    snr = np.sqrt(Tobs*Itg)
    
    return snr, [fmin,fmax]
