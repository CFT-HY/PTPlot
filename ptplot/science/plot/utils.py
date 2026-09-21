"""Plotting utilities."""

from datetime import datetime
import io
import typing as tp

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Annotation
import numpy as np

from ptplot.science.plot.lock import matplotlib_lock
import ptplot.science.type_hints as th
from ptplot.science.utils import GIT_DESCRIPTION

#: Points per inch, as used by Matplotlib font sizes.
POINTS_PER_INCH: float = 72
#: Default padding around the text of :func:`add_text`, in points.
TEXT_PAD: float = 3


@matplotlib_lock
def add_text(
        fig_or_ax: Figure | Axes,
        text: str,
        fontsize: int = 8,
        color: str = "black",
        alpha: float = 1.0,
        pad: float = TEXT_PAD) -> Annotation:
    """Add text above the top left corner of the plot area, and lay out the figure to make room for it.

    The text is anchored to the top left corner of the axes,
    so that its position doesn't depend on the layout of the overall figure.

    :func:`matplotlib.figure.Figure.tight_layout` doesn't take the text into account,
    since the text is excluded from the layout to keep it from resizing the axes.
    Therefore, the room for the text is reserved by laying out the axes within a rect
    that leaves the top of the figure free.

    :param fig_or_ax: Axes to add the text to, or a figure, in which case its first axes is used
    :param text: Text to add
    :param fontsize: Font size of the text in points
    :param color: Color of the text
    :param alpha: Opacity of the text
    :param pad: Padding around the text in points
    :return: The created text
    """
    fig: Figure
    ax: Axes
    if isinstance(fig_or_ax, Figure):
        axes = fig_or_ax.get_axes()
        if not axes:
            raise ValueError("The figure has no axes to add the text to.")
        fig = fig_or_ax
        ax = axes[0]
    else:
        ax = fig_or_ax
        # An axes always belongs to a figure.
        fig = tp.cast(Figure, ax.get_figure(root=True))

    txt = ax.annotate(
        text,
        xy=(0, 1), xycoords="axes fraction",
        xytext=(0, pad), textcoords="offset points",
        fontsize=fontsize, color=color, alpha=alpha, ha="left", va="bottom",
        # The text is outside the axes, so it must not be clipped to them,
        # and it must be excluded from the layout so that it doesn't resize them.
        annotation_clip=False, in_layout=False
    )
    # The height of the text has to be measured, since it depends on the font and the characters of the text.
    text_height = txt.get_window_extent().transformed(fig.transFigure.inverted()).height

    # Lay out the axes so that they and the text fit in the figure.
    # The text is above the axes, so the room needed above them is the padding, the text and the padding again.
    pad_y = pad / (fig.get_figheight() * POINTS_PER_INCH)
    fig.tight_layout(rect=(0, 0, 1, 1 - (text_height + 2 * pad_y)))
    return txt


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
