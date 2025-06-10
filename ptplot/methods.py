import typing as tp

from django.http import Http404, HttpResponse
from django.db.models import Model as DjangoModel
from matplotlib.figure import Figure

from ptplot.science.plot_utils import fig_to_svg


def fig_to_response(fig: Figure) -> HttpResponse:
    return HttpResponse(fig_to_svg(fig), content_type="image/svg+xml")


def get_object_or_404_related(
        model: tp.Type[DjangoModel],
        related: tp.List[str] = None,
        prefetch: tp.List[str] = None,
        **kwargs):
    try:
        obj = model.objects
        if related is not None:
            obj = obj.select_related(*related)
        if prefetch is not None:
            obj = obj.prefetch_related(*prefetch)
        obj = obj.get(**kwargs)
    except model.DoesNotExist:
        raise Http404(f"No {model._meta.object_name} matches the given query.")
    return obj
