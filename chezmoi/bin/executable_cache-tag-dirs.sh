#!/usr/bin/env bash

# cache-tag-dirs.sh — tag cachey build dirs so backup tools can skip them
# Usage:
#   cache-tag-dirs.sh [-n|--dry-run] [--force] [ROOT ...]
# Examples:
#   cache-tag-dirs.sh                # defaults to: Downloads workplace
#   cache-tag-dirs.sh -n Projects .  # dry run on Projects and current dir
#   cache-tag-dirs.sh --force ~/src  # rewrite tag files if present

set -euo pipefail

IFS=$'\n\t'

# -----------------------------------------------------------------------------
#    Config
# -----------------------------------------------------------------------------
SIGNATURE="Signature: 8a477f597d28d172789f06886806bc55"
# Default search roots if none provided
DEFAULT_ROOTS=( "Downloads" "workplace" )

DRY_RUN=false
FORCE=false
ROOTS=()
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#    Arg parsing
# -----------------------------------------------------------------------------
while (( $# )); do
  case "${1:-}" in
    -n|--dry-run) DRY_RUN=true; shift;;
    --force)      FORCE=true;   shift;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
    --) shift; break;;
    -*) echo "error: unknown flag: $1" >&2; exit 2;;
    *)  ROOTS+=( "$1" ); shift;;
  esac
done
# -----------------------------------------------------------------------------

# Accept any remaining positional args as roots too (after --)
if (( $# )); then
  ROOTS+=( "$@" )
fi
# Fallback to defaults
if (( ${#ROOTS[@]} == 0 )); then
  ROOTS=( "${DEFAULT_ROOTS[@]}" )
fi

log() { printf '%s\n' "$*" >&2; }

write_tag() {
  # $1 = dir
  local d="$1" f="$1/CACHEDIR.TAG"
  if [[ -f "$f" && $FORCE == false ]]; then
    log "skip (exists): $f"
    return 0
  fi
  if $DRY_RUN; then
    log "tag: $d"
  else
    printf "%s\n" "$SIGNATURE" > "$f"
    log "wrote: $f"
  fi
}

# -----------------------------------------------------------------------------
#    Node — outermost node_modules
# -----------------------------------------------------------------------------
tag_node_modules() {
  find "${ROOTS[@]}" \
    -type d -name node_modules -prune -print0 \
  | while IFS= read -r -d '' d; do
      write_tag "$d"
    done
}
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#    Python — .venv
# -----------------------------------------------------------------------------
tag_python_venv() {
  find "${ROOTS[@]}" \
    -type d -name .venv -prune -print0 \
  | while IFS= read -r -d '' d; do
      write_tag "$d"
    done
}
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#    Rust — target only if parent has Cargo.toml
# -----------------------------------------------------------------------------
tag_rust_target() {
  find "${ROOTS[@]}" \
    -type d -name target -prune -print0 \
  | while IFS= read -r -d '' d; do
      local parent
      parent="$(dirname "$d")"
      if [[ -f "$parent/Cargo.toml" ]]; then
        write_tag "$d"
      else
        log "skip (no Cargo.toml): $d"
      fi
    done
}
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#    Run
# -----------------------------------------------------------------------------
log "roots: ${ROOTS[*]}"
$DRY_RUN && log "(dry run)"
$FORCE   && log "(force)"

tag_node_modules
tag_python_venv
tag_rust_target
