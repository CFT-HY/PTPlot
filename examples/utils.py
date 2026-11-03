"""Utilities for PTPlot examples"""

import contextlib
import logging
import os
from pathlib import Path
import typing as tp

from django.http import HttpResponse
from matplotlib.figure import Figure
import pttools.plot.utils as plot_utils
from pttools.plot.utils import FIG_FORMATS
from pttools.utils.docstrings import copy_docstring_dec
from pttools.utils.exceptions import log_exceptions

from ptplot.science.plot.snr_histogram import snr_histogram_figure
from ptplot.science.plot.utils import save_html

if tp.TYPE_CHECKING:
    import numpy as np

    from ptplot.models import Model
    from ptplot.science.snr.grid import SNRGrid
    from ptplot.science.spectrum import Engine

logger: logging.Logger = logging.getLogger(__name__)

EXAMPLES_DIR: Path = Path(__file__).resolve().parent
PROJECT_DIR: Path = EXAMPLES_DIR.parent
#: The figure directory, which can be changed with the ``PTPLOT_FIG_DIR`` environment variable,
#: e.g. by the nightly run ``pttools.docs.nightly`` of PTtools
FIG_DIR: Path = Path(os.environ.get("PTPLOT_FIG_DIR") or EXAMPLES_DIR / "fig").resolve()
LOG_DIR: Path = PROJECT_DIR / "logs"
FIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def csv_path(path: str | os.PathLike[str], fig_dir: str | os.PathLike[str] = FIG_DIR) -> Path:
    """Path of a CSV file of a figure as ``FIG_DIR/csv/PATH.csv``, i.e. with the same structure as the figures.

    :param path: Path of the figure within the directory of each format, without the suffix
    :param fig_dir: Figure directory
    :return: Path of the CSV file
    """
    path = Path(fig_dir) / "csv" / path
    return path.with_name(f"{path.name}.csv")


def model_csv_path(
        model: "Model",
        name: str,
        fig_dir: str | os.PathLike[str] = FIG_DIR,
        subdir: str | None = None) -> Path:
    """Path of a CSV file of a figure of a model as ``FIG_DIR/csv/SUBDIR/SLUG_NAME.csv``, see :py:func:`save_model_fig`.

    :param model: Model of the figure
    :param name: Name of the figure
    :param fig_dir: Figure directory
    :param subdir: Subdirectory within the CSV directory, defaults to the slug of the model
    :return: Path of the CSV file
    """
    return csv_path(Path(model.slug if subdir is None else subdir) / f"{model.slug}_{name}", fig_dir=fig_dir)


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
        subdir: str | None = None) -> None:
    """Save a figure of a model as ``FIG_DIR/FORMAT/SUBDIR/SLUG_NAME.FORMAT``.

    :param fig: Figure to save
    :param model: Model of the figure
    :param name: Name of the figure
    :param fig_dir: Figure directory
    :param subdir: Subdirectory within the directory of each format, defaults to the slug of the model
    """
    save_fig(fig, Path(model.slug if subdir is None else subdir) / f"{model.slug}_{name}", fig_dir=fig_dir)


def save_model_html(
        html: str,
        model: "Model",
        name: str,
        fig_dir: str | os.PathLike[str] = FIG_DIR,
        subdir: str | None = None) -> Path:
    """Save an HTML figure of a model as ``FIG_DIR/html/SUBDIR/SLUG_NAME.html``.

    :param html: HTML of the figure, e.g. from :py:meth:`ptplot.science.plot.snr.SNRFigure.plotly_html`
    :param model: Model of the figure
    :param name: Name of the figure
    :param fig_dir: Figure directory
    :param subdir: Subdirectory within the directory of the HTML files, defaults to the slug of the model
    :return: Path of the saved file
    """
    html_dir = Path(fig_dir) / "html" / (model.slug if subdir is None else subdir)
    return save_html(html, html_dir / f"{model.slug}_{name}.html")


def save_snr_figures(
        model: "Model",
        grid: "SNRGrid",
        name: str,
        fig_dir: str | os.PathLike[str] = FIG_DIR,
        subdir: str | None = None,
        highlights: dict[str, int] | None = None,
        log_errors: bool = False) -> None:
    """Save the SNR figures of a grid of a model, both unfilled and filled, and the interactive HTML figure.

    :param model: Model of the grid
    :param grid: SNR grid
    :param name: Name of the figures
    :param fig_dir: Figure directory
    :param subdir: Subdirectory within the directory of each format, defaults to the slug of the model
    :param highlights: Labels of the points to be highlighted, and their indices,
        see :py:class:`~ptplot.science.plot.snr.SNRFigure`
    :param log_errors: Whether to log the exceptions of each figure instead of raising them,
        so that a failure in one figure does not prevent saving the others,
        see :py:func:`pttools.utils.exceptions.log_exceptions`
    """
    def handler(fig_name: str) -> contextlib.AbstractContextManager[None]:
        if log_errors:
            return log_exceptions(logger, "Failed to save %s for %s", fig_name, model.name)
        return contextlib.nullcontext()

    with handler(name):
        save_model_fig(
            model.snr_figure(grid, highlights=highlights).matplotlib(), model, name, fig_dir=fig_dir, subdir=subdir
        )
    with handler(f"{name}_filled"):
        save_model_fig(
            model.snr_figure(grid, filled=True, highlights=highlights).matplotlib(), model, f"{name}_filled",
            fig_dir=fig_dir, subdir=subdir
        )
    with handler(f"{name} HTML"):
        save_model_html(
            model.snr_figure(grid, highlights=highlights).plotly_html(), model, name, fig_dir=fig_dir, subdir=subdir
        )


def save_svg_response(response: HttpResponse, path: str | os.PathLike[str]) -> None:
    """Save an SVG HttpResponse in a file"""
    path = Path(path)
    if not path.is_absolute():
        path = FIG_DIR / path
    if path.suffix != ".svg":
        path = path.with_name(f"{path.name}.svg")
    path.write_bytes(response.content)


def snr_histograms(snr: "np.ndarray", engines: list["Engine"]) -> dict[str, Figure]:
    """Draw the SNR histograms of precomputed SNR values with all the valid points of each engine,
    and with only the points for which all the engines produced a valid SNR,
    see :py:func:`ptplot.science.plot.snr_histogram.snr_histogram_figure`.

    :param snr: SNR values [point, engine], e.g. from :py:meth:`ptplot.models.model.Model.snr_points`
    :param engines: Engines of the SNR values
    :return: Histograms by name: ``snr_histogram`` and ``snr_histogram_common``
    """
    return {
        "snr_histogram": snr_histogram_figure(snr, engines),
        "snr_histogram_common": snr_histogram_figure(snr, engines, common_only=True),
    }
