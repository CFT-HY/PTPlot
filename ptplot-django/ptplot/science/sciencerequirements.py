import math
import numpy as np

def Sh(f):
    return (1.0/2.0)*(20.0/3.0)* \
        (SI(f)/(
            (2.0*math.pi*f)*(2.0*math.pi*f)*(2.0*math.pi*f)*(2.0*math.pi*f))
         + SII(f))*R(f)

def SI(f):
    s = 1
    f1 = 0.4e-3
    return 5.76e-48*(1.0/(s*s*s*s))*(1.0 + (f1/f)*(f1/f))

def SII(f):
    return 3.6e-41

def R(f):
    f2 = 25e-3
    return 1.0 + (f/f2)*(f/f2)

def OmSens(f):
    H0 = 100.0/3.0e18
    return (2.0*math.pi*math.pi/(3.0*H0*H0))*f*f*f*Sh(f)

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import numpy as np
    x = np.logspace(-6,1,2000)
    y = np.sqrt(Sh(x))
    z = OmSens(x)
    for (mx,my,mz) in zip(x,y,z):
        print("%g %g %g %g" % (mx, my, mz, 0.0))
#    plt.loglog(x, np.sqrt(y))
#    plt.show()
