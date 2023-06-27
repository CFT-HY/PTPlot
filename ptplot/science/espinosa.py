"""Energy budget computations

This file contains all the functions related to the calculation of
the energy budget of a First-order Phase Transition, following J. R.
Espinosa et al. JCAP06 (2010) 028 (arXiv:1004.4187).

Contains the following functions:
    * ubarf - calculates ubarf from alpha and vw
    * kappav - calculates kappav from alpha and vw
    * ubarf_to_alpha - converts from ubarf to alpha
"""

import math
import scipy.optimize
import numpy as np

def ubarf(vw, alpha):
    """Calculates the rms fluid velocity

    Parameters
    ----------
    vw : float
        Wall velocity
    alpha : float
        Phase transition strength

    Returns
    -------
    ubarf : float
        Measure of the rms fluid velocity
    """

    return math.sqrt((3.0/4.0)*kappav(vw,alpha)*alpha/(1.0 + alpha))

def kappav(vw, alpha):
    """Calculates the fluid efficiency

    The fluid efficiency gives the fraction of vacuum energy that is
    turned into kinetic energy during the phase transition.

    Parameters
    ----------
    vw : float
        Wall velocity
    alpha : float
        Phase transition strength

    Returns
    -------
    kappav : float
        Fluid efficiency
    """

    # Approximations for the different kappas can be found in Appendix A
    # of arXiv:1004.4187
    kappaA = math.pow(vw,6.0/5.0)*6.9*alpha/ \
             (1.36 - 0.037*math.sqrt(alpha) + alpha)
    kappaB = math.pow(alpha,2.0/5.0)/ \
             (0.017 + math.pow(0.997 + alpha,2.0/5.0))
    kappaC = math.sqrt(alpha)/(0.135 + math.sqrt(0.98 + alpha))
    kappaD = alpha/(0.73 + 0.083*math.sqrt(alpha) + alpha)

    cs = math.pow(1.0/3.0,0.5)

    xiJ = (math.sqrt((2.0/3.0)*alpha + alpha*alpha) + math.sqrt(1.0/3.0))/(1+alpha)

    deltaK = -0.9*math.log((math.sqrt(alpha)/(1 + math.sqrt(alpha))))

    if vw < cs:
        return math.pow(cs,11.0/5.0)*kappaA*kappaB/ \
                ((math.pow(cs,11.0/5.0)
                 - math.pow(vw,11.0/5.0))*kappaB
                 + vw*math.pow(cs,6.0/5.0)*kappaA)
    elif vw > xiJ:
        return math.pow(xiJ - 1, 3.0)*math.pow(xiJ,5.0/2.0)* \
                math.pow(vw,-5.0/2.0)*kappaC*kappaD/ \
                ((math.pow(xiJ-1,3.0) - math.pow(vw -1,3.0))* \
                 math.pow(xiJ,5.0/2.0)*kappaC + math.pow(vw - 1,3.0)*kappaD)
    else:
        return kappaB + (vw - cs)*deltaK \
                + (math.pow(vw-cs,3.0)/math.pow(xiJ-cs,3.0))*(kappaC-kappaB-(xiJ-cs)*deltaK)


def ubarf_to_alpha(vw, this_ubarf):
    """Calculates alpha from ubarf

    For a given wall velocity and list of ubarf values, calculate
    the corresponding list of alpha values. As the calculation of
    the rms fluid velocity for a given alpha is not easy to invert,
    we calculate ubarf for different alphas until finding an alpha
    that minimises the difference between the calculated ubarf and
    this_ubarf (input) value.

    Parameters
    ----------
    vw : float
        Wall velocity
    this_ubarf : np.ndarray
        List of rms fluid velocities

    Returns
    -------
    alpha_list : np.ndarray
        List of phase transition strengths
    """

    def ubarf_to_alpha_inner(vw, this_ubarf):

        def alphatrue(alpha):
            return ubarf(vw, alpha) - this_ubarf

#        try:
        return scipy.optimize.brentq(alphatrue, 1e-8, 1e12, xtol=1e-6)
#        except ValueError:
#            import sys
#            sys.stderr.write('vw=%g, this_ubarf=%g\n' % (vw, this_ubarf))


    vfunc = np.vectorize(ubarf_to_alpha_inner)
    return vfunc(vw, this_ubarf)
