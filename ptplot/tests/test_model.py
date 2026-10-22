"""Tests for the particle physics models."""

from django.test import TestCase
import numpy as np
import pytest

from ptplot.models import Model, ParameterChoice, Scenario
from ptplot.science.plot.snr_alpha_beta import SNRFigureAlphaBeta
from ptplot.science.plot.snr_ubarf_rstar import SNRFigureUbarfRStar
from ptplot.science.snr.grid import GridAxes
from ptplot.science.snr.grid_comparison import engine_comparisons
from ptplot.science.spectrum import Engine
from ptplot.tests.const import TEST_GRID_SIZE

#: Number, $\alpha$, $\beta/H_*$, $T_*$ and the number of the scenario of each point of the test model.
#: The points are deliberately not ordered by $\alpha$, and the scenarios are interleaved.
POINTS: tuple[tuple[int, float, float, float | None, int], ...] = (
    (1, 0.3, 100, None, 2),
    (2, 0.1, 50, 70, 1),
    (3, 0.5, 200, 80, 2),
    (4, 0.2, 20, 120, 1),
)
#: $T_*$ of the model, which is used for the points that don't have their own
MODEL_T_STAR: float = 100


class ModelTest(TestCase):
    """Tests for :py:class:`ptplot.models.model.Model`."""

    model: Model
    empty_model: Model

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a model with points in two scenarios, and a model without points."""
        cls.model = Model.objects.create(
            name="Test model", slug="test_model", v_wall=0.9, T_star=MODEL_T_STAR, g_star=100, has_scenarios=True
        )
        cls.empty_model = Model.objects.create(
            name="Empty model", slug="empty_model", v_wall=0.9, T_star=MODEL_T_STAR, g_star=100, has_scenarios=False
        )
        scenarios = {
            number: Scenario.objects.create(model=cls.model, number=number, name=f"Scenario {number}")
            for number in (1, 2)
        }
        for number, alpha, beta_tilde, T_star, scenario in POINTS:
            ParameterChoice.objects.create(
                model=cls.model, number=number, alpha=alpha, beta_tilde=beta_tilde, T_star=T_star,
                scenario=scenarios[scenario]
            )

    def test_closest_point(self) -> None:
        r"""The point whose $\alpha$ is closest to the given value should be found."""
        for alpha, number in ((0.31, 1), (0.0, 2), (0.14, 2), (0.16, 4), (0.45, 3), (10., 3)):
            assert self.model.closest_point(alpha).number == number

    def test_closest_point_tie(self) -> None:
        """Of equally close points, the one with the smallest number should be returned."""
        ParameterChoice.objects.create(model=self.model, number=5, alpha=0.3, beta_tilde=10)
        assert self.model.closest_point(0.3).number == 1

    def test_closest_point_empty(self) -> None:
        """A model without points has no closest point."""
        with pytest.raises(ValueError, match="no points"):
            self.empty_model.closest_point(0.1)

    def test_point_index(self) -> None:
        """The index should be that of the point in the arrays of the points of the model."""
        _, alpha, *_ = self.model.point_data_by_field()
        for number, point_alpha, *_ in POINTS:
            point = ParameterChoice.objects.get(model=self.model, number=number)
            assert alpha[self.model.point_index(point)] == point_alpha

    def test_point_index_other_model(self) -> None:
        """The points of other models should not be found."""
        point = ParameterChoice.objects.create(model=self.empty_model, number=1, alpha=0.1, beta_tilde=10)
        with pytest.raises(ValueError, match="not a point"):
            self.model.point_index(point)

    def test_point_T_star(self) -> None:
        """The statistics of the $T_*$ of the points should use the $T_*$ of the model as the default."""
        T_star = [MODEL_T_STAR if T_star is None else T_star for _, _, _, T_star, _ in POINTS]
        assert self.model.point_T_star() == pytest.approx(np.mean(T_star))
        assert self.model.point_T_star("mean") == pytest.approx(92.5)
        assert self.model.point_T_star("median") == pytest.approx(90)
        with pytest.raises(ValueError, match="no points"):
            self.empty_model.point_T_star()
        with pytest.raises(ValueError, match="not a valid Statistic"):
            self.model.point_T_star("mode")

    def test_snr_grid_by_scenario(self) -> None:
        """The points of the grid should be grouped by scenario only if requested."""
        axes = GridAxes(size=TEST_GRID_SIZE)
        grid = self.model.snr_grid_alpha_beta(axes=axes)
        assert grid.titles == ["Scenario 1", "Scenario 2"]
        np.testing.assert_array_equal(grid.alpha_points, [[0.1, 0.2], [0.3, 0.5]])

        grid_flat = self.model.snr_grid_alpha_beta(axes=axes, by_scenario=False)
        assert grid_flat.titles == self.model.name
        np.testing.assert_array_equal(grid_flat.alpha_points, [0.3, 0.1, 0.5, 0.2])

        grid_ur = self.model.snr_grid_ubarf_rstar(axes=axes, by_scenario=False)
        assert grid_ur.titles == self.model.name
        assert grid_ur.ubarf_points is not None
        assert np.size(grid_ur.ubarf_points) == len(POINTS)

    def test_snr_figures(self) -> None:
        """The figures should be created for the grids of both types, with the highlighted points."""
        axes = GridAxes(size=TEST_GRID_SIZE)
        highlights = {"Highlight": self.model.point_index(self.model.closest_point(0.5))}
        grids_ab = {
            engine: self.model.snr_grid_alpha_beta(engine=engine, axes=axes, by_scenario=False)
            for engine in (Engine.CosWG20bpl, Engine.GH21dbpl, Engine.CosWG24dbpl)
        }
        grid_ur = self.model.snr_grid_ubarf_rstar(axes=axes, by_scenario=False)
        assert isinstance(self.model.snr_figure(grids_ab[Engine.DEFAULT]), SNRFigureAlphaBeta)
        assert isinstance(self.model.snr_figure(grid_ur), SNRFigureUbarfRStar)
        with pytest.raises(TypeError, match="Unsupported"):
            self.model.snr_figure(engine_comparisons(grids_ab)[Engine.GH21dbpl])  # pyrefly: ignore[bad-argument-type]

        fig = self.model.snr_figure_alpha_beta(grids_ab[Engine.DEFAULT], highlights=highlights)
        legend = fig.get_axes()[0].get_legend()
        assert legend is not None
        assert "Highlight" in [text.get_text() for text in legend.get_texts()]
        self.model.snr_figure_ubarf_rstar(grid_ur, filled=True, highlights=highlights)

        fig_grid = self.model.snr_figure_grid(list(grids_ab.values()), highlights=highlights)
        assert [ax.get_title() for ax in fig_grid.get_axes() if ax.get_title()] == list(grids_ab)

        comparisons = engine_comparisons(grids_ab)
        fig_comp = self.model.snr_comparison_grid(list(comparisons.values()), highlights=highlights, ncols=3)
        assert [ax.get_title() for ax in fig_comp.get_axes() if ax.get_title()] == [
            f"{engine} vs. {Engine.DEFAULT}" for engine in comparisons
        ]
        self.model.snr_comparison(grids_ab[Engine.DEFAULT], grids_ab[Engine.GH21dbpl], highlights=highlights)
