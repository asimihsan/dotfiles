#!/usr/bin/env bash

set -uxo pipefail

sudo echo starting...

sudo softwareupdate --download --all --agree-to-license
brew update
brew upgrade
if command -v flutter; then
    flutter upgrade --force
fi
conda update --all --yes

rustup update stable
cargo install cargo-prefetch
cargo prefetch --top-deps=200
cargo prefetch --top-downloads=200

npm install --upgrade aws-cdk

brew doctor
if command -v flutter; then
    flutter doctor
fi

doom upgrade
doom sync
doom purge
doom env
