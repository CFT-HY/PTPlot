"""Tests for the statistics of the database models."""

from django.test import TestCase
import pytest

from ptplot.methods import POINT_STATS_FIELDS, bool_stats, field_stats, field_stats_by, format_value
from ptplot.models import Model, ParameterChoice, Scenario


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

    def test_field_stats(self) -> None:
        """The statistics of all points should be computed from the stored values."""
        stats = {field.field: field for field in field_stats(ParameterChoice.objects.all(), POINT_STATS_FIELDS)}
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

    def test_field_stats_empty(self) -> None:
        """The statistics of an empty queryset should be empty."""
        stats = field_stats(ParameterChoice.objects.none(), ("alpha", ))
        assert (stats[0].n, stats[0].n_set, stats[0].median) == (0, 0, None)

    def test_field_stats_by(self) -> None:
        """The statistics should be grouped by the given field."""
        stats = field_stats_by(ParameterChoice.objects.all(), "model", ("beta_tilde", ))
        assert set(stats.keys()) == {self.model1.id, self.model2.id}
        beta1 = stats[self.model1.id][0]
        assert (beta1.n, beta1.minimum, beta1.maximum, beta1.mean, beta1.median) == (4, 10, 1000, 265, 25)
        beta2 = stats[self.model2.id][0]
        assert (beta2.n, beta2.minimum, beta2.maximum, beta2.mean, beta2.median) == (1, 50, 50, 50, 50)

        by_scenario = field_stats_by(ParameterChoice.objects.filter(scenario__isnull=False), "scenario", ("alpha", ))
        assert list(by_scenario.keys()) == [self.scenario.id]
        assert by_scenario[self.scenario.id][0].median == pytest.approx(0.2)

    def test_bool_stats(self) -> None:
        """The number of models with huge alpha should be counted."""
        stats = bool_stats(Model.objects.all(), "huge_alpha")
        assert (stats.n, stats.n_true) == (2, 1)

    @staticmethod
    def test_format_value() -> None:
        """The values should be formatted with four significant digits."""
        assert format_value(None) == "-"
        assert format_value(123456.0) == "1.235e+05"
        assert format_value(0.5) == "0.5"
