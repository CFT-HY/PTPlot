import numpy as np
import math

# Not sure about these
HoverBeta = 0.1
Tstar = 180.0


gstar = 106.75
ubarf = 0.0545
vw = 0.44
adiabaticRatio = 4.0/3.0
zp = 6.9
alpha = 0.084

hstar = 16.5e-6*(Tstar/100)*np.power(gstar/100,1.0/6.0)

kturb = 1.97/65.0

def fsw(f):
    
    return (8.9e-6)*(1.0/vw)*(1.0/HoverBeta)*(zp/10.0) \
        *(Tstar/100)*np.power(gstar/100,1.0/6.0)

def Ssw(f):
    fp = f/fsw(f)
    return np.power(fp,3.0)*np.power(7.0/(4.0 + 3.0*np.power(fp,2.0)),7.0/2.0)

def power_spectrum_sw(f):

    return 8.5e-6*np.power(100/gstar,1.0/3.0)*adiabaticRatio*adiabaticRatio \
        *np.power(ubarf,4.0)*HoverBeta*Ssw(f)


def fturb(f):
    return (27e-6)*(1.0/vw)*(1.0/HoverBeta)*(Tstar/100.0) \
        *np.power(gstar/100,1.0/6.0)

def Sturb(f):
    fp = f/fturb(f)
    return np.power(fp,3.0)/(np.power(1 + fp, 11.0/3.0)*(1 + 8*math.pi*f/hstar))

def power_spectrum_turb(f):
    return (3.35e-4)*HoverBeta*np.power(kturb*alpha/(1 + alpha),3.0/2.0)*np.power(100/gstar,1.0/3.0)*vw*Sturb(f)

def power_spectrum(f):
    return power_spectrum_sw(f) + power_spectrum_turb(f)
