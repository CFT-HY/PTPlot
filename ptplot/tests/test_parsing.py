"""Tests for the command-line argument parsing."""

import argparse

import pytest

from ptplot.science.parsing import engine_arg
from ptplot.science.spectrum import Engine


@pytest.mark.parametrize("engine", list(Engine))
def test_engine_arg(engine: Engine):
    """Both the internal names and the short names should be accepted, case-insensitively."""
    short_name = engine.spectrum.SHORT_NAME
    for value in (engine.value, engine.value.upper(), short_name, short_name.lower()):
        assert engine_arg(value) is engine


def test_engine_arg_invalid():
    """The old engine values without a year should be rejected."""
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid engine"):
        engine_arg("bpl")
