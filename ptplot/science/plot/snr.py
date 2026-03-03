"""Utilities that are common to various SNR plotting functions"""

from matplotlib import cm, rc_context
from matplotlib.axes import Axes
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
import numpy as np

from ptplot.science import const
from ptplot.science.plot.logarithmic import log_figure
from ptplot.science.plot.utils import add_text, find_label_place, watermark
from ptplot.science.spectrum import Engine
import ptplot.science.type_hints as th

COLOR_TUPLE = cm.plasma_r(np.linspace(0.1, 1, 6))
LEVELS = np.array([1, 5, 10, 20, 50, 100])
LEVELS_TSH = np.array([0.001, 0.01, 0.1, 1, 10, 100])
LEVELS_TSH_HUGE_ALPHA = np.array([1e-7, 1e-6, 1e-5, 1e-4])


def snr_figure(
        x: th.FloatArr1D,
        y: th.FloatArr1D,
        xlabel: str,
        ylabel: str,
        titles: th.StrOrList,
        snr: th.FloatArr2D,
        shock_times: th.FloatArr2D,
        label_wanted_y: float,
        engine: Engine,
        huge_alpha: bool = False,
        snr_label_locs: th.FloatArr1D | None = None,
        shock_label_locs: th.FloatArr2D | None = None,
        levels: th.FloatArr1D = LEVELS,
        levels_tsh: th.FloatArr1D = LEVELS_TSH,
        levels_tsh_huge_alpha: th.FloatArr1D = LEVELS_TSH_HUGE_ALPHA,
        xtickpos: th.FloatArr1D | None = None,
        ytickpos: th.FloatArr1D | None = None,
        xticklabels: list[str] | None = None,
        yticklabels: list[str] | None = None,
        label_fontsize: int = const.DEFAULT_LABEL_FONTSIZE,
        contour_label_fontsize: int = 8,
        filled: bool = False) -> tuple[Figure, Axes]:
    """Common code for creating SNR figures

    The x and y axes are linear instead of logarithmic so that the contour plot is created correctly.
    """
    with rc_context(const.DEFAULT_RC_CONTEXT):
        fig, ax, extent = log_figure(
            x=x, y=y,
            xlabel=xlabel, ylabel=ylabel,
            xtickpos=xtickpos, ytickpos=ytickpos,
            xticklabels=xticklabels, yticklabels=yticklabels,
            label_fontsize=label_fontsize
        )

        if filled:
            contour = ax.contourf(x, y, snr, extent=extent, norm=LogNorm())
            fig.colorbar(
                contour,
                ax=ax,
                label=rf"$\text{{SNR}}_{{{engine}}}$"
            )
        else:
            contour = ax.contour(
                x, y, snr, levels,
                linewidths=1, colors=COLOR_TUPLE, extent=extent
            )

        contour_shock = ax.contour(
            x, y, shock_times, levels_tsh,
            linewidths=1, linestyles="dashed", colors="k", extent=extent
        )

        if huge_alpha:
            ax.contour(
                x, y, shock_times, levels_tsh_huge_alpha,
                linewidths=1, linestyles="dashed", colors="k", extent=extent
            )

        # Greying out the area according to turbulence
        # TODO: Explain this better
        if not filled:
            contour_shock_hatch = ax.contourf(
                x, y, shock_times, [0.0001, 1],
                colors="none" if filled else "white",
                alpha=0.2, hatches="x", extent=extent
            )
            # contour_shock_hatch.set_edgecolor((0.3, 0.3, 0.3, 1))

        if snr_label_locs is None:
            snr_label_locs = [
                find_label_place(x=x, y=y, snr=snr, wanted_y=label_wanted_y, wanted_contour=wanted_contour)
                for wanted_contour in levels
            ]
        if shock_label_locs is None:
            locs_tsh_x = (x[-1] + x[0]) / 2
            shock_label_locs = [(locs_tsh_x, y) for y in range(int(y[0]), int(y[-1]) + 1)]
        if not filled:
            ax.clabel(contour, inline=1, fontsize=contour_label_fontsize, fmt="%.0f", manual=snr_label_locs)
        ax.clabel(contour_shock, inline=1, fontsize=contour_label_fontsize, fmt="%g", manual=shock_label_locs)
        # ax.set_title(r"SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs")
        # ax.set_xlabel(r"$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $",fontsize=16)

        # July 2023: No longer watermark with LISACosWG
        # # position bottom right
        # fig.text(
        #     0.95, 0.05, "LISACosWG",
        #     fontsize=50, color="gray",
        #     ha="right", va="bottom", alpha=0.4
        # )

        add_text(fig, watermark())
        fig.tight_layout()
        return fig, ax
