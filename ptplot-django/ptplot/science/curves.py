import numpy as np
import math
import sys

try:
    from .espinosa import ubarf
except ValueError:
    from espinosa import ubarf
except ImportError:
    from espinosa import ubarf


def rstar_to_beta(rstar, vw):
    return math.pow(8.0*math.pi,1.0/3.0)*vw/rstar


def beta_to_rstar(beta, vw):
    return math.pow(8.0*math.pi,1.0/3.0)*vw/beta

    
class PowerSpectrum:

    def __init__(self,
                 BetaoverH = None,
                 Tstar = 180.0,
                 gstar = 100,
                 vw = None,
                 adiabaticRatio = 4.0/3.0,
                 zp = 10,
                 alpha = None,
                 kturb = 1.97/65.0,
                 H_rstar = None,
                 ubarf_in = None):
        
        # # Not sure about these
        # self.Tstar = 180.0
        self.Tstar = Tstar
        
        # self.gstar = 106.75
        self.gstar = gstar
        # self.ubarf = 0.0545
        # self.adiabaticRatio = 4.0/3.0
        self.adiabaticRatio = adiabaticRatio
        # self.zp = 6.9
        self.zp = zp
        # self.alpha = 0.084
        self.alpha = alpha

        # reduced hubble rate - for turbulence
        self.hstar = 16.5e-6*(self.Tstar/100.0) \
                     *np.power(self.gstar/100.0,1.0/6.0)

        # self.kturb = 1.97/65.0
        self.kturb = kturb


        
        # self.BetaoverH = 100
        self.BetaoverH=BetaoverH
        
        # self.vw = 0.44
        self.vw = vw

        if (vw is not None) and (ubarf_in is None):
            self.ubarf = ubarf(vw, alpha)
        elif (vw is None) and (ubarf_in is not None):
            self.ubarf = ubarf_in
        else:
            raise ValueError("Either ubarf_in or vw must be set, but not both")
        # now have ubarf
        
        # calculate shock time
        if (H_rstar is None) and (BetaoverH is not None):
            self.H_rstar = beta_to_rstar(self.BetaoverH, self.vw)
        elif (H_rstar is not None) and (BetaoverH is None):
            self.H_rstar = H_rstar
        else:
            raise ValueError("Either H_rstar or BetaoverH must be set, but not both")

        # compute shock time
        self.H_tsh = self.H_rstar/self.ubarf
        

    # Spectral shape
    @staticmethod
    def Ssw(fp, norm=1.0):
        return norm*np.power(fp,3.0) \
            *np.power(7.0/(4.0 + 3.0*np.power(fp,2.0)),7.0/2.0)


    def get_shocktime(self):
        return self.H_tsh
    
    def fsw(self, f):

        # equation 43 in shape paper
        # note (1/(H_n*R_*)) = 1/((8*pi)^{1/3}*vw/BetaoverH)
        #
        # Thus numerical prefactor is (26e-6)/(8*pi)^{1/3} = 8.9e-6
        
#        return (8.9e-6)*(1.0/self.vw)*(self.BetaoverH)*(self.zp/10.0) \
#            *(self.Tstar/100)*np.power(self.gstar/100,1.0/6.0)

        return (26.0e-6)*(1.0/self.H_rstar)*(self.zp/10.0) \
            *(self.Tstar/100)*np.power(self.gstar/100,1.0/6.0)        

    def power_spectrum_sw(self, f):
        # equation 45 in shape paper with numerical prefactor coming from
        # 0.68*(3.57e-5)*(8*pi)^(1/3)*0.12 = 8.5e-6
        # (=0.68*Fgw0*geometric*Omtil)
        #
        # using equation R_* = (8*pi)^{1/3}*vw/beta (section IV, same paper)
        # Thus: H_n*R_* = (8*pi)^{1/3}*vw/BetaoverH
        
        fp = f/self.fsw(f)
#        return 8.5e-6*np.power(100.0/self.gstar,1.0/3.0) \
#            *self.adiabaticRatio*self.adiabaticRatio \
#            *np.power(self.ubarf,4.0)*self.vw*(1.0/self.BetaoverH)*self.Ssw(fp)

        # Planck h=0.678
        h_planck = 0.678

        # 1704.05871 Eqs 39 and 45 are missing the factor of 3 [typo];
        # and there is no h_planck in eq 45 (on either side; intentional)
        return h_planck*h_planck*3.0 \
            *0.68*3.57e-5*0.12*np.power(100.0/self.gstar,1.0/3.0) \
            *self.adiabaticRatio*self.adiabaticRatio \
            *np.power(self.ubarf,4.0)*self.H_rstar*self.Ssw(fp)    

    def fturb(self, f):
        return (27e-6)*(1.0/self.vw)*(self.BetaoverH)*(self.Tstar/100.0) \
            *np.power(self.gstar/100,1.0/6.0)

    def Sturb(self, f, fp):
        return np.power(fp,3.0)/(np.power(1 + fp, 11.0/3.0) \
                                 *(1 + 8*math.pi*f/self.hstar))

    def power_spectrum_turb(self, f):
        fp = f/self.fturb(f)
        return (3.35e-4)/self.BetaoverH \
            *np.power(self.kturb*self.alpha/(1 + self.alpha),3.0/2.0) \
            *np.power(100/self.gstar,1.0/3.0)*self.vw*self.Sturb(f,fp)

    def power_spectrum_sw_conservative(self, f):
        return min(self.H_tsh,1.0)*self.power_spectrum_sw(f)
    
    def power_spectrum(self, f):
        return self.power_spectrum_sw(f) + self.power_spectrum_turb(f)

    def power_spectrum_conservative(self, f):
        return self.power_spectrum_sw_conservative(f) + self.power_spectrum_turb(f)
    
