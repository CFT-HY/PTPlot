#!/usr/bin/env bash
set -eu

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DJANGO_SETTINGS_MODULE="ptplot_site.settings.dev"

rm -f "${SCRIPT_DIR}/db.sqlite3"

# This step should be removed, once the migrations are pushed to Git.
rm "${SCRIPT_DIR}/ptplot/migrations/"0*_*.py
python manage.py makemigrations

python manage.py migrate
python manage.py populate
