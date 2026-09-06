"""Utilities for PTPlot examples"""

import os
import typing as tp

import django
from django.http import HttpResponse
from matplotlib.figure import Figure
import pttools.analysis.utils as plot_utils
from pttools.analysis.utils import FIG_FORMATS
from pttools.logging import setup_logging as pttools_logging

EXAMPLES_DIR: str = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR: str = os.path.dirname(EXAMPLES_DIR)
FIG_DIR: str = os.path.join(EXAMPLES_DIR, "fig")
LOG_DIR: str = os.path.join(PROJECT_DIR, "logs")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def save_fig(
        fig: Figure,
        path: str,
        fig_dir: str | None = FIG_DIR,
        formats: tp.Iterable[str] = FIG_FORMATS,
        makedirs: bool = True,
        **kwargs) -> None:
    """Save a figure in the figure directory of the examples."""
    plot_utils.save_fig(fig=fig, path=path, fig_dir=fig_dir, formats=formats, makedirs=makedirs, **kwargs)



def save_svg_response(response: HttpResponse, path: str):
    """Save an SVG HttpResponse in a file"""
    if not os.path.isabs(path):
        path = os.path.join(FIG_DIR, path)
    if not path.endswith(".svg"):
        path += ".svg"
    with open(path, "wb") as file:
        file.write(response.content)


def setup_django():
    """Configure Django for use in a script"""
    pttools_logging(name="ptplot", log_dir=LOG_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ptplot_site.settings.dev")
    django.setup()
