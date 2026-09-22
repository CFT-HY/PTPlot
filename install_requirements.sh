#!/usr/bin/env bash
# Install the dependencies of PTPlot with uv.
# This creates the virtualenv ./.venv, installs the locked dependencies to it,
# and installs PTPlot itself there in editable mode.
set -eu

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Resolve the environment that uv syncs to, so that the cleanup below is applied
# to the same environment, regardless of where it is located.
VENV="${UV_PROJECT_ENVIRONMENT:-${SCRIPT_DIR}/.venv}"

# Find the site-packages directory of the environment, if the environment exists.
site_packages() {
  local dir
  for dir in "${VENV}"/lib/python*/site-packages "${VENV}"/Lib/site-packages; do
    if [ -d "${dir}" ]; then
      echo "${dir}"
      return
    fi
  done
}

# Find the Git commit of the installed PTtools, if it's installed from Git.
# uv records the source of such a package in its direct_url.json.
pttools_commit() {
  local sp file
  sp="$(site_packages)"
  if [ -z "${sp}" ]; then
    return
  fi
  for file in "${sp}"/pttools_gw-*.dist-info/direct_url.json; do
    if [ -f "${file}" ]; then
      sed -n 's/.*"commit_id"[[:space:]]*:[[:space:]]*"\([0-9a-fA-F]*\)".*/\1/p' "${file}"
      return
    fi
  done
}

# Numba stores its cache in the __pycache__ directories next to the source files,
# or in NUMBA_CACHE_DIR, if it's set.
# These files are not tracked by uv, and are therefore not removed when the package is updated.
clear_numba_cache() {
  local package="$1"
  local sp
  sp="$(site_packages)"
  if [ -n "${sp}" ] && [ -d "${sp}/${package}" ]; then
    echo "Clearing the Numba cache of ${package} in ${sp}."
    find "${sp}/${package}" -type f \( -name "*.nbi" -o -name "*.nbc" \) -delete
  fi
  if [ -n "${NUMBA_CACHE_DIR:-}" ] && [ -d "${NUMBA_CACHE_DIR}" ]; then
    echo "Clearing the Numba cache of ${package} in ${NUMBA_CACHE_DIR}."
    find "${NUMBA_CACHE_DIR}" -type f -path "*${package}*" \( -name "*.nbi" -o -name "*.nbc" \) -delete
  fi
}

# uv keys the packages that are installed from Git by their commit,
# and therefore it reinstalls PTtools when the commit in pyproject.toml is changed,
# even if the version number stays the same.
COMMIT_BEFORE="$(pttools_commit)"

echo "Installing to ${VENV}"
uv sync --project "${SCRIPT_DIR}" "$@"

COMMIT_AFTER="$(pttools_commit)"
if [ "${COMMIT_BEFORE}" != "${COMMIT_AFTER}" ]; then
  echo "PTtools was updated from \"${COMMIT_BEFORE:-none}\" to \"${COMMIT_AFTER:-none}\"."
  clear_numba_cache pttools
fi
