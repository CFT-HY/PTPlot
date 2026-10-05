"""Generic utility methods."""

import os
import typing as tp

import django
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model, Prefetch
from django.http import Http404, HttpResponse
from matplotlib.figure import Figure
from pttools.logging import setup_logging as pttools_logging

from ptplot import PTPLOT_DIR
from ptplot.science.plot.utils import fig_to_svg


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
    if log_dir is None:
        repo_dir = PTPLOT_DIR.parent
        if not (repo_dir / "examples").is_dir():
            raise ValueError("log_dir must be specified when PTPlot is not installed with \"git clone\".")
        log_dir = repo_dir / "logs"
    pttools_logging(name="ptplot", log_dir=log_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)
    django.setup()
