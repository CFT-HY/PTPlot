"""Generic utility methods."""

from collections.abc import Iterator
import contextlib
import logging
import os
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


@contextlib.contextmanager
def log_exceptions(logger: logging.Logger, msg: str, *args: object) -> Iterator[None]:
    """Log the exceptions raised within the context instead of raising them.

    This is for long scripts, e.g. those that create many figures,
    which should continue with the rest of their work if a part of it fails.
    Only the subclasses of :py:class:`Exception` are caught, so e.g. :py:class:`KeyboardInterrupt` is not.

    :param logger: Logger to which the exceptions are logged
    :param msg: Message of the log entry, with ``%`` placeholders for the arguments
    :param args: Arguments of the message
    """
    try:
        yield
    except Exception:
        logger.exception(msg, *args)


def setup_django(log_dir: str | os.PathLike[str] | None = None, settings: str = "ptplot_site.settings.dev") -> None:
    """Configure Django for use in a script."""
    if not DJANGO_SETUP_LOCK.acquire(blocking=False):
        return

    if log_dir is None:
        repo_dir = PTPLOT_DIR.parent
        if not (repo_dir / "examples").is_dir():
            raise ValueError("log_dir must be specified when PTPlot is not installed with \"git clone\".")
        log_dir = repo_dir / "logs"
    setup_logging(log_dir=log_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)
    django.setup()


def setup_logging(name: str = "ptplot", log_dir: str | os.PathLike[str] | None = None) -> None:
    """Configure logging."""
    pttools_logging(name=name, log_dir=log_dir)
