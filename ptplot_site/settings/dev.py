"""Development settings for PTPlot"""

from .base import *  # pylint: disable=unused-wildcard-import, wildcard-import

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
INTERNAL_IPS = ["127.0.0.1"]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-5)qw0w+z9)*q145l8$n_@d+$dj0f++p)npdmrddazr5j$yu869"

INSTALLED_APPS.append("debug_toolbar")
# The Django debug toolbar middleware should be as early as possible,
# but it must come after any other middleware that encodes the response's content, such as GZipMiddleware.
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#add-the-middleware
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # type: ignore[index]  # Wildcard import from .base

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
