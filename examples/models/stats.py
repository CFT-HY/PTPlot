"""
Model statistics
================

Print statistics of the models, scenarios and points in the database.

The querysets are annotated with the statistics before they are fetched,
so that the statistics are computed by the database in the same queries that fetch the objects.
The minimum, maximum, mean and the number of values over all the objects of a queryset
are computed with window aggregations, and those of the related objects with subqueries.
The median is computed in Python from the fetched objects, as there is no median aggregation for SQLite.
For the fields that can be left unset, the number of objects for which they are set is also shown.
See :py:mod:`ptplot.methods.stats` for details.
"""

from django.db.models import Prefetch
from pandas import DataFrame

from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.methods import FieldStats, related_stats, window_bool_stats, window_stats
from ptplot.models import Model, ParameterChoice, Scenario


def stats_table(stats: list[FieldStats]) -> str:
    """Format the statistics of the fields as a table."""
    return DataFrame(
        data={
            "values": [field.values for field in stats],
            "min": [field.minimum_str for field in stats],
            "max": [field.maximum_str for field in stats],
            "mean": [field.mean_str for field in stats],
            "median": [field.median_str for field in stats],
        },
        index=[field.field for field in stats]
    ).to_string()


def print_stats(title: str, stats: list[FieldStats]) -> None:
    """Print the statistics with a title."""
    print(f"{title}\n{stats_table(stats)}\n")


def main() -> None:
    """Print the statistics of the models, scenarios and points."""
    models = list(
        Model.objects
        .annotate(**Model.all_stats_annotations(), **Model.stats_annotations())
        .prefetch_related(
            "points",
            Prefetch("scenarios", queryset=Scenario.objects.annotate(**Scenario.stats_annotations())),
            "scenarios__points"
        )
    )
    scenarios = list(Scenario.objects.annotate(**Scenario.all_stats_annotations()))
    points = list(ParameterChoice.objects.annotate(**ParameterChoice.all_stats_annotations()))

    # Models
    print_stats("All models", window_stats(Model, models))
    huge_alpha = window_bool_stats(Model, models, "huge_alpha")
    print(f"Models with {huge_alpha.name}: {huge_alpha.n_true} / {huge_alpha.n}\n")

    # Scenarios
    print_stats("Scenarios of all models", window_stats(Scenario, scenarios))
    for model in models:
        if model.has_scenarios:
            print_stats(f"Scenarios of {model.name}", related_stats(model, "scenarios"))

    # Points
    print_stats("Points of all models", window_stats(ParameterChoice, points))
    for model in models:
        print_stats(f"Points of {model.name}", related_stats(model, "points"))
    for model in models:
        for scenario in model.scenarios.all():
            print_stats(f"Points of {model.name}: {scenario.name}", related_stats(scenario, "points"))


if __name__ == "__main__":
    main()
