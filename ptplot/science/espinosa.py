"""Energy budget computations

This file contains all the functions related to the calculation of
the energy budget of a First-order Phase Transition, following J. R.
Espinosa et al. JCAP06 (2010) 028 (arXiv:1004.4187).
"""

import math
import scipy.optimize
import numpy as np

from ptplot.science import const


def ubarf(vw: float, alpha: float, adiabaticRatio: float = const.DEFAULT_ADIABATIC_RATIO):
    r"""Calculate the rms fluid velocity

    :param vw: Wall velocity $v_\text{wall}$
    :param alpha: Phase transition strength $\alpha$
    :param adiabaticRatio: Adiabatic index $\Gamma$
    :return: Measure of the rms fluid velocity $\bar{U}_f$
    """
    return math.sqrt((1.0/adiabaticRatio) * kappav(vw, alpha) * alpha/(1.0 + alpha))


def kappav(vw: float, alpha: float) -> float:
    r"""Calculate the fluid efficiency

    The fluid efficiency gives the fraction of vacuum energy that is
    turned into kinetic energy during the phase transition.

    :param vw: Wall velocity $v_\text{wall}$
    :param alpha: Phase transition strength $\alpha$
    :return: Fluid efficiency $\kappa_v$
    """

    # Approximations for the different kappas can be found in Appendix A
    # of arXiv:1004.4187
    kappaA = math.pow(vw, 6.0/5.0) * 6.9 * alpha / (1.36 - 0.037 * math.sqrt(alpha) + alpha)
    kappaB = math.pow(alpha, 2.0/5.0) / (0.017 + math.pow(0.997 + alpha, 2.0/5.0))
    kappaC = math.sqrt(alpha) / (0.135 + math.sqrt(0.98 + alpha))
    kappaD = alpha / (0.73 + 0.083 * math.sqrt(alpha) + alpha)

    cs = const.CS0
    xiJ = (math.sqrt((2.0/3.0) * alpha + alpha * alpha) + math.sqrt(1.0/3.0)) / (1+alpha)
    deltaK = -0.9 * math.log((math.sqrt(alpha)/(1 + math.sqrt(alpha))))

    if vw < cs:
        return math.pow(cs, 11.0/5.0)*kappaA*kappaB/ \
                ((math.pow(cs, 11.0/5.0)
                 - math.pow(vw, 11.0/5.0))*kappaB
                 + vw*math.pow(cs, 6.0/5.0)*kappaA)
    elif vw > xiJ:
        return math.pow(xiJ - 1, 3.0) * math.pow(xiJ,5.0/2.0) * \
                math.pow(vw, -5.0/2.0)*kappaC*kappaD/ \
                ((math.pow(xiJ-1, 3.0) - math.pow(vw -1,3.0)) *
                 math.pow(xiJ, 5.0/2.0)*kappaC + math.pow(vw - 1,3.0)*kappaD)
    else:
        return kappaB + (vw - cs) * deltaK \
                + (math.pow(vw-cs, 3.0)/math.pow(xiJ-cs,3.0)) * (kappaC-kappaB-(xiJ-cs) * deltaK)


def ubarf_to_alpha_scalar(vw: float, this_ubarf: float, adiabaticRatio: float = const.DEFAULT_ADIABATIC_RATIO) -> float:
    def alpha_true(alpha: float):
        return ubarf(vw, alpha, adiabaticRatio) - this_ubarf

    return scipy.optimize.brentq(alpha_true, a=1e-8, b=1e12, xtol=1e-6)


def ubarf_to_alpha(vw: float, this_ubarf: np.ndarray, adiabaticRatio: float = const.DEFAULT_ADIABATIC_RATIO) -> np.ndarray:
    r"""Calculates alpha from ubarf

    For a given wall velocity and list of ubarf values, calculate
    the corresponding list of alpha values. As the calculation of
    the rms fluid velocity for a given alpha is not easy to invert,
    we calculate ubarf for different alphas until finding an alpha
    that minimises the difference between the calculated ubarf and
    this_ubarf (input) value.

    :param vw: Wall velocity $v_\text{wall}$
    :param this_ubarf: List of rms fluid velocities $\bar{U}_f$
    :param adiabaticRatio: Adiabatic index $\Gamma$
    :return: Array of phase transition strengths $\alpha$
    """
    vfunc = np.vectorize(ubarf_to_alpha_scalar)
    return vfunc(vw, this_ubarf, adiabaticRatio)
