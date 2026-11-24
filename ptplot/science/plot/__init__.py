"""Plotting tools for PTPlot."""

from . import (
    bubble,
    grid,
    lattice,
    logarithmic,
    ps,
    snr,
    snr_alpha_beta,
    snr_ubarf_rstar,
    ticks,
    utils,
)
from . import snr_comparison as _snr_comparison
from . import snr_histogram as _snr_histogram
from .bubble import *
from .grid import *
from .lattice import *
from .logarithmic import *
from .ps import *
from .snr import *
from .snr_alpha_beta import *
from .snr_comparison import *
from .snr_histogram import *
from .snr_ubarf_rstar import *
from .ticks import *
from .utils import *

# Some submodules export a function with the same name as the module,
# which replaces the submodule attribute in the star import. Therefore, they are referred to with aliases.
__all__: list[str] = []
__all__ += bubble.__all__
__all__ += grid.__all__
__all__ += lattice.__all__
__all__ += logarithmic.__all__
__all__ += ps.__all__
__all__ += snr.__all__
__all__ += snr_alpha_beta.__all__
__all__ += _snr_comparison.__all__
__all__ += _snr_histogram.__all__
__all__ += snr_ubarf_rstar.__all__
__all__ += ticks.__all__
__all__ += utils.__all__
