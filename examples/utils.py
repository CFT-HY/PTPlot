"""Utilities for PTPlot examples"""

import os
from pathlib import Path
import typing as tp

from django.http import HttpResponse
from matplotlib.figure import Figure
import pttools.plot.utils as plot_utils
from pttools.plot.utils import FIG_FORMATS
from pttools.utils.docstrings import copy_docstring_dec

from ptplot.science.plot.utils import save_html

if tp.TYPE_CHECKING:
    from ptplot.models import Model

EXAMPLES_DIR: Path = Path(__file__).resolve().parent
PROJECT_DIR: Path = EXAMPLES_DIR.parent
#: The figure directory, which can be changed with the ``PTPLOT_FIG_DIR`` environment variable,
#: e.g. by the nightly run ``ptplot/nightly.py``
FIG_DIR: Path = Path(os.environ.get("PTPLOT_FIG_DIR") or EXAMPLES_DIR / "fig").resolve()
LOG_DIR: Path = PROJECT_DIR / "logs"
FIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


@copy_docstring_dec(plot_utils.save_and_show_fig)
def save_and_show_fig(
        fig: Figure,
        path: str | os.PathLike[str],
        fig_dir: str | os.PathLike[str] | None = FIG_DIR,
        formats: tp.Iterable[str] = FIG_FORMATS,
        makedirs: bool = True,
        **kwargs: tp.Any) -> None:
    plot_utils.save_and_show_fig(fig=fig, path=path, fig_dir=fig_dir, formats=formats, makedirs=makedirs, **kwargs)


@copy_docstring_dec(plot_utils.save_and_show_figs)
def save_and_show_figs(
        figs: dict[str, Figure],
        fig_dir: str | os.PathLike[str] | None = FIG_DIR,
        formats: tp.Iterable[str] = FIG_FORMATS,
        makedirs: bool = True,
        **kwargs: tp.Any) -> None:
    plot_utils.save_and_show_figs(figs=figs, fig_dir=fig_dir, formats=formats, makedirs=makedirs, **kwargs)


@copy_docstring_dec(plot_utils.save_fig)
def save_fig(
        fig: Figure,
        path: str | os.PathLike[str],
        fig_dir: str | os.PathLike[str] | None = FIG_DIR,
        formats: tp.Iterable[str] = FIG_FORMATS,
        makedirs: bool = True,
        **kwargs: tp.Any) -> None:
    plot_utils.save_fig(fig=fig, path=path, fig_dir=fig_dir, formats=formats, makedirs=makedirs, **kwargs)


@copy_docstring_dec(plot_utils.save_figs)
def save_figs(
        figs: dict[str, Figure],
        fig_dir: str | os.PathLike[str] | None = FIG_DIR,
        formats: tp.Iterable[str] = FIG_FORMATS,
        makedirs: bool = True,
        **kwargs: tp.Any) -> None:
    plot_utils.save_figs(figs=figs, fig_dir=fig_dir, formats=formats, makedirs=makedirs, **kwargs)


def save_model_fig(
        fig: Figure,
        model: "Model",
        name: str,
        fig_dir: str | os.PathLike[str] = FIG_DIR,
        model_dir: bool = True) -> None:
    """Save a figure of a model as ``FIG_DIR/FORMAT/SLUG/SLUG_NAME.FORMAT``.

    :param fig: Figure to save
    :param model: Model of the figure
    :param name: Name of the figure
    :param fig_dir: Figure directory
    :param model_dir: Whether to save the figure in a subdirectory of the model
    """
    path = Path(f"{model.slug}_{name}")
    save_fig(fig, Path(model.slug) / path if model_dir else path, fig_dir=fig_dir)


def save_model_html(
        html: str,
        model: "Model",
        name: str,
        fig_dir: str | os.PathLike[str] = FIG_DIR,
        model_dir: bool = True) -> Path:
    """Save an HTML figure of a model as ``FIG_DIR/html/SLUG/SLUG_NAME.html``.

    :param html: HTML of the figure, e.g. from :py:meth:`ptplot.science.plot.snr.SNRFigure.plotly_html`
    :param model: Model of the figure
    :param name: Name of the figure
    :param fig_dir: Figure directory
    :param model_dir: Whether to save the figure in a subdirectory of the model
    :return: Path of the saved file
    """
    html_dir = Path(fig_dir) / "html"
    if model_dir:
        html_dir /= model.slug
    return save_html(html, html_dir / f"{model.slug}_{name}.html")


def save_svg_response(response: HttpResponse, path: str | os.PathLike[str]) -> None:
    """Save an SVG HttpResponse in a file"""
    path = Path(path)
    if not path.is_absolute():
        path = FIG_DIR / path
    if path.suffix != ".svg":
        path = path.with_name(f"{path.name}.svg")
    path.write_bytes(response.content)
