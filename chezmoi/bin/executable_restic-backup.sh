#!/usr/bin/env bash

set -euo pipefail

LEGACY_SCRIPT="${RESTIC_BACKUP_LEGACY_SCRIPT:-${HOME}/bin/restic-backup-legacy.sh}"
ASIM_UTILITIES_DIR="${ASIM_UTILITIES_DIR:-${HOME}/workplace/asim-utilities}"
USE_LEGACY="${RESTIC_BACKUP_USE_LEGACY:-0}"
AUTO_FALLBACK="${RESTIC_BACKUP_AUTO_FALLBACK:-1}"

# These commands are implemented by the Phase 1 Python CLI.
# Deferred commands still route to legacy shell implementation during cutover.
is_python_command() {
  case "$1" in
    backup | list | restore | forget | unlock)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_legacy() {
  if [[ ! -x "$LEGACY_SCRIPT" ]]; then
    printf 'legacy restic script not found or not executable: %s\n' "$LEGACY_SCRIPT" >&2
    printf 'Set RESTIC_BACKUP_LEGACY_SCRIPT to an executable fallback path if needed.\n' >&2
    return 1
  fi

  exec "$LEGACY_SCRIPT" "$@"
}

run_python() {
  local -a cmd=()

  if command -v uv >/dev/null 2>&1; then
    if [[ -d "$ASIM_UTILITIES_DIR" ]]; then
      cmd=(uv --directory "$ASIM_UTILITIES_DIR" run restic-backup)
    fi
  fi

  if [[ ${#cmd[@]} -eq 0 ]]; then
    if command -v restic-backup >/dev/null 2>&1; then
      cmd=(restic-backup)
    fi
  fi

  if [[ ${#cmd[@]} -eq 0 ]]; then
    printf 'unable to locate Python restic-backup CLI\n' >&2
    printf 'Expected one of:\n' >&2
    printf '  1) uv with asim-utilities checkout at %s\n' "$ASIM_UTILITIES_DIR" >&2
    printf '  2) restic-backup on PATH\n' >&2
    printf 'Bootstrap with: cd %s && uv sync\n' "$ASIM_UTILITIES_DIR" >&2
    return 127
  fi

  "${cmd[@]}" "$@"
}

usage() {
  cat <<'USAGE'
Usage: restic-backup.sh <command> [options]

Python-first commands:
  backup
  list
  restore
  forget
  unlock

Legacy-only commands (routed to restic-backup-legacy.sh):
  setup
  ls
  prune
  prune-cache
  mount
  stats

Environment controls:
  RESTIC_BACKUP_USE_LEGACY=1   Force all commands through legacy shell script.
  RESTIC_BACKUP_AUTO_FALLBACK=0 Disable automatic fallback when Python command fails.
  RESTIC_BACKUP_LEGACY_SCRIPT  Override legacy script path.
  ASIM_UTILITIES_DIR           Override Python project path for uv execution.
USAGE
}

main() {
  if [[ $# -eq 0 ]]; then
    if run_python --help; then
      exit 0
    fi
    if [[ "$AUTO_FALLBACK" == "1" ]]; then
      printf "Python restic-backup help failed, falling back to legacy shell path.\n" >&2
      run_legacy help
    fi
    usage
    exit 1
  fi

  case "$1" in
    --help | -h | help)
      usage
      exit 0
      ;;
  esac

  if [[ "$USE_LEGACY" == "1" ]]; then
    run_legacy "$@"
  fi

  if is_python_command "$1"; then
    if run_python "$@"; then
      exit 0
    else
      local python_status=$?

      if [[ "$AUTO_FALLBACK" != "1" ]]; then
        exit "$python_status"
      fi

      printf "Python restic-backup failed (exit %s), falling back to legacy shell path.\n" "$python_status" >&2
      run_legacy "$@"
    fi
  fi

  run_legacy "$@"
}

main "$@"
