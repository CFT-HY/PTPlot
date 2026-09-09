"""Scenarios for particle physics models."""

import typing as tp

from django.core import validators
from django.db import models
from django.urls import reverse
from matplotlib.figure import Figure
import numpy as np
from pandas import DataFrame
from pttools.speedup import MAX_WORKERS_DEFAULT

from ptplot.methods.models import point_data
from ptplot.models.const import NAME_MAX_LENGTH
from ptplot.models.model import Model
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

if tp.TYPE_CHECKING:
    from ptplot.models.parameter_choice import ParameterChoice


class Scenario(models.Model):
    """A scenario with a particular $T_*$ for a particle physics model."""

    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="scenarios")
    number = models.IntegerField()
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    T_star = models.FloatField(
        verbose_name=const.T_STAR_NAME,
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    description = models.TextField(blank=True)

    if tp.TYPE_CHECKING:
        # Reverse relation of the foreign key that points to this model.
        points: models.Manager["ParameterChoice"]

    class Meta:
        indexes = [models.Index(fields=["name"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]

    # -----
    # Overridden methods
    # -----

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("model_scenario_plot", kwargs={"model_id": self.model.id, "scenario_id": self.number})

    # -----
    # Properties
    # -----

    @property
    def T_star_value(self) -> float:
        return self.model.T_star if self.T_star is None else self.T_star

    # -----
    # Methods
    # -----

    def point_data(self) -> DataFrame:
        return point_data(self.points.all())

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
            huge_alpha=self.model.huge_alpha,
            filled=filled
        )

    def snr_figure_ubarf_rstar(
            self,
            grid: SNRGridUbarfRStar | None = None,
            filled: bool = False) -> Figure:
        return snr_figure_ubarf_rstar(
            grid=self.snr_grid_ubarf_rstar() if grid is None else grid,
            huge_alpha=self.model.huge_alpha,
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
        r"""Compute the SNR grid of this scenario in the $(\alpha_n, \beta/H)$ plane.

        :param engine: Which power spectrum engine to use
        :param T_star: Temperature $T_*$ at which the GWs were produced, defaults to that of the scenario
        :param g_star: Degrees of freedom $g_*$, defaults to that of the model
        :param v_wall: Wall velocity $v_\text{wall}$, defaults to that of the model
        :param name: Name of the grid in comparison figures, defaults to the name of the engine
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param noise: Which noise curve to use
        :param max_workers: Maximum number of worker processes
        :return: SNR grid
        """
        data = self.point_data()
        return SNRGridAlphaBeta(
            T_star=self.T_star_value if T_star is None else T_star,
            g_star=self.model.g_star if g_star is None else g_star,
            v_wall=self.model.v_wall if v_wall is None else v_wall,
            noise=noise,
            alpha_points=data["alpha_n"].to_numpy(dtype=np.float64),
            beta_over_H_points=data["beta_over_H"].to_numpy(dtype=np.float64),
            v_wall_points=data["v_wall"].to_numpy(dtype=np.float64),
            labels_points=data["label"].to_list(),
            titles=self.name,
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
        r"""Compute the SNR grid of this scenario in the $(\bar{U}_f, r_*)$ plane.

        :param engine: Which power spectrum engine to use
        :param T_star: Temperature $T_*$ at which the GWs were produced, defaults to that of the scenario
        :param g_star: Degrees of freedom $g_*$, defaults to that of the model
        :param v_wall: Wall velocity $v_\text{wall}$, defaults to that of the model
        :param name: Name of the grid in comparison figures, defaults to the name of the engine
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param cs: Sound speed $c_s$
        :param noise: Which noise curve to use
        :param max_workers: Maximum number of worker processes
        :return: SNR grid
        """
        data = self.point_data()
        return SNRGridUbarfRStar(
            v_wall=self.model.v_wall if v_wall is None else v_wall,
            T_star=self.T_star_value if T_star is None else T_star,
            g_star=self.model.g_star if g_star is None else g_star,
            noise=noise,
            alpha_points=data["alpha_n"].to_numpy(dtype=np.float64),
            beta_over_H_points=data["beta_over_H"].to_numpy(dtype=np.float64),
            v_wall_points=data["v_wall"].to_numpy(dtype=np.float64),
            labels_points=data["label"].to_list(),
            titles=self.name,
            adiabatic_index=adiabatic_index,
            cs=cs,
            engine=engine,
            name=name,
            max_workers=max_workers
        )

    def snr_histogram(self, noise: Noise | None = None) -> Figure:
        data = self.point_data()
        return snr_histogram(
            v_wall=data["v_wall"].to_numpy(dtype=np.float64),
            alpha_n=data["alpha_n"].to_numpy(dtype=np.float64),
            beta_over_H=data["beta_over_H"].to_numpy(dtype=np.float64),
            T_star=data["T_star"].to_numpy(dtype=np.float64),
            g_star=data["g_star"].to_numpy(dtype=np.float64),
            labels=data["label"].to_list(),
            titles=self.name,
            noise=noise,
            # engines=[form.cleaned_data["engine"]]
        )
