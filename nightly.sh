#!/usr/bin/env bash
# Nightly plotting run: unit tests, documentation build (which runs the examples),
# and archiving of the resulting figures and documentation.
# This script is documented in `./docs/dev.rst`.
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${SCRIPT_DIR}"

DATE="$(date +%F)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/nightly_${DATE}.log"
FIG_DIR="${SCRIPT_DIR}/examples/fig"
FIG_ARCHIVE="${SCRIPT_DIR}/examples/fig_${DATE}.7z"
DOCS_BUILD_DIR="${SCRIPT_DIR}/docs/_build"
DOCS_ARCHIVE="${SCRIPT_DIR}/docs/nightly/docs_${DATE}.7z"
# The maximum age of the HEAD commit for the run to be started, in seconds.
MAX_COMMIT_AGE="${MAX_COMMIT_AGE:-86400}"

mkdir -p "${LOG_DIR}"
# Log both stdout and stderr of this script and of all its subprocesses.
exec >> "${LOG_FILE}" 2>&1

log() {
  echo "[$(date --iso-8601=seconds)] $*"
}

# Compress a directory to a 7-Zip archive.
archive() {
  local dir="$1"
  local archive="$2"
  if [ ! -d "${dir}" ]; then
    log "The directory ${dir} does not exist."
    return 1
  fi
  # 7-Zip appends to an existing archive instead of replacing it,
  # so a previous archive of the same day has to be removed.
  if [ -e "${archive}" ]; then
    log "Removing the existing archive ${archive}."
    rm -f "${archive}"
  fi
  mkdir -p "$(dirname "${archive}")"
  7z a -mx=9 "${archive}" "${dir}"
  log "${dir} archived to ${archive}."
}

on_error() {
  log "FAILED at line ${1} with exit code ${2}."
}
trap 'on_error "${LINENO}" "$?"' ERR

# Run only if the HEAD commit is recent, so that unchanged code is not rebuilt every night.
COMMIT_TIME="$(git log -1 --format=%ct HEAD)"
COMMIT_AGE=$(( $(date +%s) - COMMIT_TIME ))
if [ "${COMMIT_AGE}" -gt "${MAX_COMMIT_AGE}" ]; then
  log "HEAD ($(git rev-parse --short HEAD)) is $(( COMMIT_AGE / 3600 )) h old. Skipping the nightly run."
  exit 0
fi

log "Starting the nightly run at HEAD $(git rev-parse --short HEAD)."

# shellcheck disable=SC1091  # The virtualenv is not available at lint time.
source "${SCRIPT_DIR}/venv/bin/activate"

pytest
log "Unit tests finished."

make -C "${SCRIPT_DIR}/docs" all
log "Documentation build finished."

archive "${FIG_DIR}" "${FIG_ARCHIVE}"
archive "${DOCS_BUILD_DIR}" "${DOCS_ARCHIVE}"

log "Nightly run finished."
