"""Generic utility methods."""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.http import Http404, HttpResponse
from matplotlib.figure import Figure

from ptplot.science.plot.utils import fig_to_svg


def fig_to_response(fig: Figure) -> HttpResponse:
    """Convert a Matplotlib figure to an SVG HttpResponse."""
    return HttpResponse(fig_to_svg(fig), content_type="image/svg+xml")


def get_object_or_404_related[T: Model](
        model: type[T],
        annotate: list | None = None,
        related: list[str] | None = None,
        prefetch: list[str] | None = None,
        **kwargs) -> T:
    """Get an object with related objects, or a 404 error."""
    try:
        queryset = model._default_manager.get_queryset()  # noqa: SLF001
        if related is not None:
            queryset = queryset.select_related(*related)
        if prefetch is not None:
            queryset = queryset.prefetch_related(*prefetch)
        if annotate is not None:
            queryset = queryset.annotate(*annotate)
        obj = queryset.get(**kwargs)
    except ObjectDoesNotExist as err:
        raise Http404(f"No {model._meta.object_name} matches the given query.") from err  # noqa: SLF001
    return obj
