#!/usr/bin/env bash
set -eu

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

pip install --upgrade pip wheel
# Packages that use a git commit hash in requirements.txt is not updated automatically.
if [ -d "${SCRIPT_DIR}/venv/lib/python"*"/site-packages/pttools" ]; then
  echo "Uninstalling existing PTtools."
  pip uninstall pttools-gw -y
  echo "Clearing Numba cache for PTtools."
  rm -rf "${SCRIPT_DIR}/venv/lib/python"*"/site-packages/pttools/**/*.nbi"
fi
pip install --upgrade \
  -r "${SCRIPT_DIR}/requirements.txt" \
  -r "${SCRIPT_DIR}/requirements-dev.txt" \
  -r "${SCRIPT_DIR}/docs/requirements.txt"
