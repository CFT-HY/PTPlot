r"""LISA sensitivity curve from SciRD.

Implement the formula for the LISA sensitivity curve from the Science
Requirements document ESA-L3-EST-SCI-RS-001_LISA_SciRD version 1.0.

Running this module will write "StochBkg"-style output to stdout.
This reproduces the ``ScienceRequirements.txt`` file of this directory exactly,
which is verified by :py:mod:`ptplot.tests.test_noise`.

This module is kept for reference only.
PTPlot now gets its noise curve from :py:func:`pttools.omgw0.noise.omega_noise_h2`.
The combination of conventions implemented here is not consistent with the SNR formula
$\rho = \sqrt{{T}_\text{obs} \int df \frac{\Omega_\text{signal}^2}{\Omega_\text{noise}^2}}$
of :py:func:`pttools.omgw0.noise.signal_to_noise_ratio`, which is
:smith_2019:`\ ` eq. 60.
The individual differences are marked with comments below,
and :py:mod:`ptplot.tests.test_noise` verifies that they add up to the observed
factor of 5.98 between these curves and the PTtools noise.
"""

import math
import typing as tp

import numpy as np

from ptplot.science.type_hints import FloatOrArr

H100_OLD: float = 100.0 / 3.0e19
r"""
Difference 3: $1 \ \text{Mpc} = 3.0 \cdot 10^{19} \ \text{km}$ is outdated, which makes this H0 2.9 % too large
and therefore OmSens a factor of 1.058 too small.
The CODATA value used by pttools.omgw0.const.H0_100_HZ is $1 \ \text{Mpc} = 3.0857 \cdot 10^{19} \ \text{km}$.
This value is kept as it is, so that this module reproduces the .txt files of this directory.
"""


def Sh(f: FloatOrArr) -> FloatOrArr:
    r"""Compute strain sensitivity for frequency f.

    Difference 1: the factor of 1/2, which makes this a factor of $2 \sqrt{2}$ too small.
    The :lisa_sci_req:`\ ` eq. 3 sky-averaged strain sensitivity of a single equivalent-Michelson channel is
    $\frac{20}{3} \left( \frac{S_I}{(2 \pi f)^4} + S_{II} \right) R(f)$,
    so the 1/2 is an extra gain for using several channels.
    It is wrong for two reasons:

    - The gain for N_c independent channels of equal noise is $1/\sqrt{N_c}$, not $1/N_c$,
      since the SNR grows as $\sqrt{N_c}$. LISA has two noise-orthogonal channels, A and E,
      so the factor should be $1/\sqrt{2}$.
      See :smith_2019:`\ ` eq. 59, 60 and pttools.omgw0.noise.S_AE, which applies the $1/\sqrt{2}$ there.
    - The A and E channels have twice the noise-to-response ratio of the equivalent Michelson channel:
      $S_A = S_E = \frac{40}{3} (P_\text{oms} + 4 P_\text{acc}) \left( 1 + \frac{3f}{(4 f_t)^2} \right)$,
      :smith_2019:`\ ` eq. 63 and :py:func:`pttools.omgw0.noise.S_AE_approx`.
      Applying the channel gain to the (20/3) sensitivity therefore skips that factor of 2.
    """
    return (1.0/2.0) * (20.0/3.0) * (SI(f) / (2.0 * math.pi * f)**4 + SII(f)) * R(f)


def SI(f: FloatOrArr, s: float = 1., f1: float = 0.4e-3) -> FloatOrArr:
    r"""Subsidiary formula S_I for strain sensitivity.

    This agrees with pttools.omgw0.noise.S_I, i.e. :smith_2019:`\ ` eq. 53,
    and f1 agrees with :py:data:`pttools.omgw0.noise.F1_LISA`.
    """
    return 5.76e-48 * (s**-4) * (1.0 + (f1/f)**2)


def SII(f: tp.Any) -> float:  # noqa: ARG001
    r"""Subsidiary formula S_II for strain sensitivity.

    Actually just a constant.

    This agrees with pttools.omgw0.noise.P_oms, i.e. :smith_2019:`\ ` eq. 52, 54,
    for the LISA arm length L = 2.5 Gm.
    """
    return 3.6e-41


def R(f: FloatOrArr, f2: float = 25e-3) -> FloatOrArr:
    r"""Subsidiary formula R for strain sensitivity.

    Difference 2: $f_2$ is a rounded value.
    SciRD eq. 3 defines $f_2 = \frac{4}{3} f_t = \frac{2c}{3 \pi L} = 25.447 \text{mHz}$ for $L = 2.5 \text{Gm}$,
    which is :py:data:`pttools.omgw0.noise.F2_LISA`.
    This has no effect at low frequencies, but makes this function up to 3.6 % too small well above f2.
    """
    return 1.0 + (f/f2)**2


def OmSens(f: FloatOrArr) -> FloatOrArr:
    r"""Convert strain sensitivity to sensitivity in terms of Omega_GW.

    This uses $H_{100}$ instead of $H_0$, so the result is multiplied by $h^2$.

    Difference 4: the prefactor, which makes this a factor of 2 too small.
    The conversion from a one-sided noise power spectral density to the fractional GW energy
    density is $\Omega h^2 = \frac{4 pi^2}{3 H_{100}^2} f^3 S(f)$:
    :maggiore_1999:`\ ` eq. 18,
    :smith_2019:`\ ` eq. 59,
    :lisa_conventions:`\ ` eq. 167,
    :gowling_2021:`\ ` eq. 3.8 and
    :py:func:`pttools.omgw0.noise.omega_h2`.
    The $2 \pi^2$ used here follows :caprini_2020:`\ ` eq. 34.
    """
    return (2.0 * math.pi**2 / (3.0 * H100_OLD**2)) * f**3 * Sh(f)


def main(print_points: bool = True):
    """Print StochBkg-style sensitivity data to stdout.

    The first column is frequency; second is square root of strain
    sensitivity; third is sensitivity in terms of the gravitational
    wave energy density parameter.
    """
    x = np.logspace(-6,1,2000)
    y = np.sqrt(Sh(x))
    z = np.asarray(OmSens(x))
    if print_points:
        for (mx, my, mz) in zip(x, y, z, strict=True):
            print(f"{mx:g} {my:g} {mz:g} {0.0:g}")


if __name__ == "__main__":
    main()
