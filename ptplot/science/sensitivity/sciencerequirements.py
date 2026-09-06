"""LISA sensitivity curve from SciRD.

Implement the formula for the LISA sensitivity curve from the Science
Requirements document ESA-L3-EST-SCI-RS-001_LISA_SciRD version 1.0.

Running this module will write "StochBkg"-style output to stdout.
"""

import math
import typing as tp

# import matplotlib.pyplot as plt
import numpy as np

import ptplot.science.type_hints as th


def Sh(f: th.FloatOrArr) -> th.FloatOrArr:
    """Compute strain sensitivity for frequency f."""
    return (1.0/2.0) * (20.0/3.0) * (SI(f) / (2.0 * math.pi * f)**4 + SII(f)) * R(f)


def SI(f: th.FloatOrArr, s: float = 1., f1: float = 0.4e-3) -> th.FloatOrArr:
    """Subsidiary formula S_I for strain sensitivity."""
    return 5.76e-48 * (s**-4) * (1.0 + (f1/f)**2)


def SII(f: tp.Any) -> float:
    """Subsidiary formula S_II for strain sensitivity.

    Actually just a constant."""
    return 3.6e-41


def R(f: th.FloatOrArr, f2: float = 25e-3) -> th.FloatOrArr:
    """Subsidiary formula R for strain sensitivity."""
    return 1.0 + (f/f2)**2


def OmSens(f: th.FloatOrArr) -> th.FloatOrArr:
    """Convert strain sensitivity to sensitivity in terms of Omega_GW."""

    # Hubble rate - set to 100 km/s/Mpc, thus the
    # left hand side is in terms of the reduced Hubble rate
    # i.e. this returns h^2*OmSens(f).
    H0 = 100.0 / 3.09e19

    # Standard formula
    return (2.0 * math.pi**2 / (3.0 * H0**2)) * f**3 * Sh(f)


def main(print_points: bool = True):
    """Print StochBkg-style sensitivity data to stdout.

    The first column is frequency; second is square root of strain
    sensitivity; third is sensitivity in terms of the gravitational
    wave energy density parameter."""

    x = np.logspace(-6,1,2000)
    y = np.sqrt(Sh(x))
    z = np.asarray(OmSens(x))
    if print_points:
        for (mx, my, mz) in zip(x, y, z):
            print(f"{mx:g} {my:g} {mz:g} {0.0:g}")

    # plt.loglog(x, np.sqrt(y))
    # plt.show()


if __name__ == "__main__":
    main()
