#!/usr/bin/env bash

set -uo pipefail

function cache_sudo_credentials() {
    sudo -v
}

cache_sudo_credentials
echo starting...

mise cache clear
mise install
mise upgrade --yes
mise prune --yes

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

chezmoi update
chezmoi upgrade
chezmoi apply

devbox global update
eval "$(devbox global shellenv --recompute)"

sudo softwareupdate --download --all --agree-to-license
brew update
brew upgrade

rustup update stable
cargo binstall --no-confirm lazyjj
cargo binstall --no-confirm monolith

~/bin/install-npm-global.sh
claude update

brew doctor
if command -v flutter; then
    flutter doctor
fi

dotnet tool update --global P
gh extension upgrade gh-copilot

brew bundle install
xattr -cr /Applications/Chromium.app

~/bin/copy-to-backup.sh
