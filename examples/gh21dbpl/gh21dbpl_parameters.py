r"""
Best-fit spectral parameters of the DBPL
========================================

Reproduce :gowling_2021:`\ ` fig. 3:
the spectral parameters $\Omega_{p,0}$, $f_{p,0}$, $r_b$ and $b$ of the double broken power law (DBPL)
fitted to the Sound Shell Model (SSM) spectra on the $(v_{\text{wall}}, \alpha_n)$ plane,
for $r_* = 0.1$ and $T_* = 100$ GeV.
The dashed line is the Chapman-Jouguet speed $v_{\text{CJ}}(\alpha_n)$ of the bag model,
:gowling_2021:`\ ` eq. 2.4, and the black dots are the $(v_{\text{wall}}, \alpha_n)$ points of the SSM spectra.

The suppression factor $\Sigma$ is that of the article, :py:data:`pttools.ssm.suppression.suppression.GH21`,
and the small differences to the original figure are due to
the $F_{\text{gw},0}$, $f_{\ast,0}$ and $h$ of :py:mod:`pttools.omgw0`.
"""

import logging
from pathlib import Path

from matplotlib.figure import Figure
import numpy as np
from numpy.lib.npyio import NpzFile
from pttools.utils.time import log_duration

from examples.utils import save_and_show_figs
from ptplot.methods.generic import setup_logging
from ptplot.science.plot.grid import gh21dbpl_params_figure
from ptplot.science.spectrum.gh21dbpl import SSM_DATA_PATH, GH21dbplParams, data_points
from ptplot.science.utils import axis_stats

logger: logging.Logger = logging.getLogger(__name__)

#: $g_*$, :gowling_2021:`\ ` p. 7
G_STAR: float = 100.
#: $r_*$, :gowling_2021:`\ ` p. 11
R_STAR: float = 0.1
#: $T_*$, :gowling_2021:`\ ` p. 11
T_STAR: float = 100.


def data_stats(data: NpzFile) -> str:
    """Statistics of the SSM spectra of the data file of :py:func:`ptplot.science.spectrum.gh21dbpl.fit_dbpl_to_ssm`.

    :param data: SSM spectra in the format of :py:data:`ptplot.science.spectrum.gh21dbpl.SSM_DATA_PATH`,
        opened with :py:func:`numpy.load` from a path
    :return: The statistics as text
    :raises ValueError: If the file is closed
    """
    if data.fid is None:
        raise ValueError("The data file is closed.")
    data_path = Path(data.fid.name)
    v_walls = data["vw_list"]
    alpha_ns = data["alpha_list"]
    z = data["zs"]
    spectrum_keys = [key for key in data.files if key not in ("vw_list", "alpha_list", "zs")]
    spectra = np.array([data[key] for key in spectrum_keys])
    n_combinations = v_walls.size * alpha_ns.size
    peaks = spectra.max(axis=1)
    return "\n".join((
        f"SSM spectra of {data_path} ({data_path.stat().st_size / 1e6:.2f} MB)",
        axis_stats("v_wall", v_walls),
        axis_stats("alpha_n", alpha_ns),
        axis_stats("z", z),
        f"Parameter combinations: {n_combinations} = {v_walls.size} x {alpha_ns.size}",
        f"Spectra: {len(spectrum_keys)} ({n_combinations - len(spectrum_keys)} missing)",
        f"Points per spectrum: {spectra.shape[1]}, total: {spectra.size}, dtype: {spectra.dtype}",
        f"Peak values of P_gw: [{peaks.min():.3g}, {peaks.max():.3g}]",
        f"Non-finite or non-positive values: {np.count_nonzero(~(np.isfinite(spectra) & (spectra > 0)))}",
    ))


@log_duration
def main() -> dict[str, Figure]:
    """Plot the best-fit spectral parameters of the DBPL."""
    setup_logging()
    with np.load(SSM_DATA_PATH) as data:
        print(data_stats(data))
        points = data_points(data)
    params = GH21dbplParams.compute(r_star=R_STAR, T_star=T_STAR, g_star=G_STAR)
    return {"gh21dbpl_parameters": gh21dbpl_params_figure(params, points=points)}


if __name__ == "__main__":
    save_and_show_figs(main())
