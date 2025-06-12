import time
import typing as tp

from matplotlib import cm, rc_context
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np

from ptplot.science import const
from ptplot.science.plot_utils import add_text, add_ticks, find_label_place
import ptplot.science.type_hints as th

COLOR_TUPLE = cm.plasma_r(np.linspace(0.1, 1, 6))
LEVELS = np.array([1, 5, 10, 20, 50, 100])
LEVELS_TSH = np.array([0.001, 0.01, 0.1, 1, 10, 100])
LEVELS_TSH_HUGE_ALPHA = np.array([1e-7, 1e-6, 1e-5, 1e-4])


def create_snr_figure(
        x: np.ndarray,
        y: np.ndarray,
        xlabel: str,
        ylabel: str,
        titles: th.StrOrList,
        snr: np.ndarray,
        tshHn: np.ndarray,
        locs_tsh: np.ndarray,
        label_wanted_y: float,
        huge_alpha: bool = False,
        locs: np.ndarray = None,
        levels: np.ndarray = LEVELS,
        levels_tsh: np.ndarray = LEVELS_TSH,
        levels_tsh_huge_alpha: np.ndarray = LEVELS_TSH_HUGE_ALPHA,
        xtickpos: np.ndarray = None,
        ytickpos: np.ndarray = None,
        xticklabels: tp.List[str] = None,
        yticklabels: tp.List[str] = None,
        label_fontsize: int = const.DEFAULT_LABEL_FONTSIZE,
        contour_label_fontsize: int = 8) -> tp.Tuple[Figure, Axes]:
    with rc_context(const.DEFAULT_RC_CONTEXT):
        x_min = np.min(x)
        x_max = np.max(x)
        y_min = np.min(y)
        y_max = np.max(y)

        fig = Figure()
        ax = fig.add_subplot(111)

        extent = (x[0], x[-1], y[0], y[-1])
        CS = ax.contour(
            x, y, snr, levels,
            linewidths=1, colors=COLOR_TUPLE, extent=extent
        )
        CStsh = ax.contour(
            x, y, tshHn, levels_tsh,
            linewidths=1, linestyles="dashed", colors="k", extent=extent
        )

        if huge_alpha:
            ax.contour(
                x, y, tshHn, levels_tsh_huge_alpha,
                linewidths=1, linestyles="dashed", colors="k", extent=extent
            )

        # CSturb
        ax.contourf(
            x, y, tshHn, [0.0001, 1],
            colors="white", alpha=0.2, hatches="x", extent=extent
        )

        if locs is None:
            locs = [
                find_label_place(x=x, y=y, snr=snr, wanted_y=label_wanted_y, wanted_contour=wanted_contour)
                for wanted_contour in levels
            ]
        ax.clabel(CS, inline=1, fontsize=contour_label_fontsize, fmt="%.0f", manual=locs)
        ax.clabel(CStsh, inline=1, fontsize=contour_label_fontsize, fmt="%g", manual=locs_tsh)
        # ax.set_title(r"SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs")
        # ax.set_xlabel(r"$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $",fontsize=16)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel(xlabel, fontsize=label_fontsize)
        ax.set_ylabel(ylabel, fontsize=label_fontsize)

        if titles:
            ax.legend(titles, loc="lower left", framealpha=0.9)

        # July 2023: No longer watermark with LISACosWG
        # # position bottom right
        # fig.text(
        #     0.95, 0.05, "LISACosWG",
        #     fontsize=50, color="gray",
        #     ha="right", va="bottom", alpha=0.4
        # )

        add_ticks(
            ax,
            x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
            xtickpos=xtickpos, ytickpos=ytickpos,
            xticklabels=xticklabels, yticklabels=yticklabels
        )
        add_text(fig, time.asctime())
        return fig, ax
