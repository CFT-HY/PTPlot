###############################################################
##########            eLISAToolBox v 0.3             ##########
#                                                             #
# Toolbox containing various tools related to eLISA :         #
#  - Signal to Noise Ratio for GW detector given a spectrum   #
#    of stochastic background                                 #
#  - Time evolution of monochromatic binary                   #
#                                                             #
# Authors : A. Petiteau                                       #
# Last modification : 15/05/2015 from A.a Petiteau            #
#                                                             #
###############################################################


############################## IMPORTATION OF MODULES ##############################
import sys,os,re
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



############################## FUNCTIONS ##############################

############################################
# GENRAL
############################################

def run(command, disp=False, NoExit=False):
    """
    Run the given command in shell 
    Inputs : 
        - command [req]: command to be send
        - disp    : true to display the command 
        - NoExit  : exit if the command failed
    """
    commandline = command % globals()
    if disp : 
        print ("----> %s" % commandline)
    
    try:
        assert(os.system(commandline) == 0)
    except:
        print ('Script %s failed at command "%s".' % (sys.argv[0],commandline))
        if not NoExit :
            sys.exit(1)



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



def PSDNoise(f, L0s=3.3356409519815204, NoiseAcc=6.00e-48, NoiseOpt=5.07e-38):
    """
    Compute eLISA noise PSD analytically 
    Inputs : 
        - f  [req] : Frequency of interest
        - L0s      : Armlength in seconds (eLISA-L3 : 1e9/c = 3.3356409519815204)
        - NoiseAcc : Acceleration noise (eLISA-L3 : 6.00e-48)
        - NoiseOpt : Optical noise (eLISA-L3 : 5.07e-38)
    Output : 
        - Noise PSD at f
    """

    phiL = 2.0*np.pi*L0s*f;
    
    ### PSD Optical Noise
    SOpticalNoise = NoiseOpt*f*f
    
    ### PSD Acceleration Noise
    SAccelerationNoise = NoiseAcc*(1+1.e-4/f)/(f*f)
    
    ### PSD of noise for X, Y, Z
    Sn = 16.0*np.sin(phiL)*np.sin(phiL)*(SOpticalNoise + (3.0+np.cos(2.0*phiL))*SAccelerationNoise);

    #### Clipping to avoid to low
    fLim = 0.25/L0s
    NoiseMinLowf = 1.e200
    for i in xrange(len(f)):
        if f[i]<fLim :
           ## Look for the mininmum
           if Sn[i]<NoiseMinLowf :
               NoiseMinLowf = Sn[i]
        else :
           ## Apply for the mininmum
           if NoiseMinLowf>Sn[i] :
               Sn[i] = NoiseMinLowf
    return Sn
 












############################################
# FOR MONOCHROMATIC BINARY
############################################

def BinaryMono_RunSim(t, GWparameters, L0s):
    """ 
    Compute the time evolution of TDI X corresponding to a monochromatic binary seen by eLISA
    Inputs :
        - t [req] : time in seconds
        - GWparameters [req] : array of source parameters :
            [beta, lambdaa, polarisation, inclination, frequency, phase0, amplitude]
            or
            [beta, lambdaa, polarisation, inclination, frequency, phase0, m1_MSun, m2_MSun, D_pc]
        - L0s [req] : Armlength in seconds (eLISA-L3 : 1e9/c)
    Output :
        - TDI X time serie
    """
    
    ########## Precomputation for GW source ##########
    if len(GWparameters)==7 :
        [beta, lambdaa, polarisation, inclination, frequency, phase0, amplitude] = GWparameters
    elif len(GWparameters)==9 :
        [beta, lambdaa, polarisation, inclination, frequency, phase0, m1_MSun, m2_MSun, D_pc] = GWparameters
        m1=m1_MSun*MSuns
        m2=m2_MSun*MSuns
        D=D_pc*pcs
        mtot=m1+m2
        eta=m1*m2/(mtot*mtot)
        amplitude = 2.*mtot*eta*(mtot*pi*frequency)**(2./3.)/D
    else:
        print ("ERROR : Bad number of parameters : 7 or 9 ")
        sys.exit(1)

    print ("Source parameters :")
    print (" - Sky position : beta =",beta,"rad ,  lambda =",lambdaa,"rad")
    print (" - Polarization  =",polarisation,"rad")
    print (" - Inclination   =",inclination,"rad")
    print (" - Amplitude     =",amplitude)
    print (" - Frequency     =",frequency,"Hz")
    print (" - Initial phase =",phase0,"rad")

    cosinc  = np.cos(inclination)           # cos(inclination)
    hSp0  = amplitude*(1+cosinc*cosinc)     # amplitude on polarisation +
    hSc0  = -2.*amplitude*cosinc            # amplitude on polarisation x
    om = 2.*pi*frequency                    # pulsation omega
    c2pol = np.cos(2.*polarisation)         # cos(2*polarisation)
    s2pol = np.sin(2.*polarisation)         # sin(2*polarisation)
    thd = np.pi/2.-beta                     # colattitude from lattitude 
    phd = lambdaa                           # longitude
    
    
    ########## Precomputation for response functions ##########
    Dph2L = om*L0s
    C = -2.*L0s*om*np.sin(Dph2L)
    f2pioyr=2.*np.pi/yr
    sthd=np.sin(thd)
    fp6s2th = 6.*np.sin(2.*thd)/32.
    fp18s3sth2 = -18.*np.sqrt(3.)*np.sin(thd)*np.sin(thd)/32.
    fps3cth2p1 = -np.sqrt(3.)*(np.cos(thd)*np.cos(thd)+1)/32.
    fp9sin2phd = 9.*np.sin(2.*phd)
    fcs3cthd = np.sqrt(3)*np.cos(thd)/16.
    fc9c2phd = 9.*np.cos(2.*phd) 
    fc6sthd = 6.*np.sin(thd)/16.

    ########## Compute signal in low frequency approximation ##########
    '''
    #### Loop on time step
    X=np.zeros(Nt)
    for iT in xrange(Nt):
        t = iT*dt
        PhT = f2pioyr*t
        tk=t-R*sthd*np.cos(PhT-phd)
        php = om*tk-Dph2L
        Fp = fp6s2th*(3.*np.sin(PhT+phd)-np.sin(3.*PhT-phd))+fp18s3sth2*np.sin(2.*PhT)+fps3cth2p1*(np.sin(4.*PhT-2.*phd)+9.*np.sin(2.*phd))
        Fc = fcs3cthd*(np.cos(4.*PhT-2.*phd)-fc9c2phd)+fc6sthd*(np.cos(3.*PhT-phd)+3.*np.cos(PhT+phd))
        
        ###  I^{\nu} (t) \simeq  - 2 L  \dot{\phi} (t_{k})  \sin \Delta \phi_{2L}(t_{k}) & \left[  h_{S0+}(t_{k})  \left[ \cos{(2 \psi(t_{k}) )}  F_{+I}(t_{k})   -\sin{(2\psi(t_{k}) )}  F_{\times I}(t_{k})  \right] \cos \phi' (t_{k}) + h_{S 0 \times}(t_{k})  \left[ \sin{(2 \psi(t_{k})  )}  F_{+I}(t_{k})  + \cos {(2 \psi(t_{k})  )}  F_{\times I}(t_{k})  \right]  \sin \phi' (t_{k})  \right] 
        X[iT] = C*(hSp0*(c2pol*Fp-s2pol*Fc)*np.cos(php)+hSc0*(s2pol*Fp-c2pol*Fc)*np.sin(php))
    '''
    
    ########## Direct operation on time series of numpy array ... much faster
    PhT  = f2pioyr*t
    tk=t-R*sthd*np.cos(PhT-phd)
    php = om*tk-Dph2L+phase0
    Fp = fp6s2th*(3.*np.sin(PhT+phd)-np.sin(3.*PhT-phd))+fp18s3sth2*np.sin(2.*PhT)+fps3cth2p1*(np.sin(4.*PhT-2.*phd)+fp9sin2phd)
    Fc = fcs3cthd*(np.cos(4.*PhT-2.*phd)-fc9c2phd)+fc6sthd*(np.cos(3.*PhT-phd)+3.*np.cos(PhT+phd))
        
    ###  I^{\nu} (t) \simeq  - 2 L  \dot{\phi} (t_{k})  \sin \Delta \phi_{2L}(t_{k}) & \left[  h_{S0+}(t_{k})  \left[ \cos{(2 \psi(t_{k}) )}  F_{+I}(t_{k})   -\sin{(2\psi(t_{k}) )}  F_{\times I}(t_{k})  \right] \cos \phi' (t_{k}) + h_{S 0 \times}(t_{k})  \left[ \sin{(2 \psi(t_{k})  )}  F_{+I}(t_{k})  + \cos {(2 \psi(t_{k})  )}  F_{\times I}(t_{k})  \right]  \sin \phi' (t_{k})  \right] 
    X = C*(hSp0*(c2pol*Fp-s2pol*Fc)*np.cos(php)+hSc0*(s2pol*Fp-c2pol*Fc)*np.sin(php))
        
    return X
        
        



def BinaryMono_ComputelogL(GWparam, t, dataf, Sn, ifmin, ifmax, df):
    """
    Compute the compute log likelihood 
    Inputs : 
        - GWparameters [req] : array of source parameters :
            [beta, lambdaa, polarisation, inclination, frequency, phase0, amplitude]
            or
            [beta, lambdaa, polarisation, inclination, frequency, phase0, m1_MSun, m2_MSun, D_pc]
        - t     [req] : time in seconds
        - dataf [req] : array of data in frequency
        - Sn    [req] : array of noise PSD in frequency
        - ifmin [req] : index of minimal frequency
        - ifmax [req] : index of maximal frequency
        - df    [req] : size of frequency bin  
     Output :
        - log likelihood
    """
    
    ########## Generate model ##########
    X=RunSim(t,GWparam)

    ########## Fourier transform model ##########
    dt=t[2]-t[1]
    hXf = dt*np.fft.rfft(X)[1:]

    ######### Log likelihood #########
    hXfoSn = hXf[ifmin:ifmax].conj() / Sn[ifmin:ifmax]
    logL = 4.*np.real(df*np.sum(dataf[ifmin:ifmax]*hXfoSn)) - 2.*np.real(df*np.sum(hXf[ifmin:ifmax]*hXfoSn))














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
        - Tobs   [req] : observation time in years
        - fmin         : minimal frequency
        - fmax         : maximal frequency

    Output : 
        - Signal To Noise  
    """
    #print SensFr, SensOm, GWFr, GWOm, Tobs, fmin, fmax
    
    dfr = SensFr[1]-SensFr[0]

    ### Frequency range
    if fmin < 0 :
        fmin = max(SensFr[0], GWFr[0])
    if fmax < 0 :
        fmax = min(SensFr[-1], GWFr[-1])
    
    ifmin = int(np.floor(fmin/dfr))
    ifmax = int(np.ceil(fmax/dfr))
    fr = SensFr[ifmin:ifmax]

    OmEff   = SensOm[ifmin:ifmax]
    OmEff2 = OmEff**2


    ### Make an interpolated data serie
    OmGWi = 10.**np.interp(np.log10(fr),np.log10(GWFr),np.log10(GWOm))

    ### Numerical integration over frequency
    Itg = 0.
    for i in range(len(fr)):
        Itg = Itg + OmGWi[i]**2 / OmEff2[i]
    Itg = dfr*Itg 

    snr = np.sqrt(Tobs*Itg)
    
    return snr, [fmin,fmax]



def StockBkg_PlotSpectrum(plotfile, SensFr, SensOm, SensPowerLaw, GWFr, GWOm, frange, title, displayref):
    """
    Plot the spectrum of bakground 

    Inputs : 
        - plotfile     [req] : file name for output
        - SensFr       [req] : numpy array of frequency in Hz corresponding to SensOm 
        - SensOm       [req] : numpy array of sensitivity in Omega unit
        - SensPowerLaw [req] : numpy array of Power Law Sensitivity 
        - GWFr         [req] : numpy numpy of frequency in Hz corresponding to GWOm
        - GWOm         [req] : numpy numpy of GW stochastic background
        - Tobs         [req] : observation time in years
        - frange       [req] : frequency range
        - title        [req] : title
    """

    plt.loglog(SensFr, SensOm, '-b', label="Standard sensitivity")
    plt.loglog(SensFr, SensPowerLaw,  '-g', label="Power-law sensitivity")
    OmGWi = 10.**np.interp(np.log10(SensFr),np.log10(GWFr),np.log10(GWOm))
    plt.loglog(SensFr, OmGWi, '-r', label="GW spectrum")
    if displayref :
        plt.loglog(GWFr, GWFr, '*r')
    
    fsize=10
    plt.title(title,fontsize=fsize)
    plt.xlabel("Frequency (f)")
    #plt.rc('text', usetex=True)
    #plt.ylabel("$h^2 \Omega (f)$")
    plt.ylabel("h^2 Omega (f)")
    plt.grid()
    plt.legend(loc=2)
    plt.xlim(frange)
    if plotfile=="None" :
        plt.show()
    else : 
        print ("Record plot in", plotfile)
        plt.savefig(plotfile)


def StockBkg_SNRConf(GWFr, GWOm, ConfigName, duration, fmin, fmax, DirSens):
    """
    Compute Signal to Noise Ratio for a given configuration 

    Inputs : 
        - GWFr       [req] : numpy array of frequency in Hz corresponding to GWOm
        - GWOm       [req] : numpy array of GW stochastic background
        - ConfigName [req] : name of the configuration 
        - Tobs       [req] : observation time in years
        - fmin       [req] : minimal frequency in Hz
        - fmax       [req] : maximal frequency in Hz
        - DirSens    [req] : directory containing sensitivity data

    """

    fNSens = DirSens+ "/Sens_" +ConfigName +".txt"
    print ("Load sensitivity from ",fNSens,"...")
    if (not os.path.isfile(fNSens)):
        print ("ERROR : Cannot find the sensitivity file", fNSens)
        sys.exit(1)
    SensFr, SensOm = LoadFile(fNSens, 2)

    snr = StockBkg_ComputeSNR(SensFr, SensOm, GWFr, GWOm, duration, fmin, fmax)

    return snr
    
    















