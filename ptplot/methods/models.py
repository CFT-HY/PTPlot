import typing as tp

from django.db.models import QuerySet
from pandas import DataFrame

if tp.TYPE_CHECKING:
    from ptplot.models.parameter_choice import ParameterChoice


def point_data(points: "QuerySet[ParameterChoice] | None" = None) -> DataFrame:
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
