import os
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

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
