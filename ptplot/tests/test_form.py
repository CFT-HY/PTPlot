"""Tests for forms."""

import typing as tp

from django.test import TestCase
from pttools.models import ConstCSModel

from ptplot.forms import PTPlotForm
from ptplot.science.spectrum.engine import Engine
from ptplot.science.spectrum.ssm import BAG


class PTPlotFormTest(TestCase):
    """Tests for the equation of state model of the single point form."""

    DATA: tp.ClassVar[dict[str, tp.Any]] = {
        "v_wall": "0.5", "alpha": "0.2", "beta_tilde": "100", "T_star": "100", "g_star": "100",
        "obs_years": "3", "noise_eb": True, "noise_gb": True
    }

    def form(self, **kwargs: tp.Any) -> PTPlotForm:
        """Create a form of the test data with the given changes."""
        return PTPlotForm(data={**self.DATA, **kwargs})

    def test_model_bag(self) -> None:
        """Without the sound speeds, or with those of the bag model, the bag model should be used."""
        for kwargs in ({}, {"css2": "1/3", "csb2": "1/3"}):
            form = self.form(engine=Engine.SSM, **kwargs)
            assert form.is_valid(), form.errors
            assert form.model is BAG

    def test_model_const_cs(self) -> None:
        """With the sound speeds, the SSM should use the constant sound speed model."""
        css2 = 0.25
        csb2 = 0.3
        # The fraction should also be accepted.
        form = self.form(engine=Engine.SSM, css2="1/4", csb2=str(csb2))
        assert form.is_valid(), form.errors
        assert isinstance(form.model, ConstCSModel)
        assert form.model.css2 == css2
        assert form.model.csb2 == csb2

    def test_model_other_engines(self) -> None:
        """The sound speeds should be ignored by the other engines."""
        form = self.form(engine=Engine.DEFAULT, css2="0.3", csb2="0.25")
        assert form.is_valid(), form.errors
        assert form.model is BAG

    def test_alpha_outside_model(self) -> None:
        r"""$\alpha$ outside the valid range of the model of the SSM should be a validation error."""
        form = self.form(engine=Engine.SSM, alpha="0.1", css2="1/4", csb2="0.3")
        assert not form.is_valid()
        assert "Invalid alpha" in str(form.non_field_errors())

    def test_model_invalid(self) -> None:
        """Sound speeds with which the model cannot be created should be a validation error for the SSM."""
        form = self.form(engine=Engine.SSM, css2="0.3", csb2="0.25")
        assert not form.is_valid()
        assert "Invalid sound speeds" in str(form.non_field_errors())
