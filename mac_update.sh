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
    
    echo "Updating dotfiles repository..."
    
    if ! git fetch; then
        echo "Failed to fetch updates from remote"
        return 1
    fi

    if ! git pull --autostash --rebase; then
        echo "Failed to pull updates from remote"
        return 1
    fi
}

update_dotfiles

"$HOME"/.dotfiles/install
chezmoi update
chezmoi upgrade
chezmoi apply

devbox global update

sudo softwareupdate --download --all --agree-to-license
brew update
brew upgrade

(cd ~/.dotfiles && git pull --rebase)

if command -v flutter; then
    flutter upgrade --force
fi

rustup update stable
cargo install cargo-prefetch
cargo prefetch --top-deps=200
cargo prefetch --top-downloads=200

npm install --ugprade npm
npm install --upgrade aws-cdk
npm install --upgrade '@githubnext/github-copilot-cli'

brew doctor
if command -v flutter; then
    flutter doctor
fi

dotnet tool update --global P
gh extension upgrade gh-copilot
