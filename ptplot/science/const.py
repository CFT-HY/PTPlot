"""Constants used by other modules"""

import typing as tp

from matplotlib.typing import RcKeyType
import numpy as np
from pttools.bubble import const as bubble_const

import ptplot.science.type_hints as th

# Default values
DEFAULT_ADIABATIC_RATIO: float = bubble_const.DEFAULT_ADIABATIC_INDEX
DEFAULT_ALPHA: float = 0.1
DEFAULT_BETA_OVER_H: float = 10
DEFAULT_G_STAR: float = 100
DEFAULT_K_TURB: float = 1.97 / 65.0

DEFAULT_OMEGA_TILDE_GW: float = 0.012
r"""
Default $\tilde{\Omega}_\text{gw}$, :hindmarsh_2017:`\ ` p. 13.
Please note that there is a typo in the original article: $0.12 \rightarrow 0.012$: :hindmarsh_2017_erratum:`\ `.
This value is obtained numerically from simulations.
:caprini_2020:`\ ` p. 16
"""

DEFAULT_SNR_F_MIN: float = 1e-6
DEFAULT_SNR_F_MAX: float = 1.
DEFAULT_T_STAR: float = 180
DEFAULT_V_WALL: float = 0.9

DEFAULT_ZP: int = 10
r"""
This default value is determine from simulations,
and accounts for the observed peak value of $kR_*$.
When $v_\text{wall} \approx v_\text{CJ}$, the value of $z_p$ may differ from 10,
as the sound shells are so thin that they may set a substantially smaller length scale
$\Delta R_* = R_* \frac{|v_\text{wall} - c_s|}{c_s}$.
:caprini_2020:`\ ` p. 17
"""

# Default plotting ranges
DEFAULT_GRID_SIZE: int = 51
DEFAULT_ALPHA_N_RANGE: th.FloatArr1D = np.logspace(-2, 0.3, DEFAULT_GRID_SIZE)
DEFAULT_BETA_OVER_H_RANGE: th.FloatArr1D = np.logspace(0.5, 4.5, DEFAULT_GRID_SIZE)
DEFAULT_R_STAR_RANGE: th.FloatArr1D = np.logspace(-4, 0.08, DEFAULT_GRID_SIZE)
DEFAULT_UBARF_RANGE: th.FloatArr1D = np.logspace(-2, 0, DEFAULT_GRID_SIZE)

# Default plotting parameters
DEFAULT_LABEL_FONTSIZE: int = 14
DEFAULT_RC_CONTEXT: dict[RcKeyType, tp.Any] = {
    "backend": "Agg",
    "font.family": "serif",
    "mathtext.fontset": "dejavuserif",
    # "text.usetex": usetex
}

# Numerical constants
#: $c_s$, bag model sound speed
CS0: tp.Final[float] = bubble_const.CS0
#: $c_s^2$, bag model sound speed squared
CS0_2: tp.Final[float] = bubble_const.CS0_2
#: $h_\text{Planck}$
H_PLANCK: float = 0.678
#: $h_\text{Planck}^2$
H_PLANCK2: float = H_PLANCK**2
YEAR_IN_SECONDS: float = 365.25 * 86400

# Names
ALPHA_NAME: str = "transition strength (α)"
BETA_OVER_H_NAME: str = "inverse phase transition duration (β/H)"
G_STAR_NAME: str = "degrees of freedom (g*)"
HUGE_ALPHA_NAME: str = "huge α"
T_STAR_NAME: str = "nucleation temperature (T*, GeV)"
V_WALL_NAME: str = "wall velocity (v_w)"
