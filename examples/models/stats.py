"""
Model statistics
================

Print statistics of the models, scenarios and points in the database.
The minimum, maximum, mean and the number of values are computed with Django aggregations.
The median is computed in Python, as there is no median aggregation for SQLite.
For the fields that can be left unset, the number of objects for which they are set is also shown.
"""

from pandas import DataFrame

from ptplot.methods import setup_django

if __name__ == "__main__":
    setup_django()

from ptplot.methods import (
    MODEL_STATS_FIELDS,
    POINT_STATS_FIELDS,
    SCENARIO_STATS_FIELDS,
    FieldStats,
    bool_stats,
    field_stats,
    field_stats_by,
)
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
    models = Model.objects.all()
    scenarios = Scenario.objects.all()
    points = ParameterChoice.objects.all()
    model_names: dict[int, str] = dict(models.values_list("id", "name"))
    scenario_names: dict[int, str] = {
        scenario.id: f"{model_names[scenario.model_id]}: {scenario.name}" for scenario in scenarios
    }

    # Models
    print_stats("All models", field_stats(models, MODEL_STATS_FIELDS))
    huge_alpha = bool_stats(models, "huge_alpha")
    print(f"Models with {huge_alpha.name}: {huge_alpha.n_true} / {huge_alpha.n}\n")

    # Scenarios
    print_stats("Scenarios of all models", field_stats(scenarios, SCENARIO_STATS_FIELDS))
    for model_id, stats in field_stats_by(scenarios, "model", SCENARIO_STATS_FIELDS).items():
        print_stats(f"Scenarios of {model_names[model_id]}", stats)

    # Points
    print_stats("Points of all models", field_stats(points, POINT_STATS_FIELDS))
    for model_id, stats in field_stats_by(points, "model", POINT_STATS_FIELDS).items():
        print_stats(f"Points of {model_names[model_id]}", stats)
    scenario_points = points.filter(scenario__isnull=False)
    for scenario_id, stats in field_stats_by(scenario_points, "scenario", POINT_STATS_FIELDS).items():
        print_stats(f"Points of {scenario_names[scenario_id]}", stats)


if __name__ == "__main__":
    main()
