"""Parameter choices for particle physics models."""

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from matplotlib.figure import Figure
from pttools.speedup import MAX_WORKERS_DEFAULT

from ptplot.models.model import Model
from ptplot.models.scenario import Scenario
from ptplot.science import const
from ptplot.science.noise import Noise
from ptplot.science.plot.power_spectrum import power_spectrum_figure
from ptplot.science.plot.snr_alpha_beta import snr_figure_alpha_beta
from ptplot.science.plot.snr_comparison import snr_comparison
from ptplot.science.plot.snr_ubarf_rstar import snr_figure_ubarf_rstar
from ptplot.science.snr.grid import SNRGrid
from ptplot.science.snr.grid_alpha_beta import SNRGridAlphaBeta
from ptplot.science.snr.grid_comparison import ComparisonMethod, SNRGridComparison
from ptplot.science.snr.grid_ubarf_rstar import SNRGridUbarfRStar
from ptplot.science.spectrum import Engine, power_spectrum


class ParameterChoice(models.Model):
    """A parameter choice, aka. a point, for a particle physics model."""

    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name="points")
    number = models.IntegerField()
    short_label = models.CharField(max_length=2)
    long_label = models.CharField(max_length=100)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True, related_name="points")
    # Numerical values that must be provided for the point
    alpha = models.FloatField(
        verbose_name=const.ALPHA_NAME,
        validators=[
            validators.MinValueValidator(0)
        ]
    )
    beta_over_H = models.FloatField(
        verbose_name=const.BETA_OVER_H_NAME,
        validators=[
            validators.MinValueValidator(0)
        ]
    )
    # Optional numerical values that override the values from the model and scenario
    v_wall = models.FloatField(
        verbose_name=const.V_WALL_NAME,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(1)
        ],
        null=True
    )
    T_star = models.FloatField(
        verbose_name=const.T_STAR_NAME,
        validators=[validators.MinValueValidator(0)],
        null=True
    )
    g_star = models.FloatField(
        verbose_name=const.G_STAR_NAME,
        validators=[validators.MinValueValidator(0)],
        null=True
    )

    class Meta:
        indexes = [models.Index(fields=["model", "number"])]
        ordering = ["model", "number"]
        unique_together = ["model", "number"]

    # -----
    # Overridden methods
    # -----

    def __str__(self) -> str:
        return self.long_label

    def get_absolute_url(self) -> str:
        return reverse("model_point_plot", kwargs={"model_id": self.model.id, "point_id": self.number})

    def clean(self):
        super().clean()
        errors = {}
        if self.scenario is not None and self.scenario.model != self.model:
            errors["scenario"] = ValidationError("The scenario must be for the same model as the parameter choice.")
        if errors:
            raise ValidationError(errors)

    # -----
    # Properties
    # -----

    @property
    def g_star_value(self) -> float:
        return self.model.g_star if self.g_star is None else self.g_star

    @property
    def v_wall_value(self) -> float:
        return self.model.v_wall if self.v_wall is None else self.v_wall

    @property
    def T_star_value(self) -> float:
        return self.T_star \
            if self.T_star is not None \
            else self.scenario.T_star_value if self.scenario is not None \
            else self.model.T_star

    # -----
    # Methods
    # -----

    def csv(self, noise: Noise | None = None, engine: Engine = Engine.DEFAULT) -> str:
        csv = power_spectrum(
            T_star=self.T_star_value,
            g_star=self.g_star_value,
            v_wall=self.v_wall_value,
            alpha=self.alpha,
            beta_over_H=self.beta_over_H,
            engine=engine
        ).csv(noise=noise)
        if csv is None:
            raise ValueError("Got no CSV data.")
        return csv

    def power_spectrum_figure(
            self,
            noise: Noise | None = None,
            engine: Engine = Engine.DEFAULT) -> Figure:
        spectrum = power_spectrum(
            T_star=self.T_star_value,
            g_star=self.g_star_value,
            v_wall=self.v_wall_value,
            alpha=self.alpha,
            beta_over_H=self.beta_over_H,
            engine=engine
        )
        return power_spectrum_figure(spectrum=spectrum, noise=noise)

    # def snr(
    #         self,
    #         adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX,
    #         noise: Noise | None = None,
    #         engine: Engine = Engine.DEFAULT) -> tuple[float, float]:
    #     snr, shock_time = snr_point(
    #         x=self.alpha, y=self.beta_over_H,
    #         T_star=self.T_star_value, g_star=self.g_star_value, v_wall=self.v_wall_value,
    #         adiabatic_index=adiabatic_index,
    #         noise=noise, engine=engine
    #     )
    #     return snr, shock_time

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
        r"""Compute the SNR grid of this point in the $(\alpha_n, \beta/H)$ plane.

        :param engine: Which power spectrum engine to use
        :param T_star: Temperature $T_*$ at which the GWs were produced, defaults to that of the point
        :param g_star: Degrees of freedom $g_*$, defaults to that of the point
        :param v_wall: Wall velocity $v_\text{wall}$, defaults to that of the point
        :param name: Name of the grid in comparison figures, defaults to the name of the engine
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param noise: Which noise curve to use
        :param max_workers: Maximum number of worker processes
        :return: SNR grid
        """
        return SNRGridAlphaBeta(
            T_star=self.T_star_value if T_star is None else T_star,
            g_star=self.g_star_value if g_star is None else g_star,
            v_wall=self.v_wall_value if v_wall is None else v_wall,
            noise=noise,
            alpha_points=self.alpha,
            beta_over_H_points=self.beta_over_H,
            v_wall_points=self.v_wall_value,
            labels_points=self.short_label,
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
        r"""Compute the SNR grid of this point in the $(\bar{U}_f, r_*)$ plane.

        :param engine: Which power spectrum engine to use
        :param T_star: Temperature $T_*$ at which the GWs were produced, defaults to that of the point
        :param g_star: Degrees of freedom $g_*$, defaults to that of the point
        :param v_wall: Wall velocity $v_\text{wall}$, defaults to that of the point
        :param name: Name of the grid in comparison figures, defaults to the name of the engine
        :param adiabatic_index: Mean adiabatic index $\Gamma$
        :param cs: Sound speed $c_s$
        :param noise: Which noise curve to use
        :param max_workers: Maximum number of worker processes
        :return: SNR grid
        """
        return SNRGridUbarfRStar(
            v_wall=self.v_wall_value if v_wall is None else v_wall,
            T_star=self.T_star_value if T_star is None else T_star,
            g_star=self.g_star_value if g_star is None else g_star,
            noise=noise,
            alpha_points=self.alpha,
            beta_over_H_points=self.beta_over_H,
            v_wall_points=self.v_wall_value,
            labels_points=self.short_label,
            adiabatic_index=adiabatic_index,
            cs=cs,
            engine=engine,
            name=name,
            max_workers=max_workers
        )
