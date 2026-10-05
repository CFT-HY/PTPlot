"""Statistics of the numerical fields of the database models."""

from collections import defaultdict
from dataclasses import dataclass
import statistics
import typing as tp

from django.db.models import Avg, Count, Max, Min, Q

if tp.TYPE_CHECKING:
    from django.db.models import Aggregate, Field, Model, QuerySet

#: Fields of :py:class:`ptplot.models.model.Model` for which statistics are computed
MODEL_STATS_FIELDS: tuple[str, ...] = ("T_star", "g_star", "v_wall")
#: Fields of :py:class:`ptplot.models.scenario.Scenario` for which statistics are computed
SCENARIO_STATS_FIELDS: tuple[str, ...] = ("T_star", )
#: Fields of :py:class:`ptplot.models.parameter_choice.ParameterChoice` for which statistics are computed
POINT_STATS_FIELDS: tuple[str, ...] = ("alpha", "beta_tilde", "v_wall", "T_star", "g_star")


@dataclass(frozen=True, slots=True)
class FieldStats:
    """Statistics of a numerical field over a set of objects."""

    #: Name of the field
    field: str
    #: Human-readable name of the field
    name: str
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


def _aggregations(fields: tp.Iterable[str]) -> "dict[str, Aggregate]":
    """Get the aggregations that can be computed by the database.

    Django doesn't provide a median aggregation, and SQLite doesn't support one,
    so the median is computed separately in Python.
    """
    aggregations: dict[str, Aggregate] = {"n": Count("pk")}
    for field in fields:
        aggregations[f"{field}__count"] = Count(field)
        aggregations[f"{field}__min"] = Min(field)
        aggregations[f"{field}__max"] = Max(field)
        aggregations[f"{field}__avg"] = Avg(field)
    return aggregations


def _medians(
        queryset: "QuerySet[tp.Any]",
        fields: tp.Sequence[str],
        group_by: str | None = None) -> dict[tp.Any, dict[str, float | None]]:
    """Compute the medians of the fields in Python, as they are not available as database aggregations.

    All the values are fetched with a single query.
    """
    columns = fields if group_by is None else (group_by, *fields)
    values: defaultdict[tp.Any, dict[str, list[float]]] = defaultdict(lambda: {field: [] for field in fields})
    for row in queryset.order_by().values_list(*columns):
        group = None if group_by is None else row[0]
        group_values = values[group]
        for field, value in zip(fields, row if group_by is None else row[1:], strict=True):
            if value is not None:
                group_values[field].append(value)
    return {
        group: {field: statistics.median(vals) if vals else None for field, vals in group_values.items()}
        for group, group_values in values.items()
    }


def _field_stats(
        model: "type[Model]",
        fields: tp.Sequence[str],
        aggregates: dict[str, tp.Any],
        medians: dict[str, float | None]) -> list[FieldStats]:
    """Create the statistics objects from the results of the aggregation."""
    stats = []
    for field in fields:
        # The statistics are computed for concrete fields, not for reverse relations.
        model_field = tp.cast("Field", model._meta.get_field(field))  # noqa: SLF001
        stats.append(FieldStats(
            field=field,
            name=str(model_field.verbose_name),
            nullable=model_field.null,
            n=aggregates["n"],
            n_set=aggregates[f"{field}__count"],
            minimum=aggregates[f"{field}__min"],
            maximum=aggregates[f"{field}__max"],
            mean=aggregates[f"{field}__avg"],
            median=medians.get(field)
        ))
    return stats


def field_stats(queryset: "QuerySet[tp.Any]", fields: tp.Sequence[str]) -> list[FieldStats]:
    """Compute the statistics of numerical fields over the objects of a queryset.

    :param queryset: Objects over which the statistics are computed
    :param fields: Names of the numerical fields
    :return: Statistics of each field
    """
    aggregates = queryset.aggregate(**_aggregations(fields))
    medians = _medians(queryset, fields).get(None, {})
    return _field_stats(queryset.model, fields, aggregates, medians)


def field_stats_by(
        queryset: "QuerySet[tp.Any]",
        group_by: str,
        fields: tp.Sequence[str]) -> dict[tp.Any, list[FieldStats]]:
    """Compute the statistics of numerical fields over the objects of a queryset for each group.

    :param queryset: Objects over which the statistics are computed
    :param group_by: Name of the field by which the objects are grouped, e.g. a foreign key
    :param fields: Names of the numerical fields
    :return: Statistics of each field by the value of the grouping field
    """
    rows = queryset.order_by(group_by).values(group_by).annotate(**_aggregations(fields))
    medians = _medians(queryset, fields, group_by=group_by)
    return {
        row[group_by]: _field_stats(queryset.model, fields, row, medians.get(row[group_by], {}))
        for row in rows
    }


def bool_stats(queryset: "QuerySet[tp.Any]", field: str) -> BoolStats:
    """Count how many of the objects of a queryset have a boolean field set to true.

    :param queryset: Objects to count
    :param field: Name of the boolean field
    :return: Statistics of the field
    """
    aggregates = queryset.aggregate(n=Count("pk"), n_true=Count("pk", filter=Q(**{field: True})))
    return BoolStats(
        field=field,
        name=str(tp.cast("Field", queryset.model._meta.get_field(field)).verbose_name),  # noqa: SLF001
        n=aggregates["n"],
        n_true=aggregates["n_true"]
    )
