#!/usr/bin/env bash

set -euo pipefail

eval "$(devbox global shellenv)"
eval "$(/opt/homebrew/bin/mise activate bash)"

atuin daemon
