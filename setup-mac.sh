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

# Function to set up Devbox global
setup_devbox_global() {
    fancy_echo "Setting up Devbox global..."
    devbox global add gh
    eval "$(devbox global shellenv --recompute)"
}

# Function to install Python and pipx
install_python_and_pipx() {
    devbox global add python311Full python311Packages.pip gh
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

    local dotfiles_repo="${DOTFILES_REPO:-dotfiles}"

    if [ ! -d "$HOME/.dotfiles" ]; then
        fancy_echo "Cloning dotfiles repository..."
        git clone "git@github.com:${GITHUB_USERNAME}/${dotfiles_repo}.git" "$HOME/.dotfiles"
    else
        fancy_echo "Dotfiles already cloned."
    fi

    rm -f "$(devbox global path)"/devbox.json

    cd "$HOME/.dotfiles"
    git pull
    ./install
}

install_homebrew_packages() {
    fancy_echo "Installing Homebrew packages ..."

    brew tap borgbackup/tap
    brew update
    brew install --cask macfuse

    packages=(
        borgbackup/tap/borgbackup-fuse
        fontconfig
        libyaml
        pyenv
        pyenv-virtualenv
        rbenv
    )

    casks=(
        1password
        docker
        firefox
        google-chrome
        gpg-suite
        hammerspoon
        iterm2
        jetbrains-toolbox
        karabiner-elements
        loopback
        menumeters
        moom
        obsidian
        omnigraffle
        raycast
        slack
        spotify
        tor-browser
        vorta
        zoom
    )

    for package in "${packages[@]}"; do
        if ! brew list "$package" &>/dev/null; then
            brew install "$package"
        else
            echo "$package is already installed."
        fi
    done

    for cask in "${casks[@]}"; do
        if ! brew list --cask "$cask" &>/dev/null; then
            brew install --cask "$cask"
        else
            echo "$cask is already installed."
        fi
    done
}

setup_node() {
    if [ ! -d "$HOME/.nvm" ]; then
        fancy_echo "Installing NVM..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    else
        fancy_echo "NVM already installed."
    fi
    source "$HOME/.nvm/nvm.sh"
    nvm install --lts
    nvm use --lts
}

# Setup Python with pyenv
setup_python() {
    # PYTHON_CFLAGS="-march=native" \
    #     CONFIGURE_OPTS="--enable-optimizations --with-lto" \

    # use pyenv to check if 3.11 is installed, if not install and global it
    if ! pyenv versions | grep -q 3.11; then
        fancy_echo "Installing Python 3.11..."
        pyenv install 3.11
        pyenv global 3.11
    else
        fancy_echo "Python 3.11 already installed."
    fi

    pip install --upgrade pip
    pip install pipx
    pipx ensurepath
    pipx install aider-chat
    pipx install poetry
    pipx install pre-commit
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

    (cd "$HOME"/.dotfiles/config && make iosevka-docker-build)
    (cd "$HOME"/.dotfiles/config && make iosevka-font-build)

    rsync -av "$HOME/Fonts" "$HOME/Library/Fonts"
    fc-cache -f -v

    echo "Font installation process completed."
}

# Main function
main() {
    fancy_echo "Starting Mac setup..."

    install_xcode_clt
    install_homebrew
    install_nix_and_devbox
    setup_devbox_global
    setup_ssh_and_github
    install_homebrew_packages
    setup_fonts
    setup_node
    setup_python
    setup_dotfiles
    configure_mac_settings

    fancy_echo "Setup complete! Check the log file for details: $LOG_FILE"
}

main
