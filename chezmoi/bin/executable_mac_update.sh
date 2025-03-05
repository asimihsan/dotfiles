#!/usr/bin/env bash

set -uo pipefail

function cache_sudo_credentials() {
    sudo -v
}

cache_sudo_credentials
echo starting...

update_dotfiles() {
    local dotfiles_dir="$HOME/.dotfiles"

    if [[ ! -d "$dotfiles_dir" ]]; then
        echo "No ~/.dotfiles directory found, skipping git update"
        return 0
    fi

    cd "$dotfiles_dir" || {
        echo "Failed to change directory to $dotfiles_dir"
        return 1
    }

    # echo "Updating dotfiles repository..."

    # if ! git town sync; then
    #     echo "Failed to git town sync"
    #     return 1
    # fi
}

update_dotfiles

"$HOME"/.dotfiles/install
cp "$(devbox global path)/devbox.{lock,json}" ~/.dotfiles/chezmoi/dot_local/share/devbox/global/default/

chezmoi update
chezmoi upgrade
chezmoi apply

devbox global update
cp "$(devbox global path)/devbox.{lock,json}" ~/.dotfiles/chezmoi/dot_local/share/devbox/global/default/

sudo softwareupdate --download --all --agree-to-license
brew update
brew upgrade

if command -v flutter; then
    flutter upgrade --force
fi

mise cache clear
mise install
mise upgrade

rustup update stable
cargo install cargo-binstall
cargo binstall --no-confirm lazyjj

~/bin/install-npm-global.sh
npm update -g

brew doctor
if command -v flutter; then
    flutter doctor
fi

dotnet tool update --global P
gh extension upgrade gh-copilot

brew bundle install
