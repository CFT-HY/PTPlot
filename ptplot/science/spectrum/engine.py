"""GW spectrum engine choices"""

from ptplot.science.spectrum.base import Engine, ENGINE_SPECTRUM_CLASSES
from ptplot.science.spectrum.bpl import PowerSpectrumBPL
from ptplot.science.spectrum.dbpl import PowerSpectrumDBPL
from ptplot.science.spectrum.ssm import PowerSpectrumSSM

# -----
# Update this when adding new engines
# -----

ENGINE_SPECTRUM_CLASSES.update({
    Engine.BPL: PowerSpectrumBPL,
    Engine.DBPL: PowerSpectrumDBPL,
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
