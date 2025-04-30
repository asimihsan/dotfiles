#!/usr/bin/env bash

set -uo pipefail

function cache_sudo_credentials() {
    sudo -v
}

ensure_restic_sudoers() {
  local file=/etc/sudoers.d/restic-snapshot
  local tmp
  tmp=$(mktemp)

  cat >"$tmp" <<EOF
# restic snapshot privileges for $USER
$USER ALL=(root) NOPASSWD: \
    /usr/bin/tmutil *, \
    /sbin/mount_apfs *, \
    /sbin/umount *, \
    /usr/sbin/diskutil unmount *
EOF

  # Install only if different or missing
  if ! sudo test -f "$file" || ! sudo cmp -s "$tmp" "$file"; then
    sudo install -m 0440 -o root -g wheel "$tmp" "$file"
    sudo visudo -cf "$file" || { echo "sudoers syntax error"; exit 1; }
    echo "Updated $file"
  fi
  rm -f "$tmp"
}

cache_sudo_credentials
echo starting...

ensure_restic_sudoers

# TODO REMOVEME
for tap in aws smithy-lang; do
  file="/opt/homebrew/Library/Taps/${tap}/homebrew-tap/ConfigProvider/config_provider.rb"
  sudo perl -0777 -pi -e 's/^(\s*)CONFIG_DIR\s*=/\1CONFIG_DIR ||=/' "$file"
done

# TODO REMOVEME
for f in $(brew uses --installed icu4c@76); do
  brew reinstall $f
done
brew uninstall icu4c@76

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
}

update_dotfiles

"$HOME"/.dotfiles/install

chezmoi update
chezmoi upgrade
chezmoi apply

devbox global update
eval "$(devbox global shellenv --recompute)"

sudo softwareupdate --download --all --agree-to-license
brew update --auto-update
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
brew cleanup --prune=all

~/bin/copy-to-backup.sh

xattr -cr /Applications/Chromium.app
