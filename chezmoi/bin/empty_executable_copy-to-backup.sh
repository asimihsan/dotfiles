#!/usr/bin/env bash

set -euo pipefail

chezmoi add "$(devbox global path)"/devbox.json
chezmoi add "$(devbox global path)"/devbox.lock
chezmoi add ~/.config/zed/settings.json
chezmoi add ~/.config/zed/tasks.json
chezmoi add ~/.config/karabiner/karabiner.json
chezmoi add ~/.config/kitty/kitty.conf
chezmoi add --template ~/.zshrc
chezmoi add ~/Library/Preferences/com.googlecode.iterm2.plist
chezmoi add ~/Library/Preferences/com.googlecode.iterm2.private.plist
chezmoi add --encrypt ~/.claude.json
