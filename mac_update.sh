#!/usr/bin/env bash

set -uxo pipefail

sudo echo starting...

sudo softwareupdate --download --all --agree-to-license
brew update
brew upgrade
rustup update stable
flutter upgrade
conda update --all --yes
brew doctor
flutter doctor
