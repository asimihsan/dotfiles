#!/usr/bin/env bash

set -euo pipefail

cp $(devbox global path)/devbox.{lock,json} ~/.dotfiles/chezmoi/dot_local/share/devbox/global/default/
cp ~/.config/zed/settings.json ~/.dotfiles/chezmoi/dot_config/zed/private_settings.json
cp ~/.config/zed/tasks.json ~/.dotfiles/chezmoi/dot_config/zed/private_tasks.json
