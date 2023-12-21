#!/usr/bin/env zsh

set -uo pipefail

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

npm install --ugprade npm
npm install --upgrade aws-cdk
hishtory update

brew doctor
if command -v flutter; then
    flutter doctor
fi

dotnet tool update --global P
gh extension upgrade gh-copilot
