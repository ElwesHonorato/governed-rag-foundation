#!/usr/bin/env bash
set -euo pipefail

: <<'DOC'
Repository Python Bootstrap (pyenv)

────────────────────────────────────────────────────────
HOW TO USE
────────────────────────────────────────────────────────

Run from anywhere:

  ./script.sh

This will:
  • Ensure pyenv is installed
  • Install Python 3.11.14 (if missing)
  • Pin it locally in this repository (.python-version)

To automatically enable pyenv in new shells:

  ./script.sh --enable-pyenv-in-shell

After that, restart your shell:

  exec "$SHELL"

────────────────────────────────────────────────────────
WHAT THIS SCRIPT DOES
────────────────────────────────────────────────────────

1. Shows current python resolution.
2. Installs pyenv if missing.
3. Optionally appends pyenv init to ~/.bashrc and ~/.zshrc (opt-in).
4. Initializes pyenv in the current process.
5. Installs EXPECTED_VERSION via pyenv.
6. Writes .python-version at the repository root.
7. Prints final interpreter resolution.

────────────────────────────────────────────────────────
DESIGN PRINCIPLES
────────────────────────────────────────────────────────

• Fail fast (set -euo pipefail)
• Do not modify shell config unless explicitly requested
• Keep Python version pinned per-repository (never global)
• Be idempotent (safe to re-run)

If something fails:
  - Missing build deps → install your system's Python build dependencies.
  - pyenv not active → restart your shell or run with --enable-pyenv-in-shell.

DOC

EXPECTED_VERSION="3.11.14"

# Resolve script location and infer repository root (two levels up).
# This assumes script lives under something like repo/scripts/... .
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Simple logging helpers.
log() { printf '%s\n' "$*"; }
die() { log "Error: $*"; exit 1; }

# Check if a command exists in PATH.
have() { command -v "$1" >/dev/null 2>&1; }

show_local_python() {
  : <<'DOC'
Print current python resolution before pyenv changes anything.

Why this matters:
  - Debugging pyenv issues is mostly PATH + shell init related.
  - Showing both python and python3 clarifies environment state.
DOC

  local p
  if p="$(command -v python 2>/dev/null)"; then
    log "Current python:  ${p} ($("${p}" --version 2>&1))"
  else
    log "Current python:  not found"
  fi

  if p="$(command -v python3 2>/dev/null)"; then
    log "Current python3: ${p} ($("${p}" --version 2>&1))"
  else
    log "Current python3: not found"
  fi
}

ensure_prereqs_for_install() {
  : <<'DOC'
Validate minimal prerequisites for installing pyenv via https://pyenv.run.

This does NOT validate CPython build dependencies (gcc, zlib, openssl, etc).
If Python compilation fails, that is a system-level package issue.
DOC

  have curl || die "curl is required."
  have git  || die "git is required."
}

ensure_pyenv() {
  : <<'DOC'
Ensure pyenv is installed and available in this shell session.

Behavior:
  1. If pyenv is already in PATH, do nothing.
  2. If installed but not on PATH, adjust PATH for this process.
  3. Otherwise, install via https://pyenv.run.
DOC

  if have pyenv; then
    return 0
  fi

  # pyenv may already be installed but not on PATH in this shell.
  export PYENV_ROOT="${HOME}/.pyenv"
  if [[ -x "${PYENV_ROOT}/bin/pyenv" ]]; then
    export PATH="${PYENV_ROOT}/bin:${PATH}"
    have pyenv && return 0
  fi

  ensure_prereqs_for_install
  log "pyenv not found. Installing pyenv via https://pyenv.run ..."
  curl -fsSL https://pyenv.run | bash

  # Make it available in *this* process right now.
  export PATH="${PYENV_ROOT}/bin:${PATH}"

  have pyenv || die "pyenv install finished but pyenv is still not on PATH (${PYENV_ROOT}/bin)."
}

load_pyenv_for_current_shell() {
  : <<'DOC'
Initialize pyenv for the current process.

This allows:
  - `pyenv install`
  - `pyenv local`
  - `python` resolution through shims

Note:
  This affects only the current script process. It does NOT persist across shells
  unless rc files are modified.
DOC

  export PYENV_ROOT="${HOME}/.pyenv"
  export PATH="${PYENV_ROOT}/bin:${PATH}"

  # Ensure pyenv is callable before eval.
  have pyenv || die "pyenv not found on PATH after setting PYENV_ROOT."

  eval "$(pyenv init - bash)"
}

maybe_update_rc_files() {
  : <<'DOC'
Optionally persist pyenv initialization into user shell rc files.

Trigger:
  Only executes if first argument equals "--enable-pyenv-in-shell".

Behavior:
  - Appends a clearly marked block to ~/.bashrc and ~/.zshrc.
  - Uses marker guards to ensure idempotency.
  - Does NOT overwrite existing config.
  - Does NOT remove old config.
DOC

  [[ "${1:-}" == "--enable-pyenv-in-shell" ]] || return 0

  local bashrc="${HOME}/.bashrc"
  local zshrc="${HOME}/.zshrc"
  local marker_begin="# >>> pyenv setup (added by repo script) >>>"
  local marker_end="# <<< pyenv setup (added by repo script) <<<"

  append_block_once() {
    : <<'DOC'
Append pyenv init block once per rc file.

If marker is found, skip to prevent duplication.
DOC
    local rc="$1"
    local init_cmd="$2"

    [[ -f "${rc}" ]] || return 0
    if grep -Fq "${marker_begin}" "${rc}"; then
      return 0
    fi

    {
      echo ""
      echo "${marker_begin}"
      echo 'export PYENV_ROOT="$HOME/.pyenv"'
      echo 'export PATH="$PYENV_ROOT/bin:$PATH"'
      echo "${init_cmd}"
      echo "${marker_end}"
    } >> "${rc}"
  }

  append_block_once "${bashrc}" 'eval "$(pyenv init - bash)"'
  append_block_once "${zshrc}"  'eval "$(pyenv init - zsh)"'

  log "Updated rc files (opt-in): ${bashrc} / ${zshrc}"
}

install_python_version() {
  : <<'DOC'
Install EXPECTED_VERSION using pyenv.

The -s flag makes installation idempotent:
  - If version already exists, no-op.
DOC

  log "Installing Python ${EXPECTED_VERSION} with pyenv (if missing)..."
  pyenv install -s "${EXPECTED_VERSION}"
}

set_local_version() {
  : <<'DOC'
Pin repository-local Python version.

Writes `.python-version` in REPO_ROOT so that:
  - Any pyenv-enabled shell entering this directory tree
    will use EXPECTED_VERSION automatically.
DOC

  cd "${REPO_ROOT}"
  pyenv local "${EXPECTED_VERSION}"
  log "Set local python version in ${REPO_ROOT}/.python-version -> ${EXPECTED_VERSION}"
}

show_result() {
  : <<'DOC'
Display final interpreter resolution after pyenv configuration.

This confirms:
  - pyenv is installed
  - correct version selected
  - shims resolving correctly
DOC

  cd "${REPO_ROOT}"
  log "pyenv version: $(pyenv --version)"
  log "Local pyenv selection: $(pyenv version-name)"
  log "python resolves to: $(pyenv which python)"
  log "python --version: $(python --version 2>&1)"
}

main() {
  : <<'DOC'
Execution flow orchestrator.

Sequence:
  1. Show current Python resolution.
  2. Ensure pyenv installed.
  3. Optionally update shell rc.
  4. Initialize pyenv in this process.
  5. Install expected Python version.
  6. Pin local version.
  7. Display final state.
DOC

  show_local_python
  ensure_pyenv
  maybe_update_rc_files "${1:-}"
  load_pyenv_for_current_shell
  install_python_version
  set_local_version
  show_result

  if [[ "${1:-}" == "--enable-pyenv-in-shell" ]]; then
    log 'Done. Open a new shell (or run: exec "$SHELL") to load rc changes.'
  else
    log 'Done. To enable pyenv automatically in new shells, re-run with --enable-pyenv-in-shell (or add pyenv init to your rc manually).'
  fi
}

main "$@"