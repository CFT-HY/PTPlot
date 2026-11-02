"""
WSGI config for ptplot_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.handlers.wsgi import WSGIHandler
from django.core.wsgi import get_wsgi_application

import ptplot.utils

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ptplot_site.settings")
# This has to be set before setting up Django, which imports the rest of PTPlot,
# as some of its constants, e.g. ptplot.science.plot.utils.DEFAULT_RC_CONTEXT, depend on it.
ptplot.utils._DJANGO = True  # noqa: SLF001

application: WSGIHandler = get_wsgi_application()
