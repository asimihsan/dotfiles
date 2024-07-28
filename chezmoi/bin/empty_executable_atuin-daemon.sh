#!/usr/bin/env bash

set -euo pipefail

eval "$(devbox global shellenv)"

atuin daemon
