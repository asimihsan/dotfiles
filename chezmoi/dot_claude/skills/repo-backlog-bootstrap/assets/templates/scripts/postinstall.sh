#!/usr/bin/env bash
set -euo pipefail

# Keep this hook fast and idempotent.
# Add project-specific post-install setup here.

if [[ "${PROJECT_ENV_DEBUG:-0}" == "1" ]]; then
  echo "[postinstall.sh] no-op template hook"
fi
