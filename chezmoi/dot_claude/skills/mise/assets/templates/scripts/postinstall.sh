#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1 && [[ -f pyproject.toml ]]; then
  uv venv --clear
  uv sync
fi

if command -v npm >/dev/null 2>&1 && [[ -f package.json ]]; then
  npm install
fi
