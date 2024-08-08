#!/usr/bin/env bash

set -euo pipefail

echo $(dirname $(dirname $(readlink -f $(which java))))
