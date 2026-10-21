"""Tests for creating power spectra."""

from pttools.models import ConstCSModel
import pytest

from ptplot.science import const
from ptplot.science.spectrum import Engine, PowerSpectrumSSM
from ptplot.science.spectrum.create import power_spectrum, ssm_model
from ptplot.science.spectrum.ssm import BAG


def test_ssm_model_default() -> None:
    """Without sound speeds that differ from the bag model, the bag model should be used."""
    assert ssm_model() is BAG
    assert ssm_model(css2=None, csb2=None) is BAG
    assert ssm_model(css2=const.CS0_2, csb2=const.CS0_2) is BAG


@pytest.mark.parametrize(("css2", "csb2"), [(0.3, None), (0.3, 0.3), (0.25, 0.3)])
def test_ssm_model_const_cs(css2: float | None, csb2: float | None) -> None:
    """Sound speeds that differ from the bag model should give a constant sound speed model."""
    model = ssm_model(css2=css2, csb2=csb2)
    assert isinstance(model, ConstCSModel)
    assert model.css2 == pytest.approx(const.CS0_2 if css2 is None else css2)
    assert model.csb2 == pytest.approx(const.CS0_2 if csb2 is None else csb2)


def test_ssm_model_given() -> None:
    """A model that has been given should be used regardless of the sound speeds."""
    model = ConstCSModel(css2=0.25, csb2=0.3)
    assert ssm_model(css2=0.2, csb2=0.2, model=model) is model


def test_power_spectrum_ssm_without_sound_speeds() -> None:
    """The SSM spectrum should use the bag model when the sound speeds are not given, as by the forms."""
    spectrum = power_spectrum(
        v_wall=const.DEFAULT_V_WALL, alpha=const.DEFAULT_ALPHA, beta_tilde=const.DEFAULT_BETA_TILDE,
        engine=Engine.SSM, css2=None, csb2=None
    )
    assert isinstance(spectrum, PowerSpectrumSSM)
    assert spectrum.model is BAG
