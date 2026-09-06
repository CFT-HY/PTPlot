"""Production settings for PTPlot."""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    "localhost",
    "ptplot.org",
    "ptplot-23.it.helsinki.fi",
    "128.214.48.116"
]
INTERNAL_IPS = ["127.0.0.1"]
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Enabling X-Frame-Options only in production makes it possible
# to embed a local development version of the site in an iframe for a reveal.js presentation.
MIDDLEWARE.append("django.middleware.clickjacking.XFrameOptionsMiddleware")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# The University of Helsinki virtual machine provides a Postfix configuration.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# These default values are OK for use with Postfix
# EMAIL_HOST = "localhost"
# EMAIL_HOST_PASSWORD = ""
# EMAIL_HOST_USER = ""
# EMAIL_PORT = 25
# EMAIL_USE_TLS = False
