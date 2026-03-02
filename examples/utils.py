"""Utilities for PTPlot examples"""

import os

import django
from django.http import HttpResponse
from matplotlib.figure import Figure
from pttools.logging import setup_logging as pttools_logging

EXAMPLES_DIR: str = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR: str = os.path.dirname(EXAMPLES_DIR)
FIG_DIR: str = os.path.join(EXAMPLES_DIR, "fig")
LOG_DIR: str = os.path.join(PROJECT_DIR, "logs")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def save(fig: Figure, path: str, **kwargs):
    """Save a figure in the examples figure directory"""
    has_extension = "." in path
    if not os.path.isabs(path):
        path = os.path.join(FIG_DIR, path)
    if has_extension:
        fig.savefig(path, **kwargs)
    else:
        for ext in ["eps", "pdf", "png", "svg"]:
            fig.savefig(f"{path}.{ext}", **kwargs)


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
    # Todo: add name="ptplot" when it's supported by PTtools
    pttools_logging(log_dir=LOG_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ptplot_site.settings.dev")
    django.setup()
