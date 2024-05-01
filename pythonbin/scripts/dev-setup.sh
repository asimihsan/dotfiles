#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
pushd "$ROOT_DIR"
trap "popd" EXIT

poetry install
pip install --upgrade pip
pip install pipx
poetry run playwright install
pipx install poethepoet
brew install tesseract
brew install poppler

# Initialize unstructured, see [1]
# [1] https://github.com/Unstructured-IO/unstructured/blob/main/Dockerfile
poetry run python -c "import nltk; nltk.download('punkt')"
poetry run python -c "import nltk; nltk.download('averaged_perceptron_tagger')"
poetry run python -c "from unstructured.partition.model_init import initialize; initialize()"
