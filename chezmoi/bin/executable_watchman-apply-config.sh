#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: watchman-apply-config.sh [--force] [--reload] [ROOT_DIR]

Apply the universal Watchman per-project config to ROOT_DIR/.watchmanconfig.

Options:
  --force    Overwrite an existing .watchmanconfig in ROOT_DIR.
  --reload   After writing config, reload the watch with watchman watch-project.
  -h, --help Show this help.

Environment:
  WATCHMAN_UNIVERSAL_CONFIG
      Optional override for config source path.
      Default: ~/.config/watchman/watchmanconfig-universal.json
EOF
}

force=0
reload_watchman=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=1
      shift
      ;;
    --reload)
      reload_watchman=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi

root_dir="${1:-$PWD}"
root_dir="${root_dir%/}"
if [[ -z "$root_dir" ]]; then
  root_dir="/"
fi

if [[ ! -d "$root_dir" ]]; then
  echo "Root directory does not exist: $root_dir" >&2
  exit 1
fi

source_config="${WATCHMAN_UNIVERSAL_CONFIG:-$HOME/.config/watchman/watchmanconfig-universal.json}"
target_config="$root_dir/.watchmanconfig"

if [[ ! -f "$source_config" ]]; then
  echo "Source config not found: $source_config" >&2
  echo "Run chezmoi apply first so ~/.config/watchman/watchmanconfig-universal.json exists." >&2
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  if ! jq -e . "$source_config" >/dev/null 2>&1; then
    echo "Source config is invalid JSON: $source_config" >&2
    exit 1
  fi
fi

if [[ -f "$target_config" ]] && [[ "$force" -ne 1 ]]; then
  echo "Refusing to overwrite existing file: $target_config" >&2
  echo "Re-run with --force if you want to replace it." >&2
  exit 1
fi

install -m 0644 "$source_config" "$target_config"
echo "Installed $target_config from $source_config"

if [[ "$reload_watchman" -eq 1 ]]; then
  if ! command -v watchman >/dev/null 2>&1; then
    echo "watchman is not available on PATH; skipped reload." >&2
    exit 0
  fi

  watchman watch-del "$root_dir" >/dev/null 2>&1 || true
  if watchman watch-project "$root_dir" >/dev/null 2>&1; then
    echo "Reloaded watchman watch for $root_dir"
  else
    echo "watchman watch-project failed for $root_dir" >&2
    exit 1
  fi
fi
