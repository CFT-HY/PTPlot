"""Fluid velocity and enthalpy profiles of the bubbles of the Sound Shell Model (SSM)."""

import typing as tp

from matplotlib import rc_context
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np
from pttools.bubble import Bubble
from pttools.models import Model
from pttools.plot.bubbles import plot_bubbles_common, plot_bubbles_v

from ptplot.science import const
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.utils import POINTS_PER_INCH, TEXT_PAD, add_text, watermark
from ptplot.science.spectrum.create import ssm_model
from ptplot.science.spectrum.ssm import BAG


@matplotlib_lock
def bubble_figure(
        plot: tp.Callable[[Bubble, Figure, Axes], None],
        v_wall: float,
        alpha_n: float,
        model: Model = BAG,
        css2: float | None = None,
        csb2: float | None = None,
        title: str | None = None) -> Figure:
    r"""Plot a profile of the SSM bubble.

    The bubble is the same as that of :py:class:`ptplot.science.spectrum.ssm.PowerSpectrumSSM`,
    with the equation of state model of :py:func:`ptplot.science.spectrum.create.ssm_model`.
    If the bubble cannot be solved for the given parameters, the reason is shown in the figure instead.
    The wall is marked with a dashed line.

    :param plot: Function that plots the profile of the bubble to the axes
    :param v_wall: $v_\text{wall}$, wall velocity
    :param alpha_n: $\alpha_n$, transition strength at the nucleation temperature
    :param model: Equation of state model of PTtools
    :param css2: $c_{s,s}^2$, sound speed squared in the symmetric phase
    :param csb2: $c_{s,b}^2$, sound speed squared in the broken phase
    :param title: Title of the figure, which is drawn above the watermark
    :return: Bubble profile figure
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
            plot(bubble, fig, ax)
            ax.axvline(bubble.v_wall, color="k", linestyle="--", linewidth=1, label=r"$v_\mathrm{w}$")
            ax.set_xlabel(r"$\xi$", fontsize=const.DEFAULT_LABEL_FONTSIZE)
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


def bubble_v_figure(
        v_wall: float,
        alpha_n: float,
        model: Model = BAG,
        css2: float | None = None,
        csb2: float | None = None,
        title: str | None = None) -> Figure:
    r"""Plot the fluid velocity profile $v(\xi)$ of the SSM bubble.

    The parameters are those of :py:func:`bubble_figure`.

    :return: Fluid velocity profile figure
    """
    return bubble_figure(
        _plot_v, v_wall=v_wall, alpha_n=alpha_n, model=model, css2=css2, csb2=csb2, title=title)


def bubble_w_figure(
        v_wall: float,
        alpha_n: float,
        model: Model = BAG,
        css2: float | None = None,
        csb2: float | None = None,
        title: str | None = None) -> Figure:
    r"""Plot the enthalpy profile $w(\xi)/w_n$ of the SSM bubble.

    The enthalpy is normalised by the enthalpy at the nucleation temperature $w_n$,
    i.e. that of the fluid outside the bubble, since the absolute value depends on the normalisation of the model.
    The parameters are those of :py:func:`bubble_figure`.

    :return: Enthalpy profile figure
    """
    return bubble_figure(
        _plot_w, v_wall=v_wall, alpha_n=alpha_n, model=model, css2=css2, csb2=csb2, title=title)


def _plot_v(bubble: Bubble, fig: Figure, ax: Axes) -> None:
    r"""Plot the fluid velocity profile $v(\xi)$ of the bubble."""
    plot_bubbles_v([bubble], fig, ax, legend=False, label=r"$v(\xi)$")
    ax.set_ylabel(r"$v(\xi)$", fontsize=const.DEFAULT_LABEL_FONTSIZE)


def _plot_w(bubble: Bubble, fig: Figure, ax: Axes) -> None:
    r"""Plot the enthalpy profile $w(\xi)/w_n$ of the bubble."""
    ax.plot(bubble.xi, bubble.w / bubble.wn, label=r"$w(\xi)/w_n$")
    # This sets the same xi range and grid as for the velocity profile.
    plot_bubbles_common([bubble], fig, ax, legend=False)
    ax.set_ylabel(r"$w(\xi)/w_n$", fontsize=const.DEFAULT_LABEL_FONTSIZE)
