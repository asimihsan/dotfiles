#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
GLOBAL_NPM_PACKAGES_FILE="$SCRIPT_DIR/global-npm-packages.txt"

xargs npm update -g < "$GLOBAL_NPM_PACKAGES_FILE"
