"""GW spectrum engine choices."""

from ptplot.science.spectrum.base import ENGINE_SPECTRUM_CLASSES, Engine
from ptplot.science.spectrum.bpl2020 import PowerSpectrumBPL2020
from ptplot.science.spectrum.bpl2024 import PowerSpectrumBPL2024
from ptplot.science.spectrum.dbpl2021 import PowerSpectrumDBPL2021
from ptplot.science.spectrum.dbpl2024 import PowerSpectrumDBPL2024
from ptplot.science.spectrum.ssm import PowerSpectrumSSM

# -----
# Update this when adding new engines
# -----

ENGINE_SPECTRUM_CLASSES.update({
    Engine.BPL2020: PowerSpectrumBPL2020,
    Engine.BPL2024: PowerSpectrumBPL2024,
    Engine.DBPL2021: PowerSpectrumDBPL2021,
    Engine.DBPL2024: PowerSpectrumDBPL2024,
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
