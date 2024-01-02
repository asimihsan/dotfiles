#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
pushd "$ROOT_DIR"
trap "popd" EXIT

poetry install
poetry run playwright install
pipx install poethepoet
