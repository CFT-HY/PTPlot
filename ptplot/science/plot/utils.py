"""Plotting utilities."""

from datetime import datetime
import io

from matplotlib.figure import Figure
from matplotlib.text import Text
import numpy as np

from ptplot.science.plot.lock import matplotlib_lock
import ptplot.science.type_hints as th
from ptplot.science.utils import GIT_DESCRIPTION


def add_text(
        fig: Figure,
        text: str,
        x: float = 0.13,
        y: float = 0.96,
        fontsize: int = 8,
        color: str = "black",
        ha: str = "left",
        va: str = "top",
        alpha: float = 1.0) -> Text:
    """Add text to the given figure."""
    # Suitable defaults when not using tight_layout(): x=0.13, y=0.87
    return fig.text(x=x, y=y, s=text, fontsize=fontsize, color=color, ha=ha, va=va, alpha=alpha)


@matplotlib_lock
def fig_to_svg(fig: Figure) -> bytes:
    """Convert a Figure to an SVG."""
    with io.BytesIO() as buffer:
        fig.savefig(buffer, format="svg")
        return buffer.getvalue()


def find_label_place(
        x: th.FloatArr1D,
        y: th.FloatArr1D,
        snr: th.FloatArr2D,
        wanted_y: float,
        wanted_contour: float) -> tuple[float, float]:
    """Determine where to put contour label, based on y-coordinate and contour value."""
    nearest_y = np.abs(y - wanted_y).argmin()
    nearest_x = (np.abs(snr[nearest_y, :] - wanted_contour)).argmin()
    return x[nearest_x].item(), wanted_y


def watermark() -> str:
    """Get the watermark string."""
    return f"PTPlot {GIT_DESCRIPTION}, {datetime.now().isoformat(sep=" ", timespec="seconds")}"
