r"""Points in the parameter space of the phase transitions, e.g. for highlighting them in the SNR figures.

:py:class:`PointBase` is the base class of the points, which does not depend on Django.
It is inherited by the Django model :py:class:`ptplot.models.parameter_choice.ParameterChoice`,
and by :py:class:`Point`, which can be used without a database, e.g. for the parameters of a lattice simulation.
"""

from dataclasses import dataclass

from pttools.bubble.energy_budget import ubarf_approx
from pttools.models import Model
from pttools.ssm.nucleation import r_star as r_star_func

from ptplot.science import const

__all__ = ["Point", "PointBase"]


class PointBase:
    r"""Base class of the points, which have $\alpha$, $\tilde{\beta}$ and $v_\text{wall}$.

    This is a plain class instead of an abstract base class,
    as the metaclass of the Django models conflicts with :py:class:`abc.ABCMeta`.
    The subclasses have to provide :py:attr:`alpha_value`, :py:attr:`beta_tilde_value` and :py:attr:`v_wall_value`.
    """

    __slots__ = ()

    @property
    def alpha_value(self) -> float:
        r"""$\alpha$, phase transition strength."""
        raise NotImplementedError

    @property
    def beta_tilde_value(self) -> float:
        r"""$\tilde{\beta} = \beta/H_*$, inverse phase transition duration."""
        raise NotImplementedError

    @property
    def v_wall_value(self) -> float:
        r"""$v_\text{wall}$, wall velocity."""
        raise NotImplementedError

    def r_star(self, cs: float = const.CS0, legacy_nucleation_cs_max: bool = False) -> float:
        r"""$r_*$, Hubble-scaled mean bubble spacing of this point.

        See :py:func:`pttools.ssm.nucleation.r_star`
        and :py:func:`ptplot.science.utils.ubarf_rstar_from_alpha_beta`.

        :param cs: $c_s$, sound speed, which is used only for the legacy conversion
        :param legacy_nucleation_cs_max:
            Use legacy $\max(v_{\text{wall}}, c_s)$ in $\tilde{\beta} \leftrightarrow r_*$ conversion
        """
        return float(r_star_func(
            beta_tilde=self.beta_tilde_value, v_wall=self.v_wall_value,
            legacy_cs=cs if legacy_nucleation_cs_max else None
        ))

    def ubarf(
            self,
            model: Model | None = None,
            cs: float = const.CS0,
            adiabatic_index: float = const.DEFAULT_ADIABATIC_INDEX) -> float:
        r"""$\bar{U}_f$, approximate RMS fluid velocity of this point.

        See :py:func:`pttools.bubble.energy_budget.ubarf_approx`
        and :py:func:`ptplot.science.utils.ubarf_rstar_from_alpha_beta`.

        :param model: Equation of state model of PTtools
        :param cs: $c_s$, sound speed
        :param adiabatic_index: $\Gamma$, mean adiabatic index
        """
        return float(ubarf_approx(
            v_wall=self.v_wall_value, alpha_n=self.alpha_value, model=model, cs=cs, adiabatic_index=adiabatic_index
        ))


@dataclass(frozen=True, slots=True)
class Point(PointBase):
    r"""A point that is not stored in the database, e.g. the parameters of a lattice simulation."""

    #: $\alpha$, phase transition strength
    alpha: float
    #: $\tilde{\beta} = \beta/H_*$, inverse phase transition duration
    beta_tilde: float
    #: $v_\text{wall}$, wall velocity
    v_wall: float

    @property
    def alpha_value(self) -> float:
        r"""$\alpha$, phase transition strength."""
        return self.alpha

    @property
    def beta_tilde_value(self) -> float:
        r"""$\tilde{\beta} = \beta/H_*$, inverse phase transition duration."""
        return self.beta_tilde

    @property
    def v_wall_value(self) -> float:
        r"""$v_\text{wall}$, wall velocity."""
        return self.v_wall
