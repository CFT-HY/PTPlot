

#!/usr/bin/env python
# Broken power law (Mark Hindmarsh Sep 2015)
#-
# Hacked from
#   ExampleUseSNR1.py v 0.3 (Antoine Petiteau 15/05/2015)

############################## Import modules ##############################
import math, sys, os


# Fix some things if running standalone
if (__name__ == "__main__" and __package__ is None) or __package__ == '':

    # eLISATools from Antoine
    # from eLISATools import *
    from snr import *
    
    from calculate_powerspectrum import PowerSpectrum
    from precomputed import available_sensitivitycurves_lite, available_durations

    root = './'
    
else:
    
    # eLISATools from Antoine
    # from .eLISATools import *
    from .snr import *
    
    from .calculate_powerspectrum import PowerSpectrum
    from .precomputed import available_sensitivitycurves_lite, available_durations

    
    from django.conf import settings
    BASE_DIR = getattr(settings, "BASE_DIR", None)
    root = os.path.join(BASE_DIR, 'ptplot', 'science')

sensitivity_root = os.path.join(root, 'sensitivity')
    
############################## Functions ##############################

def get_SNRcurve(Tn, gstar, MissionProfile,  ubarfmax=1):
    duration = yr*available_durations[MissionProfile]
    
    ## Values of log10 Ubarf to scan
    log10Ubarf = np.linspace(-2, math.log10(ubarfmax), 51)

    ## Values of log10 HnRstar to scan
    log10HnRstar = np.linspace(-4, 0.08, 51)

    # Model parameters
    #Omtil = 1.2e-1 # GW efficiency parameter
    #zp = 10        # Peak kR*

#    Tn = 100.      # Nucleation temp in GeV
#    gstar = 100    # d.o.f.
    #AdInd = 4./3.  # Adiabatic index

    # Hubble rate redshifted to now - equation 42
    #Hn0 = 16.5e-6 * (Tn/100) * (gstar/100)**(1./6) # Hz


    sensitivity_curve = os.path.join(sensitivity_root,
                                     available_sensitivitycurves_lite[
                                         MissionProfile])

    fS, OmEff = LoadFile(sensitivity_curve, 2)
    
    ### Computation of SNR map as a function of GW Amplitude and Peak frequency
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
            
            # this stuff should all be aligned with the PS calc

            # Peak amplitude and peak frequency, equation 45
            # OmMax = 0.68 * AdInd**2 * Ubarf**4 * Omtil * HnRstar
            # GW dilution factor now - equation 44
            # Fgw0 = 3.57e-5* (100.0/gstar)**(1./3)
            
            # equation 43, peak frequency
            # fp = 26.0e-6*(1.0/HnRstar)*(zp/10)*(Tn/100)* (gstar/100)**(1.0/6.0)

            # s = fS/fp # frequency scaled to peak
            # OmGW0 = Fgw0*PowerSpectrum.Ssw(s, OmMax)
            OmGW0 = ps.power_spectrum_sw_conservative(fS)
            
            tshHn[i,j] = ps.get_shocktime() # HnRstar/Ubarf

            # hacky way of doing it
            # OmGW0 = OmGW0*min(tshHn[i,j],1.0)
            
            snr[i,j], frange = StockBkg_ComputeSNR(fS, OmEff, fS, OmGW0, duration, 1.e-6, 1.)

        #print('Rstar number', i, "/", len(log10HnRstar))

    return tshHn, snr, log10HnRstar, log10Ubarf



def main(sensitivity_curve, Tn, gstar):
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
        print('Rstar number', i, "/", len(log10HnRstar))

    dest_head = os.path.splitext(sensitivity_curve)[0]
    destination = f'{dest_head}_Tn_{Tn}_gstar_{gstar}_precomputed.npz'
        
    np.savez(destination,
             tshHn=tshHn,
             snr=snr,
             log10HnRstar=log10HnRstar,
             log10Ubarf=log10Ubarf)

    sys.stderr.write('Wrote sensitivity curve to %s\n'
                     % destination)

    
if __name__ == '__main__':

    if not len(sys.argv) == 4:
        sys.stderr.write("Usage: %s <sensitivity curve> <Tn> <gstar>\n"
                         "\n"
                         "Where: <Tn> is the nuleation temperature\n"
                         "       <gstar> is the number of relativistic dofs\n"
                         "Note: duration defaults to 5 years\n"
                         % sys.argv[0])
        sys.exit(1)

    main(sys.argv[1],float(sys.argv[2]),float(sys.argv[3]))
