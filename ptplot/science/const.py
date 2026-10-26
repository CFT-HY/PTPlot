"""Constants used by other modules."""

import math
import typing as tp

from matplotlib.typing import RcKeyType
import numpy as np
import pttools.bubble.const as bubble_const
import pttools.omgw0.const as omgw0_const
import pttools.ssm.const as ssm_const

import ptplot.science.type_hints as th

# -----
# Default values
# -----
#: Default mean adiabatic index $\Gamma$
DEFAULT_ADIABATIC_INDEX: float = bubble_const.DEFAULT_ADIABATIC_INDEX
#: Default transition strength $\alpha$
DEFAULT_ALPHA: float = 0.1
#: Default Hubble-scaled nucleation rate parameter $\tilde{\beta} \equiv \frac{\beta}{H_*}$
DEFAULT_BETA_TILDE: float = 10.
#: Default degrees of freedom $g_*$
DEFAULT_G_STAR: float = omgw0_const.DEFAULT_G_STAR
#: Whether to use the legacy $\max(v_{\text{wall}}, c_s)$
#: in the $\tilde{\beta} \leftrightarrow r_*$ conversion by default.
#: Please see :py:func:`pttools.ssm.nucleation.beta` for details.
DEFAULT_LEGACY_NUCLEATION_CS_MAX: bool = False

DEFAULT_OMEGA_TILDE_GW: float = ssm_const.DEFAULT_OMEGA_TILDE_GW
r"""
Default $\tilde{\Omega}_\text{gw}$.

For details, please see
:py:data:`pttools.ssm.const.DEFAULT_OMEGA_TILDE_GW`.
"""

#: Log the progress of a parallel computation every $x$ %. Set to None to disable the logging.
DEFAULT_LOG_PROGRESS_PERCENTAGE: float = 10.
#: Default minimum frequency $f_\text{min}$
DEFAULT_F_MIN: float = 1e-5
#: Default maximum frequency $f_\text{max}$
DEFAULT_F_MAX: float = 0.1
#: Default LISA mission duration $T_\text{obs}$ in years
DEFAULT_OBS_YEARS: float = 3.
#: Default transition temperature $T_*$
DEFAULT_T_STAR: float = 180.
#: Default wall speed $v_\text{wall}$
DEFAULT_V_WALL: float = 0.9

# -----
# Default plotting range sizes
# -----
#: Default number of frequency points of a noise curve
DEFAULT_F_SIZE: int = 2000
#: Default number of points for $(\alpha_n, \tilde{\beta}, \bar{U}_\text{f}, r_*)$
DEFAULT_GRID_SIZE: int = 51
#: Minimum number of frequencies for e.g. a noise curve
MIN_F_SIZE: int = 2

# -----
# Default plotting ranges
# -----
#: Default range of transition strength $\alpha_n$ for e.g. SNR plots
DEFAULT_ALPHA_N_RANGE: th.FloatArr1D = np.logspace(-2, 0.3, DEFAULT_GRID_SIZE)
#: Default range of frequency $f$
DEFAULT_F_RANGE: th.FloatArr1D = np.logspace(math.log10(DEFAULT_F_MIN), math.log10(DEFAULT_F_MAX), DEFAULT_F_SIZE)
#: Default range of inverse phase transition duration $\tilde{\beta} \equiv \frac{\beta}{H_*}$
DEFAULT_BETA_TILDE_RANGE: th.FloatArr1D = np.logspace(0.5, 4.5, DEFAULT_GRID_SIZE)
#: Default range of mean bubble spacing $r_*$
DEFAULT_R_STAR_RANGE: th.FloatArr1D = np.logspace(-4, 0.08, DEFAULT_GRID_SIZE)
#: Default range of $\bar{U}_\text{f}$
DEFAULT_UBARF_RANGE: th.FloatArr1D = np.logspace(-2, 0, DEFAULT_GRID_SIZE)

# -----
# Minimum accuracy settings
# -----
# Minimum values of the accuracy settings in :py:class:`SSMSettingsForm`,
# which are those used for compiling the Numba functions in the dataset example of PTtools
MIN_N_Z_LOOKUP: int = 200
MIN_N_T: int = 100
MIN_NX_P_TILDE_GW: int = 50

# -----
# Default plotting parameters
# -----
#: Default font size of figure labels
DEFAULT_LABEL_FONTSIZE: int = 14
#: Default Matplotlib context
DEFAULT_RC_CONTEXT: dict[RcKeyType, tp.Any] = {
    "backend": "Agg",
    "font.family": "serif",
    "mathtext.fontset": "dejavuserif",
    # "text.usetex": usetex
}

# -----
# Numerical constants
# -----
#: $c_s$, bag model sound speed
CS0: tp.Final[float] = bubble_const.CS0
#: $c_s^2$, bag model sound speed squared
CS0_2: tp.Final[float] = bubble_const.CS0_2
#: $h$, dimensionless reduced Hubble constant
H: float = omgw0_const.H
#: $h^2$, dimensionless reduced Hubble constant squared
H2: float = omgw0_const.H2
OMEGA_PHOTON_H2 = omgw0_const.OMEGA_PHOTON_H2
r"""
$\Omega_{\gamma,0} h^2$, the photon density parameter today, scaled by $h^2$
For details, please see
:py:data:`pttools.omgw0.const.OMEGA_PHOTON_H2`.
"""
#: Number of seconds in a year
YEAR_IN_SECONDS: float = omgw0_const.YEAR_IN_SECONDS

# -----
# Names
# -----
ALPHA_NAME: str = "transition strength (α)"
BETA_TILDE_NAME: str = "inverse phase transition duration (β/H)"
G_STAR_NAME: str = "degrees of freedom (g*)"
HUGE_ALPHA_NAME: str = "huge α"
T_STAR_NAME: str = "nucleation temperature (T*, GeV)"
V_WALL_NAME: str = "wall velocity (v_w)"
# Names with LaTeX symbols for the web pages
ALPHA_NAME_LATEX: str = r"transition strength ($\alpha$)"
BETA_TILDE_NAME_LATEX: str = r"inverse phase transition duration ($\beta/H_*$)"
G_STAR_NAME_LATEX: str = r"degrees of freedom ($g_*$)"
T_STAR_NAME_LATEX: str = r"nucleation temperature ($T_*$, GeV)"
V_WALL_NAME_LATEX: str = r"wall velocity ($v_\mathrm{w}$)"
