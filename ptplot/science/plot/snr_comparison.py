"""SNR comparison between engines"""

from matplotlib.figure import Figure
import numpy as np

from ptplot.science import const
from ptplot.science.spectrum.engine import Engine
from ptplot.science.mission_profile import DEFAULT_MISSION_PROFILE, MissionProfile
from ptplot.science.plot.logarithmic import add_points, log_figure
from ptplot.science.snr_grid import snr_grid_alpha_beta
from ptplot.science.utils import log_range
import ptplot.science.type_hints as th


def snr_comparison(
        engine1: Engine,
        engine2: Engine,
        v_wall_snr: float,
        T_star_snr: float,
        g_star_snr: float,
        alphas: th.FloatOrArrOrList1D2D,
        beta_over_Hs: th.FloatOrArrOrList1D2D,
        adiabatic_ratio: float = const.DEFAULT_ADIABATIC_RATIO,
        labels: th.StrOrListOrNestedList | None = None,
        titles: th.StrOrList | None = None,
        mission_profile: MissionProfile = DEFAULT_MISSION_PROFILE) -> Figure:
    """Compare the SNR values given by different engines"""

    alpha_n_grid = log_range(alphas, const.DEFAULT_ALPHA_N_RANGE)
    beta_over_H_grid = log_range(beta_over_Hs, const.DEFAULT_BETA_OVER_H_RANGE)
    snr1, shock_times1 = snr_grid_alpha_beta(
        T_star=T_star_snr, g_star=g_star_snr, v_wall=v_wall_snr, mission_profile=mission_profile,
        alpha_n=alpha_n_grid, beta_over_H=beta_over_H_grid,
        adiabatic_ratio=adiabatic_ratio, engine=engine1
    )
    snr2, shock_times2 = snr_grid_alpha_beta(
        T_star=T_star_snr, g_star=g_star_snr, v_wall=v_wall_snr, mission_profile=mission_profile,
        alpha_n=alpha_n_grid, beta_over_H=beta_over_H_grid,
        adiabatic_ratio=adiabatic_ratio, engine=engine2
    )
    log10_alpha_n_grid = np.log10(alpha_n_grid)
    log10_beta_over_H_grid = np.log10(beta_over_H_grid)

    fig, ax, extent = log_figure(
        x=log10_alpha_n_grid,
        y=log10_beta_over_H_grid,
        xlabel=r"$\alpha$",
        ylabel=r"$\beta/H_*$",
    )
    snr_rel_diff = (snr2 - snr1) / np.maximum(snr1, snr2)
    contour = ax.contourf(snr_rel_diff, extent=extent)
    fig.colorbar(
        contour,
        ax=ax,
        label=
            rf"$\frac{{\text{{SNR}}_{{{engine2.name}}} - \text{{SNR}}_{{{engine1.name}}}}}"
            rf"{{\max( \text{{SNR}}_{{{engine1.name}}}, \text{{SNR}}_{{{engine2.name}}} )}}$"
    )
    add_points(ax, x=alphas, y=beta_over_Hs, labels=labels, titles=titles)
    return fig
