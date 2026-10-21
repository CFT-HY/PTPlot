"""Fluid velocity profiles of the bubbles of the Sound Shell Model (SSM)."""

from matplotlib import rc_context
from matplotlib.figure import Figure
import numpy as np
from pttools.bubble import Bubble
from pttools.models import Model
from pttools.plot.bubbles import plot_bubbles_v

from ptplot.science import const
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.utils import POINTS_PER_INCH, TEXT_PAD, add_text, watermark
from ptplot.science.spectrum.create import ssm_model
from ptplot.science.spectrum.ssm import BAG


@matplotlib_lock
def bubble_v_figure(
        v_wall: float,
        alpha_n: float,
        model: Model = BAG,
        css2: float | None = None,
        csb2: float | None = None,
        title: str | None = None) -> Figure:
    r"""Plot the fluid velocity profile $v(\xi)$ of the SSM bubble.

    The bubble is the same as that of :py:class:`ptplot.science.spectrum.ssm.PowerSpectrumSSM`,
    with the equation of state model of :py:func:`ptplot.science.spectrum.create.ssm_model`.
    If the bubble cannot be solved for the given parameters, the reason is shown in the figure instead.

    :param v_wall: $v_\text{wall}$, wall velocity
    :param alpha_n: $\alpha_n$, transition strength at the nucleation temperature
    :param model: Equation of state model of PTtools
    :param css2: $c_{s,s}^2$, sound speed squared in the symmetric phase
    :param csb2: $c_{s,b}^2$, sound speed squared in the broken phase
    :param title: Title of the figure, which is drawn above the watermark
    :return: Fluid velocity profile figure
    """
    with rc_context(const.DEFAULT_RC_CONTEXT):
        fig = Figure()
        ax = fig.add_subplot()

        bubble: Bubble | None = None
        error = ""
        try:
            bubble = Bubble(model=ssm_model(css2=css2, csb2=csb2, model=model), v_wall=v_wall, alpha_n=alpha_n)
            if bubble.solver_failed or not np.any(np.isfinite(bubble.v)):
                bubble = None
                error = "Solving the fluid shell failed."
        except ValueError as exc:
            error = f"Could not create the fluid shell:\n{exc}"

        if bubble is not None:
            plot_bubbles_v([bubble], fig, ax, legend=False, label=r"$v(\xi)$")
            ax.axvline(bubble.v_wall, color="k", linestyle="--", linewidth=1, label=r"$v_\mathrm{w}$")
            ax.set_xlabel(r"$\xi$", fontsize=const.DEFAULT_LABEL_FONTSIZE)
            ax.set_ylabel(r"$v(\xi)$", fontsize=const.DEFAULT_LABEL_FONTSIZE)
            ax.legend(loc="best")
        else:
            ax.text(0.5, 0.5, error, ha="center", va="center", wrap=True, transform=ax.transAxes)
            ax.set_axis_off()

        txt = add_text(fig, watermark())
        if title is not None:
            # The same layout as in power_spectrum_figure
            text_height = txt.get_window_extent().height * POINTS_PER_INCH / fig.dpi
            ax.set_title(title, pad=text_height + 2 * TEXT_PAD)
            fig.tight_layout()
    return fig
