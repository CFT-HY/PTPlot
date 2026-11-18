r"""
Best-fit spectral parameters of the DBPL
========================================

Reproduce :gowling_2021:`\ ` fig. 3:
the spectral parameters $\Omega_{p,0}$, $f_{p,0}$, $r_b$ and $b$ of the double broken power law (DBPL)
fitted to the Sound Shell Model (SSM) spectra on the $(v_{\text{wall}}, \alpha_n)$ plane,
for $r_* = 0.1$ and $T_* = 100$ GeV.
The dashed line is the Chapman-Jouguet speed $v_{\text{CJ}}(\alpha_n)$ of the bag model,
:gowling_2021:`\ ` eq. 2.4.

The differences to the original figure are due to the suppression factor $\Sigma$,
which is that of :py:mod:`pttools.ssm.suppression` instead of the original dataset,
and to the $F_{\text{gw},0}$, $f_{\ast,0}$ and $h$ of :py:mod:`pttools.omgw0`.
"""

import logging

from matplotlib.figure import Figure
from pttools.utils.time import log_duration

from examples.utils import save_and_show_figs
from ptplot.science.plot.grid import gh21dbpl_params_figure
from ptplot.science.spectrum.gh21dbpl import GH21dbplParams

logger: logging.Logger = logging.getLogger(__name__)

G_STAR: float = 100.
R_STAR: float = 0.1
T_STAR: float = 100.


@log_duration
def main() -> dict[str, Figure]:
    """Plot the best-fit spectral parameters of the DBPL."""
    params = GH21dbplParams.compute(r_star=R_STAR, T_star=T_STAR, g_star=G_STAR)
    return {"gh21dbpl_parameters": gh21dbpl_params_figure(params)}


if __name__ == "__main__":
    save_and_show_figs(main())
