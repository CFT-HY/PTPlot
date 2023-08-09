#!/usr/bin/env python3

"""Precomputation of the SNR curves

This file contains all the functions related to the computation of the signal
to noise ratio curves for the UbarfRstar and AlphaBeta plots. This is done first
so the plot can then be built in parts. Can be used as a standalone module.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015)

Contains the following functions: #DCH be sure to update this when we remove the other function
    * get_SNRcurve - calculates the SNR curves
    * main - calculates the SNR curves and stores them in a file
"""

import math

# Fix some things if running standalone
if (__name__ == "__main__" and __package__ is None) or __package__ == '':
    from snr import *
    from calculate_powerspectrum import PowerSpectrum
    from precomputed import available_sensitivitycurves_lite, available_durations
    root = './'
else:
    from .snr import *
    from .calculate_powerspectrum import PowerSpectrum
    from .precomputed import available_sensitivitycurves_lite, available_durations
    from django.conf import settings
    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')
sensitivity_root = os.path.join(root, 'sensitivity')

def get_SNRcurve(Tn, gstar, MissionProfile, ubarfmax=1):
    """Calculate the SNR curves for the plots

    Parameters
    ----------
    Tn : float
        Temperature at nucleation time
    gstar : float
        Degrees of freedom
    MissionProfile : int
        Which sensitivity curve to use
    ubarfmax : float
        Maximum of rms fluid velocity (default to 1)

    Returns
    -------
    tshHn : np.ndarray
        Shocktimes
    snr : np.ndarray
        SNR values
    log10HnRstar : np.ndarray
        Scanned values of log10(HnRstar)
    log10Ubarf : np.ndarray
        Scanned values of log10(Ubarf)
    """

    # Get mission duration in seconds
    duration = yr*available_durations[MissionProfile]
    
    # Values of log10(Ubarf) to scan
    log10Ubarf = np.linspace(-2, math.log10(ubarfmax), 51)

    # Values of log10(HnRstar) to scan
    log10HnRstar = np.linspace(-4, 0.08, 51)

    sensitivity_curve = os.path.join(sensitivity_root,
                                     available_sensitivitycurves_lite[
                                         MissionProfile])
    fS, OmEff = LoadFile(sensitivity_curve, 2)
    
    # Computation of SNR map as a function of GW amplitude and peak frequency
    snr = np.zeros(( len(log10HnRstar), len(log10Ubarf) ))
    tshHn = np.zeros((len(log10HnRstar), len(log10Ubarf)  ))

    for i in range(len(log10HnRstar)):
        for j in range(len(log10Ubarf)):
            Ubarf = 10.**log10Ubarf[j]
            HnRstar = 10.**log10HnRstar[i]

            ps = PowerSpectrum(Tstar=Tn,
                               gstar=gstar,
                               H_rstar=HnRstar,
                               ubarf_in=Ubarf)

            OmGW0 = ps.power_spectrum_sw_conservative(fS)

            # Get shocktime (HnRstar/Ubarf) (TODO: rename this to match notation)
            tshHn[i,j] = ps.get_shocktime()
            
            snr[i,j], frange = StockBkg_ComputeSNR(fS, OmEff, fS, OmGW0, duration, 1.e-6, 1.)

    return tshHn, snr, log10HnRstar, log10Ubarf

# TODO: clean up this function so it only appears once
def main(sensitivity_curve, Tn, gstar):
    """Calculate the SNR curves and store them in a file

    Parameters
    ----------
    sensitivity_curve : string
        File name where the sensitivity curve is stored
    Tn : float
        Temperature at nucleation time
    gstar : float
        Degrees of freedom
    """

    # Mission duration in seconds
    duration = 5*yr
    
    # Values of log10(Ubarf) to scan
    log10Ubarf = np.arange(-2,0.025,0.025)

    # Values of log10(HnRstar) to scan
    log10HnRstar = np.arange(-4,0.025,0.025)

    # Model parameters
    # GW efficiency parameter
    Omtil = 1.2e-1
    # Peak kR*
    zp = 10
    # Adiabatic index
    AdInd = 4./3.
    # Hubble rate redshifted to now - equation 42
    Hn0 = 16.5e-6 * (Tn/100) * (gstar/100)**(1./6) # Hz

    fS, OmEff = LoadFile(sensitivity_curve, 2)
    
    # Computation of SNR map as a function of GW amplitude and peak frequency
    snr = np.zeros(( len(log10HnRstar), len(log10Ubarf) ))
    tshHn = np.zeros((len(log10HnRstar), len(log10Ubarf)  ))

    for i in range(len(log10HnRstar)):
        for j in range(len(log10Ubarf)):
            Ubarf = 10.**log10Ubarf[j]
            HnRstar = 10.**log10HnRstar[i]

            # approach used in the previous function?
            # Peak amplitude and peak frequency, equation 45
            OmMax = 0.68 * AdInd**2 * Ubarf**4 * Omtil * HnRstar
            # GW dilution factor now - equation 44
            Fgw0 = 3.57e-5* (100.0/gstar)**(1./3)
            
            # equation 43, peak frequency
            fp = 26.0e-6*(1.0/HnRstar)*(zp/10)*(Tn/100)* (gstar/100)**(1.0/6.0)

            s = fS/fp # frequency scaled to peak
            OmGW0 = Fgw0*PowerSpectrum().Csw(s, OmMax)
            snr[i,j], frange = StockBkg_ComputeSNR(fS, OmEff, fS, OmGW0, duration, 1.e-6, 1.)
            tshHn[i,j] = HnRstar/Ubarf
        print('Rstar number', i, "/", len(log10HnRstar))

    dest_head = os.path.splitext(sensitivity_curve)[0]
    destination = f'{dest_head}_Tn_{Tn}_gstar_{gstar}_precomputed.npz'
        
    np.savez(destination,
             tshHn=tshHn,
             snr=snr,
             log10HnRstar=log10HnRstar,
             log10Ubarf=log10Ubarf)

    sys.stderr.write('Wrote SNR contour to %s\n'
                     % destination)

# If this is used standalone, check the right amount of arguments are being
# passed. If not, show the user the expected input.
if __name__ == '__main__':
    if len(sys.argv) == 4:
        sensitivity_curve = str(sys.argv[1])
        Tn = float(sys.argv[2])
        gstar = float(sys.argv[3])
        main(sensitivity_curve,Tn,gstar)
    else:
        sys.stderr.write("Usage: %s <sensitivity curve> <Tn> <gstar>\n"
                         "\n"
                         "Where: <Tn> is the nucleation temperature\n"
                         "       <gstar> is the number of relativistic dofs\n"
                         "Note: duration defaults to 5 years\n"
                         % sys.argv[0])
        sys.exit(1)
