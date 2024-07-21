#!/usr/bin/env bash

# Mac Setup Script
#
# This script sets up a new Mac with essential tools and configurations.
#
# Environment Variables:
# SETUP_GITHUB: Set to 'true' to set up GitHub SSH key (default: true)
# SETUP_DOTFILES: Set to 'true' to clone and set up dotfiles (default: true)
# GITHUB_USERNAME: Your GitHub username (required if SETUP_GITHUB or SETUP_DOTFILES is true)
# DOTFILES_REPO: Your dotfiles repository name (default: dotfiles)
# CONFIGURE_MAC: Set to 'true' to configure Mac settings (default: true)
#
# Usage:
#
#   export GITHUB_USERNAME=foobar
#   ./setup_mac.sh

set -euo pipefail

SETUP_GITHUB="${SETUP_GITHUB:-true}"
SETUP_DOTFILES="${SETUP_DOTFILES:-true}"
CONFIGURE_MAC="${CONFIGURE_MAC:-true}"

# Logging
LOG_FILE="$HOME/setup_mac.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Error handling
trap 'echo "Error occurred. Check the log file: $LOG_FILE" >&2' ERR

# Fancy echo function
fancy_echo() {
    local fmt="$1"
    shift
    printf "\\n$fmt\\n" "$@"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Xcode Command Line Tools
install_xcode_clt() {
    fancy_echo "Checking for Xcode Command Line Tools..."
    if ! xcode-select -p &>/dev/null; then
        fancy_echo "Installing Xcode Command Line Tools..."
        xcode-select --install
        until xcode-select -p &>/dev/null; do
            sleep 5
        done
        fancy_echo "Xcode Command Line Tools installed successfully."
    else
        fancy_echo "Xcode Command Line Tools already installed."
    fi
}

# Function to install Homebrew
install_homebrew() {
    if ! command_exists brew; then
        fancy_echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        fancy_echo "Homebrew already installed."
    fi
}

# Function to install Nix and Devbox
install_nix_and_devbox() {
    if ! command_exists nix; then
        fancy_echo "Installing Nix..."
        curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
    else
        fancy_echo "Nix already installed."
    fi

    if ! command_exists devbox; then
        fancy_echo "Installing Devbox..."
        curl -fsSL https://get.jetify.com/devbox | FORCE=1 bash
    else
        fancy_echo "Devbox already installed."
    fi
}

# Function to set up SSH key and add to GitHub
setup_ssh_and_github() {
    if [ "${SETUP_GITHUB:-false}" != "true" ]; then
        fancy_echo "Skipping GitHub SSH setup."
        return
    fi

    if [ -z "${GITHUB_USERNAME:-}" ]; then
        fancy_echo "Error: GITHUB_USERNAME is required for GitHub setup." >&2
        exit 1
    fi

    local ssh_key="$HOME/.ssh/id_ed25519"
    local ssh_key_pub="${ssh_key}.pub"

    # Generate SSH key if it doesn't exist
    if [ ! -f "$ssh_key" ]; then
        fancy_echo "Generating new SSH key..."
        ssh-keygen -t ed25519 -C "${GITHUB_USERNAME}@users.noreply.github.com" -f "$ssh_key" -N ""
    else
        fancy_echo "SSH key already exists."
    fi

    # Ensure SSH agent is running and key is added
    eval "$(ssh-agent -s)"
    ssh-add --apple-use-keychain "$ssh_key"

    # Function to check if SSH key is already added to GitHub
    is_key_on_github() {
        if command_exists gh; then
            gh ssh-key list | grep -q "$(cat "$ssh_key_pub" | cut -d ' ' -f 2)"
        else
            fancy_echo "GitHub CLI not installed. Unable to check if key is already on GitHub."
            return 1
        fi
    }

    # Add SSH key to GitHub if not already added
    if ! is_key_on_github; then
        fancy_echo "Adding SSH key to GitHub..."
        if command_exists gh; then
            if ! gh auth status &>/dev/null; then
                fancy_echo "Please authenticate with GitHub CLI..."
                gh auth login -s admin:public_key -s admin:ssh_signing_key
            fi

            gh ssh-key add "$ssh_key_pub" --title "$(hostname)"
            if is_key_on_github; then
                fancy_echo "SSH key successfully added to GitHub."
            else
                fancy_echo "Failed to add SSH key to GitHub. Please add it manually:"
                cat "$ssh_key_pub"
            fi
        else
            fancy_echo "GitHub CLI not installed. Please manually add the SSH key to your GitHub account:"
            cat "$ssh_key_pub"
        fi
    else
        fancy_echo "SSH key is already added to GitHub."
    fi

    gh extension install github/gh-copilot
}

# Function to clone and set up dotfiles
setup_dotfiles() {
    if [ "${SETUP_DOTFILES:-false}" != "true" ]; then
        fancy_echo "Skipping dotfiles setup."
        return
    fi

    if [ -z "${GITHUB_USERNAME:-}" ]; then
        fancy_echo "Error: GITHUB_USERNAME is required for dotfiles setup." >&2
        exit 1
    fi

    (cd "$HOME" && sh -c "$(curl -fsLS get.chezmoi.io)")

    local dotfiles_repo="${DOTFILES_REPO:-dotfiles}"

    if [ ! -d "$HOME/.dotfiles" ]; then
        fancy_echo "Cloning dotfiles repository..."
        git clone "git@github.com:${GITHUB_USERNAME}/${dotfiles_repo}.git" "$HOME/.dotfiles"
    else
        fancy_echo "Dotfiles already cloned."
    fi

    cd "$HOME/.dotfiles"
    git pull

    # chezmoi
    "$HOME"/bin/chezmoi --source ~/.dotfiles/chezmoi apply

    devbox global install
    eval "$(devbox global shellenv --recompute)"

    # dotbot
    ./install
}

install_homebrew_packages() {
    fancy_echo "Installing Homebrew packages ..."

    (cd "$HOME"/.dotfiles && brew bundle install)
}

setup_node() {
    if [ ! -d "$HOME/.nvm" ]; then
        fancy_echo "Installing NVM..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    else
        fancy_echo "NVM already installed."
    fi

    export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm

    nvm install --lts
    fancy_echo "Node $(node --version) and NPM $(npm --version) installed."
}

# Setup Python with pyenv
setup_python() {
    fancy_echo "Setting up Python..."

    brew install openssl readline sqlite3 xz zlib

    # PYTHON_CFLAGS="-march=native" \
    #     CONFIGURE_OPTS="--enable-optimizations --with-lto" \

    pyenv install --skip-existing 3.11
    pyenv global 3.11

    pip install --upgrade pip
    pip install pipx
    pipx ensurepath
    pipx install aider-chat
    pipx install pre-commit
    pipx install llm
}

# Function to configure Mac settings
configure_mac_settings() {
    if [ "${CONFIGURE_MAC:-false}" != "true" ]; then
        fancy_echo "Skipping Mac settings configuration."
        return
    fi

    fancy_echo "Configuring Mac settings..."

    # Dock
    defaults write com.apple.dock autohide -bool false
    defaults write com.apple.dock tilesize -int 64

    # Finder
    defaults write com.apple.finder ShowPathbar -bool true
    defaults write com.apple.finder ShowStatusBar -bool true

    # Keyboard
    defaults write NSGlobalDomain KeyRepeat -int 2
    defaults write NSGlobalDomain InitialKeyRepeat -int 15

    # Screenshots
    defaults write com.apple.screencapture location -string "${HOME}/Desktop"
    defaults write com.apple.screencapture type -string "png"

    # Set automatic timezone
    sudo systemsetup -setusingnetworktime on >/dev/null 2>&1

    fancy_echo "Restarting affected applications..."
    for app in "Dock" "Finder" "SystemUIServer"; do
        killall "${app}" &>/dev/null
    done

    fancy_echo "Mac settings configured. Some changes may require a logout/restart to take effect."
}

setup_fonts() {
    # Function to check if a font is already installed
    is_font_installed() {
        local font_name="$1"
        fc-list | grep -i "$font_name" >/dev/null
        return $?
    }

    if is_font_installed "Iosevka Custom"; then
        echo "Font 'Iosevka Custom' is already installed. Skipping."
        return
    fi

    (cd "$HOME"/.dotfiles/fonts/iosevka-custom && make build)
    (cd "$HOME"/.dotfiles/fonts/iosevka-custom && make install)
    fc-cache -f -v

    echo "Font installation process completed."
}

install_rosetta() {
    sudo softwareupdate --install-rosetta --agree-to-license
}

# Main function
main() {
    fancy_echo "Starting Mac setup..."

    install_rosetta
    install_xcode_clt
    install_homebrew
    install_nix_and_devbox
    setup_dotfiles
    setup_ssh_and_github
    setup_fonts
    setup_node
    setup_python
    install_homebrew_packages
    configure_mac_settings

    fancy_echo "Setup complete! Check the log file for details: $LOG_FILE"
}

main
