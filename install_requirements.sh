#!/usr/bin/env bash
set -eu

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON="${PYTHON:-python3}"
# Resolve the environment that pip installs to, so that the cleanup below is applied
# to the same environment, regardless of where it is located.
SITE_PACKAGES="$("${PYTHON}" -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")"
echo "Installing to ${SITE_PACKAGES}"

# Numba stores its cache in the __pycache__ directories next to the source files,
# or in NUMBA_CACHE_DIR, if it's set.
# These files are not tracked by pip, and are therefore not removed by "pip uninstall".
clear_numba_cache() {
  local package="$1"
  if [ -d "${SITE_PACKAGES}/${package}" ]; then
    echo "Clearing the Numba cache of ${package} in ${SITE_PACKAGES}."
    find "${SITE_PACKAGES}/${package}" -type f \( -name "*.nbi" -o -name "*.nbc" \) -delete
  fi
  if [ -n "${NUMBA_CACHE_DIR:-}" ] && [ -d "${NUMBA_CACHE_DIR}" ]; then
    echo "Clearing the Numba cache of ${package} in ${NUMBA_CACHE_DIR}."
    find "${NUMBA_CACHE_DIR}" -type f -path "*${package}*" \( -name "*.nbi" -o -name "*.nbc" \) -delete
  fi
}

"${PYTHON}" -m pip install --upgrade pip wheel
# Packages that use a git commit hash in requirements.txt are not updated automatically.
if [ -d "${SITE_PACKAGES}/pttools" ]; then
  echo "Uninstalling existing PTtools."
  "${PYTHON}" -m pip uninstall pttools-gw -y
  clear_numba_cache pttools
  rm -rf "${SITE_PACKAGES}/pttools"
fi
"${PYTHON}" -m pip install --upgrade \
  -r "${SCRIPT_DIR}/requirements.txt" \
  -r "${SCRIPT_DIR}/requirements-dev.txt" \
  -r "${SCRIPT_DIR}/docs/requirements.txt"
