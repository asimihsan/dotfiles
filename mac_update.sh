#!/usr/bin/env bash

set -uxo pipefail

sudo echo starting...

sudo softwareupdate --download --all --agree-to-license
brew update
brew upgrade
[[ $(command -v flutter &>/dev/null) ]] && flutter upgrade
conda update --all --yes

rustup update stable
cargo install cargo-prefetch
cargo prefetch --top-deps=200
cargo prefetch --top-downloads=200

brew doctor
[[ $(command -v flutter &>/dev/null) ]] && flutter doctor
