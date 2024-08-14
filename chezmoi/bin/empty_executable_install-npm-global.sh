#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
GLOBAL_NPM_PACKAGES_FILE="$SCRIPT_DIR/global-npm-packages.txt"

# Read packages from file and install globally
while read package; do
  echo "Installing $package..."
  npm install -g "$package"
done < "$GLOBAL_NPM_PACKAGES_FILE"

# Alternatively, if using package.json:
# npm install -g $(jq -r '.dependencies | keys[]' ~/dotfiles/global-npm-packages.json)
