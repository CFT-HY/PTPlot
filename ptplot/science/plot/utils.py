"""Plotting utilities"""

from datetime import datetime
import io
import math

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text
import numpy as np

import ptplot.science.type_hints as th
from ptplot.science.utils import GIT_DESCRIPTION


def add_text(
        fig: Figure,
        text: str,
        x: float = 0.13,
        y: float = 0.87,
        fontsize: int = 8,
        color: str = "black",
        ha: str = "left",
        va: str = "top",
        alpha: float = 1.0) -> Text:
    """Add text to the given figure"""
    return fig.text(x=x, y=y, s=text, fontsize=fontsize, color=color, ha=ha, va=va, alpha=alpha)


def add_ticks(
        ax: Axes,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        xtickpos: th.FloatArr1D | None = None,
        ytickpos: th.FloatArr1D | None = None,
        xticklabels: list[str] | None = None,
        yticklabels: list[str] | None = None) -> None:
    """Add ticks to the given axes"""
    x_min_int = int(math.ceil(x_min))
    x_max_int = int(math.floor(x_max))
    y_min_int = int(math.ceil(y_min))
    y_max_int = int(math.floor(y_max))

    if xtickpos is None:
        xtickpos = range(x_min_int, x_max_int + 1)
    if xticklabels is None:
        xticklabels = tick_labels_log(xtickpos)
    if ytickpos is None:
        ytickpos = range(y_min_int, y_max_int + 1)
    if yticklabels is None:
        yticklabels = tick_labels_log(ytickpos)
    ax.set_xticks(xtickpos)
    ax.set_xticklabels(xticklabels)
    ax.set_xticks(
        ticks=make_minor_ticks(x_min_int, x_max_int),
        minor=True
    )
    ax.set_yticks(ytickpos)
    ax.set_yticklabels(yticklabels)
    ax.set_yticks(
        ticks=make_minor_ticks(y_min_int, y_max_int),
        minor=True
    )


def fig_to_svg(fig: Figure) -> bytes:
    """Convert a Figure to an SVG"""
    with io.BytesIO() as buffer:
        fig.savefig(buffer, format="svg")
        return buffer.getvalue()


def find_label_place(
        x: th.FloatArr1D,
        y: th.FloatArr1D,
        snr: th.FloatArr2D,
        wanted_y: float,
        wanted_contour: float) -> tuple[float, float]:
    """Determines where to put contour label, based on y-coordinate and contour value"""
    nearest_y = np.abs(y - wanted_y).argmin()
    nearest_x = (np.abs(snr[nearest_y, :] - wanted_contour)).argmin()
    return x[nearest_x].item(), wanted_y


def make_minor_ticks(min_int: int, max_int: int) -> np.ndarray:
    """Create minor ticks in the given range"""
    # Todo: This may be possible with one call of np.logspace
    return np.concatenate([
        np.log10(np.linspace(10 ** i, 10 ** (i + 1), 9, endpoint=False))
        for i in range(min_int, max_int)
    ])


def tick_labels_log(pos: th.FloatArr1D) -> list[str]:
    """Create tick labels for a logarithmic axis"""
    return [
            "1" if np.isclose(x, 0)
            else "10" if np.isclose(x, 1)
            else rf"$10^{{{x:d}}}$"
            for x in pos
        ]


def watermark() -> str:
    """Get the watermark string"""
    return f"PTPlot {GIT_DESCRIPTION}, {datetime.now().isoformat(sep=" ", timespec="seconds")}"
