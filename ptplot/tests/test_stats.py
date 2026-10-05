"""Tests for the statistics of the database models."""

from django.db.models import Prefetch
from django.test import TestCase
import pytest

from ptplot.methods import FieldStats, format_value, related_stats, window_bool_stats, window_stats
from ptplot.models import Model, ParameterChoice, Scenario
from ptplot.science import const


def by_field(stats: list[FieldStats]) -> dict[str, FieldStats]:
    """Get the statistics by the name of the field."""
    return {field.field: field for field in stats}


class StatsTest(TestCase):
    """Tests for :py:mod:`ptplot.methods.stats`."""

    model1: Model
    model2: Model
    scenario: Scenario

    @classmethod
    def setUpTestData(cls) -> None:
        """Create two models with points, one of them with a scenario."""
        cls.model1 = Model.objects.create(
            name="Model 1", slug="model1", v_wall=0.9, T_star=100, g_star=100, huge_alpha=True, has_scenarios=True
        )
        cls.model2 = Model.objects.create(
            name="Model 2", slug="model2", v_wall=0.5, T_star=200, g_star=110, has_scenarios=False
        )
        cls.scenario = Scenario.objects.create(model=cls.model1, number=1, name="Scenario 1", T_star=50)
        Scenario.objects.create(model=cls.model1, number=2, name="Scenario 2")
        for number, alpha, beta_tilde, T_star, scenario in (
                (1, 0.1, 10, None, cls.scenario),
                (2, 0.2, 20, 70, cls.scenario),
                (3, 0.6, 30, 80, cls.scenario),
                (4, 1.0, 1000, None, None)):
            ParameterChoice.objects.create(
                model=cls.model1, number=number, alpha=alpha, beta_tilde=beta_tilde, T_star=T_star, scenario=scenario
            )
        ParameterChoice.objects.create(model=cls.model2, number=1, alpha=0.5, beta_tilde=50, v_wall=0.7)

    def test_window_stats(self) -> None:
        """The statistics over all points should be computed in the same query that fetches the points."""
        with self.assertNumQueries(1):
            points = list(ParameterChoice.objects.annotate(**ParameterChoice.all_stats_annotations()))
        stats = by_field(window_stats(ParameterChoice, points))
        alpha = stats["alpha"]
        assert (alpha.n, alpha.n_set) == (5, 5)
        assert not alpha.nullable
        assert (alpha.minimum, alpha.maximum, alpha.mean, alpha.median) == pytest.approx((0.1, 1.0, 0.48, 0.5))

        # Unset values are excluded, and the median of an even number of values is the mean of the middle ones.
        T_star = stats["T_star"]
        assert T_star.nullable
        assert (T_star.n, T_star.n_set, T_star.median) == (5, 2, 75)
        assert T_star.values == "2 / 5"

        g_star = stats["g_star"]
        assert (g_star.n_set, g_star.minimum, g_star.mean, g_star.median) == (0, None, None, None)

    def test_window_stats_filtered(self) -> None:
        """The statistics should be computed over the filtered objects only."""
        models = list(Model.objects.filter(huge_alpha=False).annotate(**Model.all_stats_annotations()))
        T_star = by_field(window_stats(Model, models))["T_star"]
        assert (T_star.n, T_star.minimum, T_star.maximum, T_star.median) == (1, 200, 200, 200)

    def test_window_stats_empty(self) -> None:
        """The statistics of an empty queryset should be empty."""
        stats = window_stats(ParameterChoice, [])
        assert (stats[0].n, stats[0].n_set, stats[0].minimum, stats[0].median) == (0, 0, None, None)

    def test_window_bool_stats(self) -> None:
        """The number of models with huge alpha should be counted."""
        models = list(Model.objects.annotate(**Model.all_stats_annotations()))
        stats = window_bool_stats(Model, models, "huge_alpha")
        assert (stats.n, stats.n_true) == (2, 1)

    def test_related_stats(self) -> None:
        """The statistics of the points and scenarios should be computed for each model.

        The counts should not be multiplied by the number of rows of the other relation.
        """
        with self.assertNumQueries(3):
            models = list(Model.objects.annotate(**Model.stats_annotations()).prefetch_related("points", "scenarios"))
            stats = {model.id: (related_stats(model, "points"), related_stats(model, "scenarios")) for model in models}

        points1, scenarios1 = stats[self.model1.id]
        beta1 = by_field(points1)["beta_tilde"]
        assert (beta1.n, beta1.minimum, beta1.maximum, beta1.mean, beta1.median) == (4, 10, 1000, 265, 25)
        t_star1 = by_field(scenarios1)["T_star"]
        assert (t_star1.n, t_star1.n_set, t_star1.mean, t_star1.median) == (2, 1, 50, 50)

        points2, scenarios2 = stats[self.model2.id]
        beta2 = by_field(points2)["beta_tilde"]
        assert (beta2.n, beta2.minimum, beta2.maximum, beta2.mean, beta2.median) == (1, 50, 50, 50, 50)
        # A model without scenarios
        t_star2 = by_field(scenarios2)["T_star"]
        assert (t_star2.n, t_star2.n_set, t_star2.minimum, t_star2.median) == (0, 0, None, None)

    def test_related_stats_scenario(self) -> None:
        """The statistics of the points should be computed for each scenario."""
        model = Model.objects.prefetch_related(
            Prefetch("scenarios", queryset=Scenario.objects.annotate(**Scenario.stats_annotations())),
            "scenarios__points"
        ).get(id=self.model1.id)
        scenario1, scenario2 = model.scenarios.all()
        alpha1 = by_field(related_stats(scenario1, "points"))["alpha"]
        assert (alpha1.n, alpha1.median) == (3, pytest.approx(0.2))
        alpha2 = by_field(related_stats(scenario2, "points"))["alpha"]
        assert (alpha2.n, alpha2.median) == (0, None)

    @staticmethod
    def test_annotated_labels() -> None:
        """The LaTeX labels of the parameter ranges should combine the points and scenarios."""
        model = Model.objects.annotate(**Model.stats_annotations()).get(slug="model1")
        assert model.annotated_labels() == (
            r"$\alpha_n \in [0.1, 1], \ \beta/H_* \in [10, 1000], \ v_\text{wall} = 0.9, \ "
            r"T_* \in [50, 80] \ \text{GeV}, \ g_* = 100.0$"
        )

    @staticmethod
    def test_latex_names() -> None:
        """The statistics should have the names of the fields with LaTeX symbols."""
        stats = by_field(window_stats(ParameterChoice, []))
        assert stats["alpha"].name == const.ALPHA_NAME
        assert stats["alpha"].name_latex == const.ALPHA_NAME_LATEX

    @staticmethod
    def test_format_value() -> None:
        """The values should be formatted with four significant digits."""
        assert format_value(None) == "-"
        assert format_value(123456.0) == "1.235e+05"
        assert format_value(0.5) == "0.5"
