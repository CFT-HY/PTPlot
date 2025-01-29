#!/usr/bin/env python3

"""Precomputation of the SNR curves

This file contains all the functions related to the computation of the signal
to noise ratio curves for the UbarfRstar and AlphaBeta plots. This is done first
so the plot can then be built in parts. Can be used as a standalone module.
Broken power law by Mark Hindmarsh (Sep 2015), inspired by Antoine Petiteau's
ExampleUseSNR1.py v0.3 (May 2015)

Contains the following function:
    * get_SNRcurve - calculates the SNR curves
"""

import math

# Fix some things if running standalone
if (__name__ == "__main__" and __package__ is None) or __package__ == '':
    from snr import *
    from calculate_powerspectrum import PowerSpectrum
    from precomputed import available_sensitivitycurves_lite, available_durations, available_labels
else:
    from .snr import *
    from .calculate_powerspectrum import PowerSpectrum
    from .precomputed import available_sensitivitycurves_lite, available_durations, available_labels
sensitivity_root = os.path.join(os.path.dirname(__file__), 'sensitivity')


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

            # Get shocktime (H_tsh = HnRstar/Ubarf)
            tshHn[i,j] = ps.get_shocktime()
            
            snr[i,j], frange = StockBkg_ComputeSNR(fS, OmEff, fS, OmGW0, duration, 1.e-6, 1.)

    return tshHn, snr, log10HnRstar, log10Ubarf


# If this is used standalone, check the right amount of arguments are being
# passed. If not, show the user the expected input.
if __name__ == '__main__':
    if len(sys.argv) == 4:
        Tn = float(sys.argv[1])
        gstar = float(sys.argv[2])
        MissionProfile = int(sys.argv[3])
        ubarfmax = 1.0

        tshHn, snr, log10HnRstar, log10Ubarf = get_SNRcurve(Tn, gstar, MissionProfile, ubarfmax)

        # Use the mission profile to load the sensitivity curve name
        sensitivity_curve = os.path.join(sensitivity_root,
                                         available_sensitivitycurves_lite[
                                             MissionProfile])
        dest_head = os.path.splitext(sensitivity_curve)[0]
        destination = f'{dest_head}_Tn_{Tn}_gstar_{gstar}_precomputed.npz'

        np.savez(destination,
                 tshHn=tshHn,
                 snr=snr,
                 log10HnRstar=log10HnRstar,
                 log10Ubarf=log10Ubarf)

        sys.stderr.write('Wrote SNR contour to %s\n'
                         % destination)

    else:
        sys.stderr.write("Usage: %s <Tn> <gstar> <MissionProfile>\n"
                         "\n"
                         "Where: <Tn> is the nucleation temperature\n"
                         "       <gstar> is the number of relativistic dofs\n"
                         "       <MissionProfile> specifies which sensitivity curve to use:\n"
                         % sys.argv[0])
        for i in range(len(available_labels)):
            sys.stderr.write("        %s for %s \n" %(i,available_labels[i]) )

        sys.exit(1)
