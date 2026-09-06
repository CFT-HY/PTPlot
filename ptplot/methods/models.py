"""Methods for models"""

import typing as tp

from django.db.models import Avg, Max, Min
from pandas import DataFrame

if tp.TYPE_CHECKING:
    from django.db.models import QuerySet

    from ptplot.models.parameter_choice import ParameterChoice


def min_max_avg(*names) -> list[Avg | Max | Min]:
    return [func(name) for func in (Min, Max, Avg) for name in names]


def point_data(points: "QuerySet[ParameterChoice]") -> DataFrame:
    """Get the data of the points as a DataFrame"""
    return DataFrame(
        data={
            "number": [point.number for point in points],
            "alpha_n": [point.alpha for point in points],
            "beta_over_H": [point.beta_over_H for point in points],
            "T_star": [point.T_star_value for point in points],
            "g_star": [point.g_star_value for point in points],
            "v_wall": [point.v_wall_value for point in points],
            "label": [point.short_label for point in points]
        }
    )
