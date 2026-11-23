"""Tests for the points that do not depend on Django."""

import unittest

import numpy as np
import pytest

from ptplot.science import const
from ptplot.science.point import Point, PointBase
from ptplot.science.utils import ubarf_rstar_from_alpha_beta

#: $\alpha$, $\beta/H_*$, $v_\text{wall}$, and the reference $\bar{U}_f$, $r_*$ and the legacy $r_*$,
#: computed with the code of 2026-11-23
POINTS: tuple[tuple[float, float, float, float, float, float], ...] = (
    (0.1, 100, 0.9, 0.10264651688398349, 0.026362653976107417, 0.026362653976107417),
    (0.5, 20, 0.4, 0.35587058157959145, 0.05858367550246093, 0.08455825205365876),
    (0.05, 1000, 0.7, 0.10487296755175753, 0.0020504286425861323, 0.0020504286425861323),
)


class PointTest(unittest.TestCase):
    """Tests for :py:class:`ptplot.science.point.Point`."""

    @staticmethod
    def test_base_v_wall() -> None:
        r"""The base class should not provide $v_\text{wall}$."""
        with pytest.raises(NotImplementedError):
            _ = PointBase().v_wall_value

    @staticmethod
    def test_reference() -> None:
        r"""$\bar{U}_f$ and $r_*$ should match the reference values."""
        for alpha, beta_tilde, v_wall, ubarf, r_star, r_star_legacy in POINTS:
            point = Point(alpha=alpha, beta_tilde=beta_tilde, v_wall=v_wall)
            assert point.v_wall_value == v_wall
            assert point.ubarf() == pytest.approx(ubarf, rel=1e-12)
            assert point.r_star() == pytest.approx(r_star, rel=1e-12)
            assert point.r_star(legacy_nucleation_cs_max=True) == pytest.approx(r_star_legacy, rel=1e-12)

    @staticmethod
    def test_r_star0() -> None:
        r"""$r_*$ should be $r_*(0) = (8\pi)^{1/3} {v}_\text{wall} / \tilde{\beta}$ of :ajmi_2022:`\ ` eq. 1.

        In the legacy conversion, $v_\text{wall}$ is replaced by $\max({v}_\text{wall}, c_s)$.
        """
        for alpha, beta_tilde, v_wall, *_ in POINTS:
            point = Point(alpha=alpha, beta_tilde=beta_tilde, v_wall=v_wall)
            assert point.r_star() == pytest.approx((8 * np.pi)**(1/3) * v_wall / beta_tilde)
            assert point.r_star(legacy_nucleation_cs_max=True) == pytest.approx(
                (8 * np.pi)**(1/3) * max(v_wall, const.CS0) / beta_tilde
            )

    @staticmethod
    def test_ubarf_rstar_from_alpha_beta() -> None:
        r"""$\bar{U}_f$ and $r_*$ should be the same as those of the points of the SNR grids."""
        alpha, beta_tilde, v_wall = (np.array([point[i] for point in POINTS]) for i in range(3))
        for adiabatic_index in (const.DEFAULT_ADIABATIC_INDEX, 1.):
            for legacy in (False, True):
                _, ubarf, r_star, _ = ubarf_rstar_from_alpha_beta(
                    v_wall=v_wall, alpha=alpha, beta_tilde=beta_tilde, labels=None,
                    adiabatic_index=adiabatic_index, legacy_nucleation_cs_max=legacy
                )
                for i, (a, b, v, *_) in enumerate(POINTS):
                    point = Point(alpha=a, beta_tilde=b, v_wall=v)
                    assert point.ubarf(adiabatic_index=adiabatic_index) == pytest.approx(ubarf[0][i])
                    assert point.r_star(legacy_nucleation_cs_max=legacy) == pytest.approx(r_star[0][i])
