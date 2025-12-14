#!/usr/bin/env bash
set -euo pipefail

# Verify F* file with common options
# Usage: verify-fst.sh <file.fst> [options]

usage() {
  cat << EOF
Usage: $0 <file.fst> [options]

Options:
  --lax           Typecheck only (admit all VCs)
  --z3rlimit N    Set Z3 resource limit (default 5)
  -I, --include   Add include path (can repeat)
  --no-cache      Disable caching
  --use-hints     Use recorded hints
  --record-hints  Record hints for faster re-verification
  --query-stats   Show SMT query statistics

Examples:
  $0 src/Main.fst
  $0 --z3rlimit 60 src/Complex.fst
  $0 -I lib -I src src/Main.fst
EOF
  exit 1
}

[[ $# -lt 1 ]] && usage

# Collect files and options
FILES=()
OPTS=""
CACHE_DIR="${FSTAR_CACHE_DIR:-.fstar_cache}"
USE_CACHE=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --lax)
      OPTS="$OPTS --lax"
      shift
      ;;
    --z3rlimit)
      OPTS="$OPTS --z3rlimit $2"
      shift 2
      ;;
    -I|--include)
      OPTS="$OPTS --include $2"
      shift 2
      ;;
    --no-cache)
      USE_CACHE=false
      shift
      ;;
    --use-hints)
      OPTS="$OPTS --use_hints"
      shift
      ;;
    --record-hints)
      OPTS="$OPTS --record_hints"
      shift
      ;;
    --query-stats)
      OPTS="$OPTS --query_stats"
      shift
      ;;
    --help|-h)
      usage
      ;;
    -*)
      # Pass through other options
      OPTS="$OPTS $1"
      shift
      ;;
    *)
      # Assume it's a file
      FILES+=("$1")
      shift
      ;;
  esac
done

[[ ${#FILES[@]} -eq 0 ]] && usage

# Add caching if enabled
if $USE_CACHE; then
  mkdir -p "$CACHE_DIR"
  OPTS="--cache_checked_modules --cache_dir $CACHE_DIR $OPTS"
fi

# Run F*
exec fstar.exe $OPTS "${FILES[@]}"
