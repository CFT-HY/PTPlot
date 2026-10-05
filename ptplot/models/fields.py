"""Custom fields for the database models."""

import typing as tp

from django.db import models


class LatexFloatField(models.FloatField):
    """A float field that also has a human-readable name with LaTeX symbols for the web pages."""

    def __init__(self, *args: tp.Any, verbose_name_latex: str | None = None, **kwargs: tp.Any) -> None:
        """Create the field.

        :param verbose_name_latex: Human-readable name with LaTeX symbols, defaults to the ``verbose_name``
        """
        super().__init__(*args, **kwargs)
        self._verbose_name_latex = verbose_name_latex

    @property
    def verbose_name_latex(self) -> str:
        """Human-readable name with LaTeX symbols."""
        return str(self.verbose_name) if self._verbose_name_latex is None else self._verbose_name_latex

    def deconstruct(self) -> tuple[str, str, tp.Sequence[tp.Any], dict[str, tp.Any]]:
        """Deconstruct the field for the migrations as a plain FloatField.

        The LaTeX name only affects the web pages and not the database,
        and therefore the migrations don't need to depend on this class.
        """
        name, _, args, kwargs = super().deconstruct()
        return name, "django.db.models.FloatField", args, kwargs
