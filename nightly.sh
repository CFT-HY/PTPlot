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
DOCS_BUILD_DIR="${SCRIPT_DIR}/docs/_build"
ARCHIVE="${SCRIPT_DIR}/docs/nightly/nightly_${DATE}.7z"
# The maximum age of the HEAD commit for the run to be started, in seconds.
MAX_COMMIT_AGE="${MAX_COMMIT_AGE:-86400}"

mkdir -p "${LOG_DIR}"
# Log both stdout and stderr of this script and of all its subprocesses.
exec >> "${LOG_FILE}" 2>&1

log() {
  echo "[$(date --iso-8601=seconds)] $*"
}

# Compress directories to a 7-Zip archive.
# Usage: archive ARCHIVE DIR...
archive() {
  local archive="$1"
  shift
  local dir
  for dir in "$@"; do
    if [ ! -d "${dir}" ]; then
      log "The directory ${dir} does not exist."
      return 1
    fi
  done
  # 7-Zip appends to an existing archive instead of replacing it,
  # so if there is already an archive of the same day, a suffix _2, _3 etc. is added to the filename.
  local base="${archive%.7z}"
  local i=2
  while [ -e "${archive}" ]; do
    archive="${base}_${i}.7z"
    i=$(( i + 1 ))
  done
  mkdir -p "$(dirname "${archive}")"
  7z a -mx=9 "${archive}" "$@"
  log "$* archived to ${archive}."
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

# Cron runs with a minimal PATH, which does not include the user-specific directories
# where the standalone installer of uv puts it.
# $UV_INSTALL_DIR and $XDG_BIN_HOME are the custom installation directories supported by the installer,
# ~/.local/bin is its default, and ~/.cargo/bin is the default of older uv versions.
for dir in "${HOME}/.cargo/bin" "${HOME}/.local/bin" "${XDG_BIN_HOME:-}" "${UV_INSTALL_DIR:-}"; do
  if [ -n "${dir}" ] && [ -d "${dir}" ]; then
    PATH="${dir}:${PATH}"
  fi
done
export PATH
if ! command -v uv &> /dev/null; then
  log "uv was not found in PATH: ${PATH}"
  exit 1
fi
log "Using $(command -v uv) ($(uv --version))."

# Run in the virtualenv that uv manages.
# The --frozen ensures that the locked dependency versions are used as they are,
# without updating uv.lock.
UV="uv run --frozen --project ${SCRIPT_DIR}"

${UV} pytest
log "Unit tests finished."

${UV} make -C "${SCRIPT_DIR}/docs" all
log "Documentation build finished."

archive "${ARCHIVE}" "${DOCS_BUILD_DIR}" "${FIG_DIR}"

log "Nightly run finished."
