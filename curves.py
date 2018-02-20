import numpy as np
import math


class PowerSpectrum:

    def __init__(self,
                 HoverBeta = 0.1,
                 Tstar = 180.0,
                 gstar = 106.75,
                 ubarf = 0.0545,
                 vw = 0.44,
                 adiabaticRatio = 4.0/3.0,
                 zp = 6.9,
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
        self.ubarf = ubarf
        # self.vw = 0.44
        self.vw = vw
        # self.adiabaticRatio = 4.0/3.0
        self.adiabaticRatio = adiabaticRatio
        # self.zp = 6.9
        self.zp = zp
        # self.alpha = 0.084
        self.alpha = alpha

        self.hstar = 16.5e-6*(self.Tstar/100.0) \
                     *np.power(self.gstar/100.0,1.0/6.0)

        # self.kturb = 1.97/65.0
        self.kturb = kturb
        
    def fsw(self, f):
    
        return (8.9e-6)*(1.0/self.vw)*(1.0/self.HoverBeta)*(self.zp/10.0) \
            *(self.Tstar/100)*np.power(self.gstar/100,1.0/6.0)

    def Ssw(self, f):
        fp = f/self.fsw(f)
        return np.power(fp,3.0) \
            *np.power(7.0/(4.0 + 3.0*np.power(fp,2.0)),7.0/2.0)

    def power_spectrum_sw(self, f):

        return 8.5e-6*np.power(100/self.gstar,1.0/3.0) \
            *self.adiabaticRatio*self.adiabaticRatio \
            *np.power(self.ubarf,4.0)*self.HoverBeta*self.Ssw(f)

    def fturb(self, f):
        return (27e-6)*(1.0/self.vw)*(1.0/self.HoverBeta)*(self.Tstar/100.0) \
            *np.power(self.gstar/100,1.0/6.0)

    def Sturb(self, f):
        fp = f/self.fturb(f)
        return np.power(fp,3.0)/(np.power(1 + fp, 11.0/3.0) \
                                 *(1 + 8*math.pi*f/self.hstar))

    def power_spectrum_turb(self, f):
        return (3.35e-4)*self.HoverBeta \
            *np.power(self.kturb*self.alpha/(1 + self.alpha),3.0/2.0) \
            *np.power(100/self.gstar,1.0/3.0)*self.vw*self.Sturb(f)

    def power_spectrum(self, f):
        return self.power_spectrum_sw(f) + self.power_spectrum_turb(f)
