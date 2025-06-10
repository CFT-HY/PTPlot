import io
import math
import typing as tp

from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np


def create_ticks(
        ax: Axes,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        xtickpos: np.ndarray = None,
        ytickpos: np.ndarray = None,
        xticklabels: tp.List[str] = None,
        yticklabels: tp.List[str] = None) -> None:
    x_min_int = int(math.ceil(x_min))
    x_max_int = int(math.floor(x_max))
    y_min_int = int(math.ceil(y_min))
    y_max_int = int(math.floor(y_max))

    if xtickpos is None:
        xtickpos = list(range(x_min_int, x_max_int + 1))
    if xticklabels is None:
        xticklabels = [r"$10^{%d}$" % ind for ind in xtickpos]
    if ytickpos is None:
        ytickpos = list(range(y_min_int, y_max_int + 1))
    if yticklabels is None:
        yticklabels = [r"$10^{%d}$" % ind for ind in ytickpos]
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


def find_label_place(
        x: np.ndarray,
        y: np.ndarray,
        snr: np.ndarray,
        wanted_y: float,
        wanted_contour: float) -> tp.Tuple[float, float]:
    """Determines where to put contour label, based on y-coordinate and contour value"""
    nearest_y = np.abs(y - wanted_y).argmin()
    nearest_x = (np.abs(snr[nearest_y, :] - wanted_contour)).argmin()
    return x[nearest_x], wanted_y


def make_minor_ticks(min: int, max: int) -> np.ndarray:
    ticks = np.array([])
    for i in range(min, max):
        ticks = np.append(ticks, np.linspace(10 ** i, 10 ** (i + 1), 9, endpoint=False))
    return np.log10(ticks)


def fig_to_svg(fig: Figure) -> bytes:
    with io.BytesIO() as buffer:
        fig.savefig(buffer, format="svg")
        return buffer.getvalue()
