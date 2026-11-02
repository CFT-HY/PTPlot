#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import ptplot.utils


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ptplot_site.settings.dev")
    try:
        from django.core.management import execute_from_command_line  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    if sys.argv[1:2] == ["runserver"]:
        # This has to be set before setting up Django, which imports the rest of PTPlot,
        # as some of its constants, e.g. ptplot.science.plot.utils.DEFAULT_RC_CONTEXT, depend on it.
        # The development server loads ptplot_site.wsgi only after setting up Django.
        ptplot.utils._DJANGO = True  # noqa: SLF001
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
