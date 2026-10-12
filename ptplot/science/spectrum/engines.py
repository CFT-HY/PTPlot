"""GW spectrum engine choices."""

from ptplot.science.spectrum.coswg20bpl import CosWG20bpl
from ptplot.science.spectrum.coswg24bpl import CosWG24bpl
from ptplot.science.spectrum.coswg24dbpl import CosWG24dbpl
from ptplot.science.spectrum.engine import ENGINE_SPECTRUM_CLASSES, Engine
from ptplot.science.spectrum.gh21dbpl import GH21dbpl
from ptplot.science.spectrum.ssm import PowerSpectrumSSM

# -----
# Update this when adding new engines
# -----

ENGINE_SPECTRUM_CLASSES.update({
    Engine.CosWG20bpl: CosWG20bpl,
    Engine.CosWG24bpl: CosWG24bpl,
    Engine.GH21dbpl: GH21dbpl,
    Engine.CosWG24dbpl: CosWG24dbpl,
    Engine.SSM: PowerSpectrumSSM,
})

# -----
# These are generated automatically
# -----

ENGINE_NAMES: dict[Engine, str] = {
    engine: spectrum.NAME
    for engine, spectrum in ENGINE_SPECTRUM_CLASSES.items()
}
ENGINE_NAMES[Engine.DEFAULT] += " (default)"
ENGINE_SHORT_NAMES: dict[Engine, str] = {
    engine: spectrum.SHORT_NAME
    for engine, spectrum in ENGINE_SPECTRUM_CLASSES.items()
}
ENGINE_CHOICES: tuple[tuple[Engine, str], ...] = tuple(ENGINE_NAMES.items())
