"""Generic utility methods."""

import os
from pathlib import Path
from threading import Lock
import typing as tp

import django
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model, Prefetch
from django.http import Http404, HttpResponse
from matplotlib.figure import Figure
from pttools.logging import setup_logging as pttools_logging

from ptplot import PTPLOT_DIR
from ptplot.science.plot.utils import fig_to_svg

#: Lock for setting up Django only once.
DJANGO_SETUP_LOCK: Lock = Lock()


def _default_log_dir() -> Path:
    """Get the default log directory, which is ``logs`` in the repository."""
    repo_dir = PTPLOT_DIR.parent
    if not (repo_dir / "examples").is_dir():
        raise ValueError("log_dir must be specified when PTPlot is not installed with \"git clone\".")
    return repo_dir / "logs"


def fig_to_response(fig: Figure) -> HttpResponse:
    """Convert a Matplotlib figure to an SVG HttpResponse."""
    return HttpResponse(fig_to_svg(fig), content_type="image/svg+xml")


def get_object_or_404_related[T: Model](
        model: type[T],
        annotate: dict[str, tp.Any] | None = None,
        related: list[str] | None = None,
        prefetch: list[str | Prefetch] | None = None,
        **kwargs: tp.Any) -> T:
    """Get an object with related objects, or a 404 error."""
    try:
        queryset = model._default_manager.get_queryset()  # noqa: SLF001
        if related is not None:
            queryset = queryset.select_related(*related)
        if prefetch is not None:
            queryset = queryset.prefetch_related(*prefetch)
        if annotate is not None:
            queryset = queryset.annotate(**annotate)
        obj = queryset.get(**kwargs)
    except ObjectDoesNotExist as err:
        raise Http404(f"No {model._meta.object_name} matches the given query.") from err  # noqa: SLF001
    return obj


def setup_django(log_dir: str | os.PathLike[str] | None = None, settings: str = "ptplot_site.settings.dev") -> None:
    """Configure Django for use in a script."""
    if not DJANGO_SETUP_LOCK.acquire(blocking=False):
        return

    if log_dir is None:
        log_dir = _default_log_dir()
    setup_logging(log_dir=log_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)
    django.setup()


def setup_example_logging(gallery_conf: dict[str, tp.Any], fname: str | None) -> None:  # noqa: ARG001
    """Ensure that logging is configured before running an example.

    This is a resetter for the ``reset_modules`` option of Sphinx-Gallery, which is called before each example.
    With the ``parallel`` option, the examples are run in worker processes,
    which do not inherit the logging configuration of the main process.
    If an example configured the logging itself, the console handler would be attached to the stream
    with which Sphinx-Gallery captures the output of the example,
    and which forwards the output to the ``sphinx`` logger.
    In the worker processes the ``sphinx`` logger propagates to the root logger, as Sphinx has not configured it there,
    and this would result in an infinite recursion.
    Configuring the logging here, before Sphinx-Gallery captures the output, prevents this.
    """
    setup_logging(log_dir=_default_log_dir())


def setup_logging(name: str = "ptplot", log_dir: str | os.PathLike[str] | None = None) -> None:
    """Configure logging."""
    pttools_logging(name=name, log_dir=log_dir)
