"""Enumeration of power spectrum engines."""

from enum import StrEnum
import logging
import typing as tp

from pttools.utils import IS_GITHUB_ACTIONS

if tp.TYPE_CHECKING:
    from ptplot.science.spectrum.base import PowerSpectrum

logger: logging.Logger = logging.getLogger(__name__)


class Engine(StrEnum):
    """Enumeration of power spectrum engines."""

    BPL2020 = DEFAULT = "bpl-2020"
    BPL2024 = "bpl-2024"
    DBPL2021 = "dbpl-2021"
    DBPL2024 = "dbpl-2024"
    SSM = "ssm"

    @classmethod
    def engine(cls, name: str | None, default: "Engine | None" = None) -> "Engine":
        """Get an engine by its name.

        :param name: Name of the engine
        :param default: Engine to return if the name is not given, defaults to ``DEFAULT``
        :return: Engine
        :raises ValueError: If there is no engine with the given name
        """
        return (cls.DEFAULT if default is None else default) if name is None or not name else Engine(name)

    @classmethod
    def engines(
            cls,
            engines: "Engine | str | tp.Iterable[Engine] | None" = None,
            fast: bool = False,
            log: bool = False) -> "list[Engine]":
        """Get the engines.

        :param engines: Engine or engines to be filtered. Using all engines if not given.
        :param fast: Return only engines that are fast
        :param log: Enable logging
        :return: Engines (list instead of set to preserve order)
        """
        engines2 = ([Engine(engines)] if isinstance(engines, str) else list(engines)) \
            if engines is not None and engines else cls
        get_all = not (fast and IS_GITHUB_ACTIONS)
        engines = [engine for engine in engines2 if get_all or (engine != cls.SSM)]
        if log:
            logger.info(
                "Enabled engines: %s (docs=%s, IS_GITHUB_ACTIONS=%s)",
                engines, fast, IS_GITHUB_ACTIONS
            )
        return engines

    @classmethod
    def non_default(cls, fast: bool = False, log: bool = False) -> "list[Engine]":
        """Get the non-default engines.

        :param fast: Return only engines that are fast
        :param log: Enable logging
        :return: Non-default engines (list instead of set to preserve order)
        """
        engines = [engine for engine in cls.engines(fast=fast) if engine != cls.DEFAULT]
        if log:
            logger.info(
                "Enabled non-default engines: %s (docs=%s, IS_GITHUB_ACTIONS=%s)",
                engines, fast, IS_GITHUB_ACTIONS
            )
        return engines

    @property
    def spectrum(self) -> type[PowerSpectrum]:
        """Power spectrum class of this engine."""
        return ENGINE_SPECTRUM_CLASSES[self]


ENGINE_SPECTRUM_CLASSES: dict[Engine, type[PowerSpectrum]] = {}
