"""Utilities for PTPlot examples"""

import os
from pathlib import Path
import typing as tp

from django.http import HttpResponse
from matplotlib.figure import Figure
import pttools.analysis.utils as plot_utils
from pttools.analysis.utils import FIG_FORMATS

EXAMPLES_DIR: Path = Path(__file__).resolve().parent
PROJECT_DIR: Path = EXAMPLES_DIR.parent
FIG_DIR: Path = EXAMPLES_DIR / "fig"
LOG_DIR: Path = PROJECT_DIR / "logs"
FIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def save_fig(
        fig: Figure,
        path: str | os.PathLike[str],
        fig_dir: str | os.PathLike[str] | None = FIG_DIR,
        formats: tp.Iterable[str] = FIG_FORMATS,
        makedirs: bool = True,
        **kwargs: tp.Any) -> None:
    """Save a figure in the figure directory of the examples."""
    plot_utils.save_fig(fig=fig, path=path, fig_dir=fig_dir, formats=formats, makedirs=makedirs, **kwargs)


def save_svg_response(response: HttpResponse, path: str | os.PathLike[str]) -> None:
    """Save an SVG HttpResponse in a file"""
    path = Path(path)
    if not path.is_absolute():
        path = FIG_DIR / path
    if path.suffix != ".svg":
        path = path.with_name(f"{path.name}.svg")
    path.write_bytes(response.content)
