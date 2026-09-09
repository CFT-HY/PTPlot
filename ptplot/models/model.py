"""Particle physics models."""

import typing as tp

from django.core import validators
from django.db import models
from django.urls import reverse
from matplotlib.figure import Figure
import numpy as np
from pandas import DataFrame
from pttools.speedup import MAX_WORKERS_DEFAULT
from pttools.utils import as_latex

from ptplot.methods.models import min_max_avg, point_data
from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_comparison import snr_comparison
from ptplot.science.plot.snr_histogram import snr_histogram
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.snr.grid import SNRGrid
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr.grid_comparison import ComparisonMethod, SNRGridComparison
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum import Engine
import ptplot.science.type_hints as th

if tp.TYPE_CHECKING:
    from ptplot.models.parameter_choice import ParameterChoice
    from ptplot.models.scenario import Scenario


MODEL_ANNOTATIONS = min_max_avg(
    "points__alpha", "points__beta_over_H", "points__v_wall", "points__T_star", "points__g_star",
    "scenarios__T_star"
)


class Model(models.Model):
    """A particle physics model."""

    name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(max_length=NAME_MAX_LENGTH, unique=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    v_wall = models.FloatField(
        verbose_name="wall velocity",
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1)
        ],
    )
    T_star = models.FloatField(
        verbose_name=const.T_STAR_NAME,
        validators=[validators.MinValueValidator(0)]
    )
    g_star = models.FloatField(
        verbose_name=const.G_STAR_NAME,
        validators=[validators.MinValueValidator(0)]
    )
    huge_alpha = models.BooleanField(
        verbose_name=const.HUGE_ALPHA_NAME,
        default=False
    )
    has_scenarios = models.BooleanField()

    if tp.TYPE_CHECKING:
        # Reverse relations of the foreign keys that point to this model.
        points: models.Manager["ParameterChoice"]
        scenarios: models.Manager["Scenario"]
        # Added by Count("points") when the object is fetched with the annotation.
        n_points: int
        # Added by MODEL_ANNOTATIONS when the object is fetched with annotations.
        points__alpha__min: float | None
        points__alpha__max: float | None
        points__alpha__avg: float | None
        points__beta_over_H__min: float | None
        points__beta_over_H__max: float | None
        points__beta_over_H__avg: float | None
        points__v_wall__min: float | None
        points__v_wall__max: float | None
        points__v_wall__avg: float | None
        points__T_star__min: float | None
        points__T_star__max: float | None
        points__T_star__avg: float | None
        points__g_star__min: float | None
        points__g_star__max: float | None
        points__g_star__avg: float | None
        scenarios__T_star__min: float | None
        scenarios__T_star__max: float | None
        scenarios__T_star__avg: float | None

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("model_detail", kwargs={"model_id": self.id})

    @staticmethod
    def annotated_label(
            label: str,
            x_min: float | None,
            x_max: float | None,
            default: float | None = None,
            unit: str | None = None) -> str:
        unit_str = "" if unit is None else rf" \ \text{{{unit}}}"
        if x_min == x_max:
            return f"{label} = {default if x_min is None else as_latex(x_min)}{unit_str}"
        return rf"{label} \in [{as_latex(x_min)}, {as_latex(x_max)}]{unit_str}"

    def annotated_labels(self) -> str:
        return "$" + r", \ ".join([
            self.annotated_label(r"\alpha_n", self.points__alpha__min, self.points__alpha__max),
            self.annotated_label(r"\beta/H_*", self.points__beta_over_H__min, self.points__beta_over_H__max),
            self.annotated_label(
                r"v_\text{wall}",
                self.points__v_wall__min,
                self.points__v_wall__max,
                default=self.v_wall
            ),
            self.annotated_label(
                "T_*",
                min(x for x in (self.points__T_star__min, self.scenarios__T_star__min) if x is not None),
                max(x for x in (self.points__T_star__max, self.scenarios__T_star__max) if x is not None),
                default=self.T_star,
                unit="GeV"
            ),
            self.annotated_label("g_*", self.points__g_star__min, self.points__g_star__max, default=self.g_star)
        ]) + "$"

    def point_data(self) -> DataFrame:
        """Get the data of the points of this model as a DataFrame."""
        return point_data(self.points.all())

    def point_data_by_scenario(self) -> "dict[Scenario, DataFrame]":
        """Get the data of the points of this model by scenario."""
        return {scenario: scenario.point_data() for scenario in self.scenarios.prefetch_related("points").all()}

    def point_data_by_field(self) \
            -> tuple[th.FloatArr1D, th.FloatArr1D, th.FloatArr1D, th.FloatArr1D, th.FloatArr1D, list[str], str]:
        """Get the data of the points of this model as arrays of each field."""
        data = self.point_data()
        v_wall = data["v_wall"].to_numpy(dtype=np.float64)
        alpha = data["alpha_n"].to_numpy(dtype=np.float64)
        beta_over_H = data["beta_over_H"].to_numpy(dtype=np.float64)
        T_star = data["T_star"].to_numpy(dtype=np.float64)
        g_star = data["g_star"].to_numpy(dtype=np.float64)
        labels = data["label"].to_list()
        titles = self.name
        return v_wall, alpha, beta_over_H, T_star, g_star, labels, titles

    def point_data_by_field_and_scenario(self) -> tuple[
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                th.FloatArr1DOrListOfArr1D,
                list[list[str]] | list[str],
                list[str] | str]:
        """Get the data of the points of this model as arrays of each field, in lists by scenario."""
        if not self.has_scenarios:
            return self.point_data_by_field()
        scenarios = self.scenarios.prefetch_related("points").all()
        v_wall = []
        alpha = []
        beta_over_H = []
        T_star = []
        g_star = []
        labels = []
        titles = []

        for scenario in scenarios:
            data = scenario.point_data()
            v_wall.append(data["v_wall"].to_numpy(dtype=np.float64))
            alpha.append(data["alpha_n"].to_numpy(dtype=np.float64))
            beta_over_H.append(data["beta_over_H"].to_numpy(dtype=np.float64))
            T_star.append(data["T_star"].to_numpy(dtype=np.float64))
            g_star.append(data["g_star"].to_numpy(dtype=np.float64))
            labels.append(data["label"].to_list())
            titles.append(scenario.name)

        return v_wall, alpha, beta_over_H, T_star, g_star, labels, titles

    def snr_comparison(
            self,
            grid1: SNRGrid,
            grid2: SNRGrid,
            method: ComparisonMethod = ComparisonMethod.DEFAULT,
            label: str | None = None) -> Figure:
        """Compare the SNR values of two grids.

        :param grid1: SNR grid of the reference
        :param grid2: SNR grid to compare to the reference
        :param method: How to compare the SNR values
        :param label: Label of the comparison, defaults to a label deduced from the method
            and the names of the grids
        :return: Figure of the compared SNR values
        """
        return snr_comparison(
            SNRGridComparison(grid1=grid1, grid2=grid2, method=method, label=label)
        )

    def snr_figure_alpha_beta(
            self,
            grid: SNRGridAlphaBeta | None = None,
            filled: bool = False) -> Figure:
        return snr_figure_alpha_beta(
            grid=self.snr_grid_alpha_beta() if grid is None else grid,
            huge_alpha=self.huge_alpha,
            filled=filled
        )

    def snr_figure_ubarf_rstar(
            self,
            grid: SNRGridUbarfRStar | None = None,
            filled: bool = False) -> Figure:
        return snr_figure_ubarf_rstar(
            grid=self.snr_grid_ubarf_rstar() if grid is None else grid,
            huge_alpha=self.huge_alpha,
            filled=filled
        )

    def snr_grid_alpha_beta(
            self,
            engine: Engine = Engine.DEFAULT,
            T_star: float | None = None,
            g_star: float | None = None,
            v_wall: float | None = None,
            name: str | None = None,
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            noise: Noise | None = None,
            max_workers: int = MAX_WORKERS_DEFAULT) -> SNRGridAlphaBeta:
        r"""Compute the SNR grid of this model in the $(\alpha_n, \beta/H)$ plane.

        :param engine: Which power spectrum engine to use
        :param T_star: Temperature $T_*$ at which the GWs were produced, defaults to that of the model
        :param g_star: Degrees of freedom $g_*$, defaults to that of the model
        :param v_wall: Wall velocity $v_\text{wall}$, defaults to that of the model
        :param name: Name of the grid in comparison figures, defaults to the name of the engine
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param noise: Which noise curve to use
        :param max_workers: Maximum number of worker processes
        :return: SNR grid
        """
        v_wall_points, alpha, beta_over_H, _, _, labels, titles = self.point_data_by_field_and_scenario()
        return SNRGridAlphaBeta(
            T_star=self.T_star if T_star is None else T_star,
            g_star=self.g_star if g_star is None else g_star,
            v_wall=self.v_wall if v_wall is None else v_wall,
            noise=noise,
            alpha_points=alpha,
            beta_over_H_points=beta_over_H,
            v_wall_points=v_wall_points,
            labels_points=labels,
            titles=titles,
            adiabatic_index=adiabatic_index,
            engine=engine,
            name=name,
            max_workers=max_workers
        )

    def snr_grid_ubarf_rstar(
            self,
            engine: Engine = Engine.DEFAULT,
            T_star: float | None = None,
            g_star: float | None = None,
            v_wall: float | None = None,
            name: str | None = None,
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
            cs: float = const.CS0,
            noise: Noise | None = None,
            max_workers: int = MAX_WORKERS_DEFAULT) -> SNRGridUbarfRStar:
        r"""Compute the SNR grid of this model in the $(\bar{U}_f, r_*)$ plane.

        :param engine: Which power spectrum engine to use
        :param T_star: Temperature $T_*$ at which the GWs were produced, defaults to that of the model
        :param g_star: Degrees of freedom $g_*$, defaults to that of the model
        :param v_wall: Wall velocity $v_\text{wall}$, defaults to that of the model
        :param name: Name of the grid in comparison figures, defaults to the name of the engine
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param cs: Sound speed $c_s$
        :param noise: Which noise curve to use
        :param max_workers: Maximum number of worker processes
        :return: SNR grid
        """
        v_wall_points, alpha, beta_over_H, _, _, labels, titles = self.point_data_by_field_and_scenario()
        return SNRGridUbarfRStar(
            v_wall=self.v_wall if v_wall is None else v_wall,
            T_star=self.T_star if T_star is None else T_star,
            g_star=self.g_star if g_star is None else g_star,
            noise=noise,
            alpha_points=alpha,
            beta_over_H_points=beta_over_H,
            v_wall_points=v_wall_points,
            labels_points=labels,
            titles=titles,
            adiabatic_index=adiabatic_index,
            cs=cs,
            engine=engine,
            name=name,
            max_workers=max_workers
        )

    def snr_histogram(self, noise: Noise | None = None) -> Figure:
        v_wall, alpha, beta_over_H, T_star, g_star, labels, titles = self.point_data_by_field()
        return snr_histogram(
            v_wall=v_wall, alpha_n=alpha, beta_over_H=beta_over_H, T_star=T_star, g_star=g_star,
            labels=labels, titles=titles,
            noise=noise,
            # engines=[form.cleaned_data["engine"]]
        )
