#!/usr/bin/env bash

# mac_setup.sh — Idempotent macOS bootstrap / update script
#
# Usage:
#   ./mac_setup.sh [-p profile] [-n new_hostname] [-h]
#
# Options:
#   -p profile        Override auto-detected profile (personal, work, default)
#   -n new_hostname   Set macOS ComputerName/HostName/LocalHostName first
#   -h                Show this help and exit
#
# Examples:
#   sudo ./mac_setup.sh -n hlru5i        # First-time on new personal laptop
#   ./mac_setup.sh                       # Regular update (auto profile)
#   ./mac_setup.sh -p work               # Force work profile
#
# The script is safe to run multiple times; each step is idempotent.

# Special mode:
#   --hostname-only NEWNAME   Only set hostnames and exit. Must be run with sudo.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
pushd "$SCRIPT_DIR" >/dev/null
trap 'popd >/dev/null' EXIT

# shellcheck disable=SC2059
fancy_echo() {
  local fmt="$1"; shift
  printf "$fmt\n" "$@"
}

keep_sudo_alive() {
  # Ask once up-front
  sudo -v

  # Refresh every minute until the script ends
  while true; do
    sudo -n true 2>/dev/null
    sleep 60
  done &
  SUDO_REFRESH_PID=$!

  # Clean-up on exit or interruption
  trap 'kill $SUDO_REFRESH_PID || true' EXIT
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

usage() {
  cat <<USAGE >&2
Usage: $0 [-p profile] [-n new_hostname] [--hostname-only NEWNAME]
  -p profile        Override auto-detected profile (e.g. personal, work)
  -n new_hostname   Set macOS ComputerName/HostName/LocalHostName first
  --hostname-only NEWNAME   Only set the hostnames and exit
USAGE
}

set_hostnames() {
  local newname="$1"
  # Validate hostname characters (Bonjour rules)
  if [[ ! "$newname" =~ ^[A-Za-z0-9-]+$ ]]; then
    echo "Error: hostname must contain only letters, numbers, and hyphens." >&2
    exit 2
  fi

  fancy_echo "Setting hostnames to '$newname'…"
  sudo scutil --set ComputerName "$newname"
  sudo scutil --set HostName "$newname"
  sudo scutil --set LocalHostName "$newname"
  sudo dscacheutil -flushcache
}

run_profile_tasks() {
  local profile="$1"
  case "$profile" in
    work)
      fancy_echo "Running work profile tasks…"
      # Placeholder for work-specific setup steps
      ;;
    personal)
      fancy_echo "Running personal profile tasks…"
      # Placeholder for personal-specific setup steps
      ;;
    *)
      # default / no-op
      ;;
  esac
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

  # ruby dependencies
  brew install openssl@3 readline libyaml gmp autoconf

  brew upgrade
  brew bundle install
  brew cleanup --prune=all
}

update_mise() {
  mise cache clear
  mise install
  mise upgrade --yes
  mise prune --yes
}

install_awscli() {
  mise install awscli ref:$(mise latest awscli 2)
  mise use -g awscli@$(mise latest awscli 2)
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

install_pragmasevka_font() {
  local font_dir="$HOME/Library/Fonts"

  # If the regular style is already present, assume the font is installed.
  if find "$font_dir" -maxdepth 1 -iname "pragmasevka-nf-regular.ttf" | grep -q .; then
    fancy_echo "Pragmasevka font already installed – skipping download."
    return
  fi

  local url="https://github.com/shytikov/pragmasevka/releases/download/v1.7.0/Pragmasevka_NF.zip"
  local expected_sha="eeab758eff562d1caed761244488e56545be25e81a6b40cd84b31b032a37615c"
  local tmp_dir
  tmp_dir=$(mktemp -d)
  local zip_file="$tmp_dir/Pragmasevka_NF.zip"

  fancy_echo "Downloading Pragmasevka font..."
  curl -LfsS -o "$zip_file" "$url"

  fancy_echo "Verifying SHA256 checksum..."
  local actual_sha
  actual_sha=$(shasum -a 256 "$zip_file" | awk '{print $1}')
  if [ "$actual_sha" != "$expected_sha" ]; then
    echo "SHA256 checksum mismatch for Pragmasevka font" >&2
    echo "Expected: $expected_sha" >&2
    echo "Actual:   $actual_sha" >&2
    exit 1
  fi

  fancy_echo "Checksum verified. Installing font..."

  unzip -q "$zip_file" -d "$tmp_dir"

  mkdir -p "$font_dir"
  find "$tmp_dir" -type f \( -name "*.ttf" -o -name "*.otf" \) -exec cp -f {} "$font_dir/" \;

  fancy_echo "Pragmasevka font installed."
}

update_system() {
  sudo softwareupdate --download --all --agree-to-license || true
}

init_chezmoi() {
  install_chezmoi
  fancy_echo "Initializing chezmoi from $SCRIPT_DIR"
  chezmoi init --source "$SCRIPT_DIR" --apply
}

install_gh_copilot() {
  gh extension install github/gh-copilot --force
  if ! gh auth status >/dev/null 2>&1; then
    gh auth login --git-protocol=https
  fi
}

mac_system_setup() {
  fancy_echo "Setting up macOS system..."

  # 3 is default hibernate mode; copy RAM to hibernation file but keeps RAM powered on.
  # 25 is the most aggressive mode; copy RAM to hibernation file and power off RAM.
  sudo pmset -a hibernatemode 25

  # After 1800 seconds (30 minutes), the system will go into standby mode, which is
  # actually hibernation! (This does not work at least on Mac M1)
  # sudo pmset -a standbydelay 1800

  # Disable Power Nap, which keeps networking alive.
  sudo pmset -a powernap 0

  # Show hidden files in Finder
  defaults write com.apple.Finder AppleShowAllFiles -bool true

  # Show all file extensions in Finder
  defaults write NSGlobalDomain AppleShowAllExtensions -bool true

  # Show the path bath and status bar in Finder
  defaults write com.apple.finder ShowPathbar -bool true
  defaults write com.apple.finder ShowStatusBar -bool true

  # Use list view and search the current folder by default
  defaults write com.apple.Finder FXPreferredViewStyle -string "Nlsv"
  defaults write com.apple.Finder FXDefaultSearchScope -string "SCcf"

  # Unhide the Library folder
  chflags nohidden ~/Library

  # Show the full POSIX path in Finder window titles
  defaults write com.apple.finder _FXShowPosixPathInTitle -bool true

  # Show the ~/Downloads folder in the sidebar
  defaults write com.apple.finder ShowRecentTags -bool false
  defaults write com.apple.finder ShowSidebar -bool true

  # Change screenshot save location
  mkdir -p ~/Pictures/Screenshots
  defaults write com.apple.screencapture location ~/Pictures/Screenshots
  killall SystemUIServer || true

  # Always show scroll bars
  defaults write NSGlobalDomain AppleShowScrollBars -string "Always"

  # Enable tap‑to‑click and two‑finger right‑click
  defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
  defaults write com.apple.AppleMultitouchTrackpad TrackpadRightClick -bool true

  # Increase keyboard repeat speed
  defaults write -g InitialKeyRepeat -int 10
  defaults write -g KeyRepeat -int 1

  # Turn off automatic spelling correction and capitalisation
  defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
  defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false

  # Restart Finder
  killall Finder || true
}

main() {
  # Parse CLI flags early
  local PROFILE=""
  local NEW_HOSTNAME=""
  local HOSTNAME_ONLY="0"
  while getopts "p:n:h" opt; do
    case $opt in
      p) PROFILE=$OPTARG ;;
      n) NEW_HOSTNAME=$OPTARG ;;
      h)
        usage
        return 0
        ;;
      *)
        usage
        return 1
        ;;
    esac
  done
  shift $((OPTIND - 1))

  # Optionally set a new hostname
  if [[ -n "$NEW_HOSTNAME" ]]; then
    set_hostnames "$NEW_HOSTNAME"
  fi

  keep_sudo_alive

  # Auto-detect profile from current hostname if not provided
  if [[ -z "$PROFILE" ]]; then
    local CURRENT_HOST
    CURRENT_HOST=$(scutil --get ComputerName 2>/dev/null || hostname)
    case "$CURRENT_HOST" in
      hlru5i|im9ibk) PROFILE="personal" ;;
      yov3bc|okzf68) PROFILE="work"     ;;
      *)             PROFILE="default"  ;;
    esac
  fi

  run_profile_tasks "$PROFILE"

  mac_system_setup
  install_pragmasevka_font
  install_mise
  install_gh_copilot
  install_homebrew
  init_chezmoi
  ensure_restic_sudoers
  update_homebrew
  install_awscli
  update_mise
  update_rust
  update_system
  fancy_echo "Mac setup/update complete for profile '$PROFILE'."
}

# If invoked directly with --hostname-only NEWNAME, handle it before main()
if [[ ${1:-} == "--hostname-only" ]]; then
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 --hostname-only NEWNAME" >&2
    exit 1
  fi
  keep_sudo_alive
  set_hostnames "$2"
  exit 0
fi

main "$@"

