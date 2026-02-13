#!/usr/bin/env bash
# shellcheck shell=bash

project_env_log() {
  if [[ "${PROJECT_ENV_DEBUG:-0}" == "1" ]]; then
    echo "[env.sh] $*" >&2
  fi
}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROJECT_ROOT

if [[ -d "$PROJECT_ROOT/bin" ]]; then
  export PATH="$PROJECT_ROOT/bin:$PATH"
fi

project_env_log "PROJECT_ROOT=$PROJECT_ROOT"
project_env_log "PATH=$PATH"
