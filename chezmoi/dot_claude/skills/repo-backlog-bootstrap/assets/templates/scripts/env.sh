#!/usr/bin/env bash
set -euo pipefail

# Place project-specific environment setup here.
# Example:
# export AWS_REGION=us-west-2

if [[ "${PROJECT_ENV_DEBUG:-0}" == "1" ]]; then
  echo "[env.sh] sourced ${BASH_SOURCE[0]}"
fi
