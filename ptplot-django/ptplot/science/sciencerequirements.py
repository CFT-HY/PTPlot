"""@package sciencerequirements.py
Implement LISA sensitivity curve from SciRD.

Implement the formula for the LISA sensitivity curve from the Science
Requirements document ESA-L3-EST-SCI-RS-001_LISA_SciRD version 1.0.

Running this module will write 'StochBkg'-style output to stdout.
"""
import math
import numpy as np

def Sh(f):
    """Compute strain sensitivity for frequency f."""
    
    return (1.0/2.0)*(20.0/3.0)* \
        (SI(f)/(
            (2.0*math.pi*f)*(2.0*math.pi*f)*(2.0*math.pi*f)*(2.0*math.pi*f))
         + SII(f))*R(f)

def SI(f):
    """Subsidiary formula S_I for strain sensitivity."""
    
    s = 1
    f1 = 0.4e-3
    return 5.76e-48*(1.0/(s*s*s*s))*(1.0 + (f1/f)*(f1/f))

def SII(f):
    """Subsidiary formula S_II for strain sensitivity.

    Actually just a constant."""
    
    return 3.6e-41

def R(f):
    """Subsidiary formula R for strain sensitivity."""
    
    f2 = 25e-3
    return 1.0 + (f/f2)*(f/f2)

def OmSens(f):
    """Convert strain sensitivity to sensitivity in terms of Omega_GW."""

    # Hubble rate
    H0 = 100.0/3.0e18

    # Standard formula
    return (2.0*math.pi*math.pi/(3.0*H0*H0))*f*f*f*Sh(f)


def main():
    """Print StochBkg-style sensitivity data to stdout.

    The first column is frequency; second is square root of strain
    sensitivity; third is sensitivity in terms of the gravitational
    wave energy density parameter."""
    
#    import matplotlib.pyplot as plt

    x = np.logspace(-6,1,2000)
    y = np.sqrt(Sh(x))
    z = OmSens(x)
    for (mx,my,mz) in zip(x,y,z):
        print("%g %g %g %g" % (mx, my, mz, 0.0))

#    plt.loglog(x, np.sqrt(y))
#    plt.show()


if __name__ == '__main__':
    main()
