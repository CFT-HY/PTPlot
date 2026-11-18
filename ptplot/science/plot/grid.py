r"""Plotting of quantities on the $(v_{\text{wall}}, \alpha_n)$ grid."""

from collections.abc import Sequence

from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np
from pttools.bubble.chapman_jouguet import v_chapman_jouguet_bag
from pttools.plot.lock import matplotlib_lock

from ptplot.science.spectrum.gh21dbpl import GH21dbplParams
import ptplot.science.type_hints as th

__all__ = ["gh21dbpl_params_figure", "v_wall_alpha_n_contours"]


@matplotlib_lock
def gh21dbpl_params_figure(params: GH21dbplParams) -> Figure:
    r"""Plot the spectral parameters of :py:class:`ptplot.science.spectrum.gh21dbpl.GH21dbpl`.

    The panels are $\Omega_{p,0}$, $f_{p,0}$, $r_b$ and $b$
    with the contour levels of :gowling_2021:`\ ` fig. 3.

    :param params: The spectral parameters on the $(v_{\text{wall}}, \alpha_n)$ grid
    :return: The 2x2 figure
    """
    panels: tuple[tuple[th.FloatArr2D, Sequence[float] | th.FloatArr1D, str, str], ...] = (
        (np.log10(params.omega_p0), np.arange(-16., -8.), r"$\log_{10} \Omega_{p,0}$", "plasma_r"),
        (1e3 * params.f_p0, [0.01, 0.05, 0.1, 0.2, 0.5, 0.7, 1, 2, 5], r"$f_{p,0}$ [mHz]", "plasma"),
        (params.rb, np.arange(0.01, 1.1, 0.1), r"$r_b$", "plasma"),
        (params.b, np.arange(-0.8, 1.7, 0.3), r"$b$", "plasma"),
    )
    fig = Figure(figsize=(10, 8))
    axs = fig.subplots(2, 2, sharex=True, sharey=True)
    for ax, (values, levels, label, cmap) in zip(axs.flat, panels, strict=True):
        v_wall_alpha_n_contours(
            fig, ax, v_walls=params.v_walls, alpha_ns=params.alpha_ns,
            values=values, levels=levels, label=label, cmap=cmap
        )
    for ax in axs[0, :]:
        ax.set_xlabel("")
    for ax in axs[:, 1]:
        ax.set_ylabel("")
    fig.suptitle(
        rf"GH21dbpl fit to the SSM, $r_*={params.r_star:g}$, "
        rf"$T_*={params.T_star:g}$ GeV, $g_*={params.g_star:g}$"
    )
    fig.tight_layout()
    return fig


def v_wall_alpha_n_contours(
        fig: Figure,
        ax: Axes,
        v_walls: th.FloatArr1D,
        alpha_ns: th.FloatArr1D,
        values: th.FloatArr2D,
        levels: Sequence[float] | th.FloatArr1D,
        label: str,
        cmap: str = "plasma",
        v_cj: bool = True) -> None:
    r"""Plot filled contours of a quantity on the $(v_{\text{wall}}, \alpha_n)$ plane with a colorbar.

    :param fig: Figure of the axes, for the colorbar
    :param ax: Axes to plot on
    :param v_walls: $v_{\text{wall}}$, wall speeds
    :param alpha_ns: $\alpha_n$, transition strengths
    :param values: Values of the quantity, indexed as ``[alpha_n, v_wall]``
    :param levels: Contour levels
    :param label: Label of the colorbar
    :param cmap: Name of the colormap, of which the range from 0.1 to 0.8 is used
    :param v_cj: Plot the Chapman-Jouguet speed $v_{\text{CJ}}(\alpha_n)$ of the bag model as a dashed line,
        :gowling_2021:`\ ` eq. 2.4
    """
    colors = colormaps[cmap](np.linspace(0.1, 0.8, len(levels)))
    contours = ax.contourf(v_walls, alpha_ns, values, levels=levels, colors=colors, extend="both")
    cbar = fig.colorbar(contours, ax=ax, ticks=levels)
    cbar.ax.set_yticklabels([f"{level:.3g}" for level in levels])
    cbar.set_label(label)
    if v_cj:
        ax.plot(v_chapman_jouguet_bag(alpha_plus=alpha_ns), alpha_ns, "--", color="darkturquoise")
    ax.set_xlim(v_walls[0], v_walls[-1])
    ax.set_ylim(alpha_ns[0], alpha_ns[-1])
    ax.set_xlabel(r"$v_{\text{wall}}$")
    ax.set_ylabel(r"$\alpha_n$")
    ax.grid(True, which="both", alpha=0.5)
