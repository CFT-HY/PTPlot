"""Constants used by other modules"""

import numpy as np

DEFAULT_VW: float = 0.9
DEFAULT_ALPHA: float = 0.1
DEFAULT_BETA_OVER_H: float = 10
DEFAULT_T_STAR: float = 180
DEFAULT_G_STAR: float = 100
DEFAULT_ADIABATIC_RATIO: float = 4 / 3
DEFAULT_MISSION_PROFILE: int = 0

CS0: float = 1 / np.sqrt(3)
CS0_2: float = 1 / 3

YEAR_IN_SECONDS: float = 365.25 * 86400
H_PLANCK: float = 0.678
H_PLANCK2: float = H_PLANCK**2

ALPHA_NAME: str = "transition strength (α)"
BETA_OVER_H_NAME: str = "inverse phase transition duration (β/H)"
G_STAR_NAME: str = "degrees of freedom (g*)"
T_STAR_NAME: str = "nucleation temperature (T*, GeV)"
VW_NAME: str = "wall velocity (v_w)"
