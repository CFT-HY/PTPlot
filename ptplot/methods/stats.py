"""Statistics of the numerical fields of the database models.

The statistics are computed by annotating the querysets before they are fetched from the database,
so that no additional database queries are needed.

- The statistics over all the objects of a queryset are computed with window aggregations,
  which add the same values to every object.
  See :py:func:`window_stats_annotations` and :py:func:`window_stats`.
- The statistics of the related objects, e.g. the points of each model, are computed with correlated subqueries.
  If several relations, e.g. points and scenarios, were joined instead,
  there would be a row for each combination of the related objects, which would multiply the counts.
  See :py:func:`related_stats_annotations` and :py:func:`related_stats`.

Django doesn't provide a median aggregation, and SQLite doesn't support one,
so the medians are computed in Python from the fetched objects.
For the statistics of related objects, the related objects should therefore be prefetched.
"""

from dataclasses import dataclass
import statistics
import typing as tp

from django.db.models import Avg, Count, Max, Min, OuterRef, Q, Subquery, Window
from django.db.models.functions import Coalesce

if tp.TYPE_CHECKING:
    from django.db.models import Aggregate, ForeignObjectRel, Model
    from django.db.models.expressions import BaseExpression

#: Aggregations that are computed by the database for each field
AGGREGATIONS: dict[str, type[Avg | Count | Max | Min]] = {"count": Count, "min": Min, "max": Max, "avg": Avg}


class StatsModel(tp.Protocol):
    """A database model that defines the fields for which statistics are computed."""

    STATS_FIELDS: tp.ClassVar[tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class FieldStats:
    """Statistics of a numerical field over a set of objects."""

    #: Name of the field
    field: str
    #: Human-readable name of the field
    name: str
    #: Human-readable name of the field with LaTeX symbols
    name_latex: str
    #: Whether the field can be left unset
    nullable: bool
    #: Number of objects
    n: int
    #: Number of objects for which the field is set
    n_set: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None

    @property
    def values(self) -> str:
        """Number of values, and for nullable fields also the number of objects, as a string."""
        return f"{self.n_set} / {self.n}" if self.nullable else str(self.n)

    @property
    def minimum_str(self) -> str:
        """Minimum as a string."""
        return format_value(self.minimum)

    @property
    def maximum_str(self) -> str:
        """Maximum as a string."""
        return format_value(self.maximum)

    @property
    def mean_str(self) -> str:
        """Mean as a string."""
        return format_value(self.mean)

    @property
    def median_str(self) -> str:
        """Median as a string."""
        return format_value(self.median)


@dataclass(frozen=True, slots=True)
class BoolStats:
    """Statistics of a boolean field over a set of objects."""

    #: Name of the field
    field: str
    #: Human-readable name of the field
    name: str
    #: Number of objects
    n: int
    #: Number of objects for which the field is true
    n_true: int


def format_value(value: float | None) -> str:
    """Format a statistic with four significant digits, or as a dash if it's not available."""
    return "-" if value is None else f"{value:.4g}"


def count_name(prefix: str) -> str:
    """Get the name of the annotation for the number of objects."""
    return f"{prefix}__n"


def annotation_name(prefix: str, field: str, aggregation: str) -> str:
    """Get the name of the annotation for an aggregation of a field, e.g. ``points__alpha__min``."""
    return f"{prefix}__{field}__{aggregation}"


def stats_fields(model: "type[Model]") -> tuple[str, ...]:
    """Get the fields of a model for which statistics are computed."""
    return tp.cast("type[StatsModel]", model).STATS_FIELDS


# -----
# Annotations
# -----

def window_stats_annotations(
        model: "type[Model]",
        prefix: str = "all",
        bool_fields: tp.Iterable[str] = ()) -> "dict[str, BaseExpression]":
    """Get the annotations for the statistics over all the objects of a queryset.

    The annotations are computed after the filters of the queryset have been applied.

    :param model: Model whose ``STATS_FIELDS`` are aggregated
    :param prefix: Prefix of the names of the annotations
    :param bool_fields: Boolean fields for which the number of true values is counted
    :return: Annotations for :py:meth:`django.db.models.query.QuerySet.annotate`
    """
    annotations: dict[str, BaseExpression] = {count_name(prefix): Window(Count("pk"))}
    for field in stats_fields(model):
        for aggregation, func in AGGREGATIONS.items():
            annotations[annotation_name(prefix, field, aggregation)] = Window(func(field))
    for field in bool_fields:
        annotations[annotation_name(prefix, field, "true")] = Window(Count("pk", filter=Q(**{field: True})))
    return annotations


def related_stats_annotations(model: "type[Model]", relation: str) -> "dict[str, BaseExpression]":
    """Get the annotations for the statistics of the related objects.

    The names of the annotations are prefixed with the name of the relation, e.g. ``points__alpha__min``.

    :param model: Model to be annotated
    :param relation: Name of the reverse relation of a foreign key, e.g. ``points``.
        The ``STATS_FIELDS`` of the related model are aggregated.
    :return: Annotations for :py:meth:`django.db.models.query.QuerySet.annotate`
    """
    rel = tp.cast("ForeignObjectRel", model._meta.get_field(relation))  # noqa: SLF001
    related_model = tp.cast("type[Model]", rel.related_model)
    fk = rel.field.name
    related = related_model._default_manager.filter(**{fk: OuterRef("pk")}).order_by().values(fk)  # noqa: SLF001

    def subquery(aggregate: "Aggregate") -> "BaseExpression":
        query = Subquery(related.annotate(value=aggregate).values("value"))
        # There are no rows in the subquery if there are no related objects.
        return Coalesce(query, 0) if isinstance(aggregate, Count) else query

    annotations = {count_name(relation): subquery(Count("pk"))}
    for field in stats_fields(related_model):
        for aggregation, func in AGGREGATIONS.items():
            annotations[annotation_name(relation, field, aggregation)] = subquery(func(field))
    return annotations


# -----
# Statistics from the annotations
# -----

def annotated_stats(
        obj: "Model | None",
        prefix: str,
        model: "type[Model]",
        objects: "tp.Iterable[Model]") -> list[FieldStats]:
    """Get the statistics from the annotations of an object.

    :param obj: Object with the annotations, or None if there are no objects to compute the statistics of
    :param prefix: Prefix of the names of the annotations
    :param model: Model whose ``STATS_FIELDS`` were aggregated
    :param objects: Objects from which the medians are computed
    :return: Statistics of each field
    """
    objects = list(objects)
    stats = []
    for field in stats_fields(model):
        model_field = model._meta.get_field(field)  # noqa: SLF001
        name = str(getattr(model_field, "verbose_name", field))
        values = [value for value in (getattr(o, field) for o in objects) if value is not None]
        stats.append(FieldStats(
            field=field,
            name=name,
            name_latex=getattr(model_field, "verbose_name_latex", name),
            nullable=model_field.null,
            n=0 if obj is None else getattr(obj, count_name(prefix)),
            n_set=0 if obj is None else getattr(obj, annotation_name(prefix, field, "count")),
            minimum=None if obj is None else getattr(obj, annotation_name(prefix, field, "min")),
            maximum=None if obj is None else getattr(obj, annotation_name(prefix, field, "max")),
            mean=None if obj is None else getattr(obj, annotation_name(prefix, field, "avg")),
            median=statistics.median(values) if values else None
        ))
    return stats


def window_stats(model: "type[Model]", objects: "tp.Sequence[Model]", prefix: str = "all") -> list[FieldStats]:
    """Get the statistics over objects that were annotated with :py:func:`window_stats_annotations`.

    :param model: Model of the objects
    :param objects: Fetched objects of the annotated queryset
    :param prefix: Prefix of the names of the annotations
    :return: Statistics of each field
    """
    return annotated_stats(objects[0] if objects else None, prefix, model, objects)


def window_bool_stats(
        model: "type[Model]",
        objects: "tp.Sequence[Model]",
        field: str,
        prefix: str = "all") -> BoolStats:
    """Get the statistics of a boolean field over objects annotated with :py:func:`window_stats_annotations`.

    :param model: Model of the objects
    :param objects: Fetched objects of the annotated queryset
    :param field: Name of the boolean field
    :param prefix: Prefix of the names of the annotations
    :return: Statistics of the field
    """
    obj = objects[0] if objects else None
    return BoolStats(
        field=field,
        name=str(getattr(model._meta.get_field(field), "verbose_name", field)),  # noqa: SLF001
        n=0 if obj is None else getattr(obj, count_name(prefix)),
        n_true=0 if obj is None else getattr(obj, annotation_name(prefix, field, "true"))
    )


def related_stats(obj: "Model", relation: str) -> list[FieldStats]:
    """Get the statistics of the related objects of an object annotated with :py:func:`related_stats_annotations`.

    The related objects should be prefetched for the medians, as otherwise they are fetched with a separate query.

    :param obj: Annotated object
    :param relation: Name of the reverse relation, which must also be the prefix of the annotations
    :return: Statistics of each field
    """
    manager = getattr(obj, relation)
    return annotated_stats(obj, relation, manager.model, manager.all())
