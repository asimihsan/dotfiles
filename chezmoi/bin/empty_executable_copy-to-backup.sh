#!/usr/bin/env bash

set -euo pipefail

# chezmoi add --encrypt ~/.claude.json
chezmoi add --template ~/.zshrc

# chezmoi re-add ~/.claude.json
chezmoi re-add ~/.zprofile
chezmoi re-add ~/.zshenv
chezmoi re-add ~/.config/karabiner/karabiner.json
chezmoi re-add ~/.config/kitty/kitty.conf
chezmoi re-add ~/.config/mise/config.toml
chezmoi re-add ~/.config/zed/settings.json
chezmoi re-add ~/.config/zed/settings.json
chezmoi re-add ~/.config/zed/tasks.json
chezmoi re-add ~/bin/idea
chezmoi re-add ~/Library/Preferences/com.googlecode.iterm2.plist
chezmoi re-add ~/Library/Preferences/com.googlecode.iterm2.private.plist
