#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <target-dir> [--force]"
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
fi

TARGET_DIR="$1"
FORCE=0
if [[ "${2:-}" == "--force" ]]; then
  FORCE=1
elif [[ $# -eq 2 ]]; then
  usage
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$SKILL_DIR/assets/templates"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Template directory not found: $TEMPLATE_DIR" >&2
  exit 1
fi

if [[ -e "$TARGET_DIR" && "$FORCE" -ne 1 ]]; then
  if [[ -n "$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    echo "Target directory is not empty. Re-run with --force to overwrite template files." >&2
    exit 1
  fi
fi

mkdir -p "$TARGET_DIR/scripts"

cp "$TEMPLATE_DIR/mise.toml" "$TARGET_DIR/mise.toml"
cp "$TEMPLATE_DIR/tasks.core.toml" "$TARGET_DIR/tasks.core.toml"
cp "$TEMPLATE_DIR/scripts/env.sh" "$TARGET_DIR/scripts/env.sh"
cp "$TEMPLATE_DIR/scripts/postinstall.sh" "$TARGET_DIR/scripts/postinstall.sh"

chmod +x "$TARGET_DIR/scripts/env.sh" "$TARGET_DIR/scripts/postinstall.sh"

echo "Scaffolded mise project in $TARGET_DIR"
echo "Next steps:"
echo "1) Edit $TARGET_DIR/mise.toml tool versions and task includes"
echo "2) Replace placeholder task commands in $TARGET_DIR/tasks.core.toml"
echo "3) Run: cd $TARGET_DIR && mise trust && mise install && mise run doctor"
