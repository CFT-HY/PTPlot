import numpy as np
import math
import sys

try:
    from .espinosa import ubarf
except ValueError:
    from espinosa import ubarf
except ImportError:
    from espinosa import ubarf


class PowerSpectrum:

    def __init__(self,
                 HoverBeta = 0.1,
                 Tstar = 180.0,
                 gstar = 100,
                 vw = 0.44,
                 adiabaticRatio = 4.0/3.0,
                 zp = 10,
                 alpha = 0.1,
                 kturb = 1.97/65.0):
        
        # # Not sure about these
        # self.HoverBeta = 0.1
        self.HoverBeta=HoverBeta
        # self.Tstar = 180.0
        self.Tstar = Tstar
        
        # self.gstar = 106.75
        self.gstar = gstar
        # self.ubarf = 0.0545
        # self.vw = 0.44
        self.vw = vw
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

        self.ubarf = ubarf(vw, alpha)



    # Spectral shape
    def Ssw(self, fp, norm=1.0):
        return norm*np.power(fp,3.0) \
            *np.power(7.0/(4.0 + 3.0*np.power(fp,2.0)),7.0/2.0)
        
    def fsw(self, f):

        # equation 43 in shape paper
        # note (1/(H_n*R_*)) = 1/((8*pi)^{1/3}*vw*HoverBeta)
        #
        # Thus numerical prefactor is (26e-6)/(8*pi)^{1/3} = 8.9e-6
        
        return (8.9e-6)*(1.0/self.vw)*(1.0/self.HoverBeta)*(self.zp/10.0) \
            *(self.Tstar/100)*np.power(self.gstar/100,1.0/6.0)


    def power_spectrum_sw(self, f):
        # equation 45 in shape paper with numerical prefactor coming from
        # 0.68*(3.57e-5)*(8*pi)^(1/3) = 8.5e-6
        # using equation R_* = (8*pi)^{1/3}*vw/beta (section IV, same paper)
        # Thus: H_n*R_* = (8*pi)^{1/3}*vw*HoverBeta
        
        fp = f/self.fsw(f)
        return 8.5e-6*np.power(100.0/self.gstar,1.0/3.0) \
            *self.adiabaticRatio*self.adiabaticRatio \
            *np.power(self.ubarf,4.0)*self.vw*self.HoverBeta*self.Ssw(fp)

    def fturb(self, f):
        return (27e-6)*(1.0/self.vw)*(1.0/self.HoverBeta)*(self.Tstar/100.0) \
            *np.power(self.gstar/100,1.0/6.0)

    def Sturb(self, f, fp):
        return np.power(fp,3.0)/(np.power(1 + fp, 11.0/3.0) \
                                 *(1 + 8*math.pi*f/self.hstar))

    def power_spectrum_turb(self, f):
        fp = f/self.fturb(f)
        return (3.35e-4)*self.HoverBeta \
            *np.power(self.kturb*self.alpha/(1 + self.alpha),3.0/2.0) \
            *np.power(100/self.gstar,1.0/3.0)*self.vw*self.Sturb(f,fp)

    def power_spectrum(self, f):
        return self.power_spectrum_sw(f) + self.power_spectrum_turb(f)
