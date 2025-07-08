#!/usr/bin/env bash

set -euo pipefail

# shellcheck disable=SC2059
fancy_echo() {
  local fmt="$1"; shift
  printf "\n$fmt\n" "$@"
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

install_homebrew() {
  if ! command_exists brew; then
    fancy_echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ -x /opt/homebrew/bin/brew ]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
  else
    fancy_echo "Homebrew already installed."
  fi
}

install_mise() {
  if ! command_exists mise; then
    fancy_echo "Installing mise via Homebrew..."
    brew install mise
  else
    fancy_echo "mise already installed."
  fi
  eval "$(mise activate bash)" || true
}

install_chezmoi() {
  if ! command_exists chezmoi; then
    fancy_echo "Installing chezmoi via mise..."
    mise use -g chezmoi
  else
    fancy_echo "chezmoi already installed."
  fi
  eval "$(mise activate bash)" || true
}

ensure_restic_sudoers() {
  local file=/etc/sudoers.d/restic-snapshot
  local tmp
  tmp=$(mktemp)
  cat >"$tmp" <<EOF_SUDO
# restic snapshot privileges for $USER
$USER ALL=(root) NOPASSWD: \
    /usr/bin/tmutil *, \
    /sbin/mount_apfs *, \
    /sbin/umount *, \
    /usr/sbin/diskutil unmount *
EOF_SUDO
  if ! sudo test -f "$file" || ! sudo cmp -s "$tmp" "$file"; then
    sudo install -m 0440 -o root -g wheel "$tmp" "$file"
    sudo visudo -cf "$file" || { echo "sudoers syntax error"; exit 1; }
    fancy_echo "Updated $file"
  fi
  rm -f "$tmp"
}

update_homebrew() {
  brew update --auto-update
  brew upgrade
  brew bundle install --no-lock || true
  brew cleanup --prune=all
}

update_mise() {
  mise cache clear
  mise install
  mise upgrade --yes
  mise prune --yes
}

update_rust() {
  if command_exists rustup; then
    rustup update stable
  fi
  if command_exists cargo; then
    cargo binstall --no-confirm lazyjj monolith || true
    cargo install taplo-cli --locked --features lsp || true
  fi
}

update_system() {
  sudo softwareupdate --download --all --agree-to-license || true
}

init_chezmoi() {
  install_chezmoi
  local repo="${DOTFILES_REPO:-git@github.com:${GITHUB_USERNAME:-${USER}}/dotfiles.git}"
  if [ ! -d "$HOME/.local/share/chezmoi" ]; then
    fancy_echo "Initializing dotfiles from $repo"
    chezmoi init --apply --source=chezmoi "$repo"
  else
    fancy_echo "Applying dotfiles"
    chezmoi apply
  fi
}

main() {
  install_homebrew
  install_mise
  init_chezmoi
  ensure_restic_sudoers
  update_homebrew
  update_mise
  update_rust
  update_system
  fancy_echo "Mac setup/update complete."
}

main "$@"

