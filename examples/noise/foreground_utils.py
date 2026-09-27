r"""Variants of the galactic compact binary foreground for the SNR examples.

:py:func:`pttools.omgw0.noise.S_gb` implements :cornish_2017:`\ ` eq. 3 as printed, with the 4-year parameters.
These functions allow comparing it with some alternatives:

- The sign in front of $\beta$ corrected as in :schmitz_2020:`\ ` footnote 3 (eq. 3.9),
  which is also used by :gowling_2021:`\ ` (footnote before eq. 3.10).
- The parameters for other observation times of :cornish_2017:`\ ` table 1.
- The fit of :babak_2021:`\ ` sec. 9 (eq. 85-86), which depends continuously on the observation time.
- A scaling factor with respect to the instrument noise.
  The fits above are given in the units of the single-channel strain sensitivity $S_n = \frac{20}{3} \ldots$,
  whereas :py:func:`pttools.omgw0.noise.omega_ins_h2` is the two-channel SGWB sensitivity of :smith_2019:`\ `.
  The correct relative normalisation of the two should be checked, and the scaling factor allows studying its effect.
"""

import numpy as np
from pttools.omgw0.noise import GB_DATA, omega_eb_h2, omega_h2, omega_ins_h2

from ptplot.science.noise import Noise
import ptplot.science.type_hints as th

#: Amplitude $A$ of :cornish_2017:`\ ` eq. 3
A_CORNISH: float = 1.8e-44
#: Amplitude $A$ of :babak_2021:`\ ` eq. 85
A_BABAK: float = 1.14e-44


def S_gb_cornish(
        f: th.FloatArr1D,
        t_obs: float = 4.,
        beta_sign: float = 1.,
        amplitude: float = A_CORNISH) -> th.FloatArr1D:
    r"""Galactic binary foreground of :cornish_2017:`\ ` eq. 3.

    $$S_c(f) = A f^{-7/3} e^{-f^\alpha + \beta f \sin(\kappa f)} \left[ 1 + \tanh(\gamma (f_k - f)) \right]$$

    :param f: Frequencies $f$ (Hz)
    :param t_obs: Observation time in years. Must be one of those of :cornish_2017:`\ ` table 1.
    :param beta_sign: Sign in front of $\beta$. :schmitz_2020:`\ ` corrects it to $-1$.
    :param amplitude: Amplitude $A$
    :return: $S_c(f)$ (1/Hz)
    """
    matches = np.flatnonzero(GB_DATA[0] == t_obs)
    if matches.size != 1:
        raise ValueError(f"Parameters are available only for t_obs in {GB_DATA[0]}, got {t_obs}.")
    alpha, beta, kappa, gamma, fk = GB_DATA[1:, matches[0]]
    return amplitude * f**(-7/3) * np.exp(-f**alpha + beta_sign * beta * f * np.sin(kappa * f)) \
        * (1 + np.tanh(gamma * (fk - f)))


def S_gal_babak(
        f: th.FloatArr1D,
        t_obs: float = 4.,
        amplitude: float = A_BABAK,
        alpha: float = 1.8,
        f2: float = 0.31e-3) -> th.FloatArr1D:
    r"""Galactic binary foreground of :babak_2021:`\ ` eq. 85-86.

    $$S_\text{Gal}(f) = A f^{-7/3} e^{-(f/f_1)^\alpha}
    \frac{1}{2} \left[ 1 + \tanh \left( -\frac{f - f_k}{f_2} \right) \right]$$
    $$\log_{10} f_1 = -0.25 \log_{10} T_\text{obs} - 2.7, \quad \log_{10} f_k = -0.27 \log_{10} T_\text{obs} - 2.47$$

    :param f: Frequencies $f$ (Hz)
    :param t_obs: Observation time $T_\text{obs}$ in years
    :param amplitude: Amplitude $A$
    :param alpha: $\alpha$
    :param f2: $f_2$ (Hz)
    :return: $S_\text{Gal}(f)$ (1/Hz)
    """
    f1 = 10**(-0.25 * np.log10(t_obs) - 2.7)
    fk = 10**(-0.27 * np.log10(t_obs) - 2.47)
    return amplitude * f**(-7/3) * np.exp(-(f / f1)**alpha) * 0.5 * (1 + np.tanh(-(f - fk) / f2))


def noise_with_foreground(
        obs_years: float = 3.,
        s_gb: th.FloatArr1D | None = None,
        gb_factor: float = 1.,
        eb_factor: float = 1.) -> Noise:
    r"""Create a noise curve with a custom galactic binary foreground.

    $$\Omega_\text{noise} h^2 = \Omega_\text{ins} h^2 + a_\text{eb} \Omega_\text{eb} h^2
    + a_\text{gb} \frac{4 \pi^2}{3 H_{100}^2} f^3 S_\text{gb}(f)$$

    :param obs_years: Mission duration $T_\text{obs}$ in years
    :param s_gb: Galactic binary foreground $S_\text{gb}$ on the frequencies of the default noise curve.
        None disables the galactic foreground.
    :param gb_factor: Scaling factor $a_\text{gb}$ of the galactic foreground
    :param eb_factor: Scaling factor $a_\text{eb}$ of the extragalactic foreground
    :return: Noise curve
    """
    noise = Noise(obs_years=obs_years, eb=False, gb=False)
    om = omega_ins_h2(noise.f) + eb_factor * omega_eb_h2(noise.f)
    if s_gb is not None:
        om = om + gb_factor * omega_h2(f=noise.f, S=s_gb)
    noise.noise = np.ascontiguousarray(om)
    return noise
