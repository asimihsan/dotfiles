#!/usr/bin/env bash

set -uo pipefail

# Function: cache_sudo_credentials
#
# Description:
#   This function caches sudo credentials by running 'sudo -v' and blocks
#   until authentication succeeds. It also sets up a trap to refresh the
#   sudo timestamp every 5 minutes to keep the sudo session alive.
#
# Usage:
#   cache_sudo_credentials
#
# Example:
#   cache_sudo_credentials
#   # Your script logic here
#   # Sudo commands will now work without prompting for a password
#
function cache_sudo_credentials() {
    local sudo_refresh_pid

    # Function to kill the sudo refresh process
    kill_sudo_refresh() {
        if [ ! -z "$sudo_refresh_pid" ]; then
            echo "Killing sudo refresh process (PID: $sudo_refresh_pid)"
            kill $sudo_refresh_pid 2>/dev/null
        fi
    }

    # Set up the trap
    trap kill_sudo_refresh EXIT INT TERM

    # Check if sudo authentication was successful
    if ! sudo -v; then
        echo "Sudo authentication failed"
        return 1
    fi

    # Start a background process to keep sudo credentials alive
    (
        while true; do
            sudo -v
            sleep 300  # Refresh every 5 minutes
        done
    ) &
    sudo_refresh_pid=$!

    echo "Sudo credentials cached and will be refreshed every 5 minutes (PID: $sudo_refresh_pid)"
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
    
    if git diff-index --quiet HEAD --; then
        # Repository is clean, proceed with rebase
        if git pull --rebase; then
            echo "Successfully updated dotfiles"
            return 0
        else
            echo "Failed to rebase dotfiles"
            return 1
        fi
    else
        # Repository is dirty
        echo "Warning: The dotfiles repository has uncommitted changes"
        echo "Please commit or stash your changes before updating"
        
        # Optionally, we can show the status of the repo
        git status --short
        
        return 1
    fi
}

update_dotfiles

"$HOME"/.dotfiles/install
chezmoi --source ~/.dotfiles/chezmoi update
chezmoi --source ~/.dotfiles/chezmoi upgrade
chezmoi --source ~/.dotfiles/chezmoi apply

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
