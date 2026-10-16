"""Tests for the enumeration of the power spectrum engines."""

from ptplot.science.spectrum.engine import STRONG_ENGINES, Engine


def test_engines_all() -> None:
    """All engines should be returned by default, including those for strong transitions only."""
    assert Engine.engines() == list(Engine)


def test_engines_not_strong() -> None:
    """strong=False should exclude CosWG24bpl and keep the order of the other engines."""
    assert {Engine.CosWG24bpl} == STRONG_ENGINES
    assert Engine.engines(strong=False) == [engine for engine in Engine if engine != Engine.CosWG24bpl]


def test_engines_not_strong_given() -> None:
    """strong=False should also filter the given engines."""
    assert Engine.engines([Engine.CosWG24bpl, Engine.GH21dbpl], strong=False) == [Engine.GH21dbpl]
    assert Engine.engines("CosWG24bpl", strong=False) == []
    assert Engine.engines("CosWG24bpl") == [Engine.CosWG24bpl]
