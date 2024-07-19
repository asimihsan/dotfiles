# add devbox bits to zsh
fpath+=($DEVBOX_GLOBAL_PREFIX/share/zsh/site-functions $DEVBOX_GLOBAL_PREFIX/share/zsh/$ZSH_VERSION/functions $DEVBOX_GLOBAL_PREFIX/share/zsh/vendor-completions)
autoload -U compinit && compinit
eval "$(devbox global shellenv)"

export PATH="$HOME/.bin:$HOME/bin:$PATH"
export PATH="/usr/local/bin:$HOME/bin:$PATH"
eval "$(/opt/homebrew/bin/brew shellenv)"

export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm

export PATH="$PATH":$HOME/flutter/bin

source <(fzf --zsh)

export ANDROID_HOME=/$HOME/Library/Android/sdk
export ANDROID_NDK_HOME=$ANDROID_HOME/ndk/25.1.8937393
export ANDROID_NDK=$ANDROID_NDK_HOME
export NDK=$ANDROID_HOME/ndk/25.1.8937393

export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"

export GRAALVM_HOME="/Library/Java/JavaVirtualMachines/graalvm-ce-java17-22.3.0/Contents/Home"
export PATH="${PATH}":"${GRAALVM_HOME}"/bin
# export PATH=$HOME/.emacs.d/bin:"$PATH"

# brew install coreutils

# brew install vivid
export LS_COLORS="$(vivid generate molokai)"

# brew install exa

export PATH="$HOME"/go/bin:"$PATH"

autoload -U +X bashcompinit && bashcompinit

# Hishtory Config:
# export PATH="$PATH:/Users/asimi/.hishtory"
# source /Users/asimi/.hishtory/config.zsh

# Better history
# bindkey -s '^e' "hishtory export | tac | awk '!a[\$0]++' | tac | fzf --scheme=history --tac --no-sort --preview 'echo {}' --preview-window down:5:wrap --bind '?:toggle-preview'^M"

test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"

export DOTNET_CLI_TELEMETRY_OPTOUT=1

[[ -s "/Users/asimi/.gvm/scripts/gvm" ]] && source "/Users/asimi/.gvm/scripts/gvm"

export PATH="${PATH}":/Users/asimi/Library/Application\ Support/JetBrains/Toolbox/scripts/
export PATH=$PATH:$(go env GOPATH)/bin

export PATH="$PATH":"$HOME/.pub-cache/bin"
export NDK_HOME=$HOME/Library/Android/sdk/ndk/25.1.8937393
export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-17.jdk/Contents/Home
export PATH=$HOME/flutter/bin:$PATH
export PATH=$PATH:/Users/asimi/.local/bin:/Users/asimi/bin

# -----------------------------------------------------------------------------
#   Homebrew paths.
# -----------------------------------------------------------------------------
# Get the Homebrew base installation directory once
brew_prefix=$(brew --prefix)

# Update PATH for sqlite, tidy-html5, poetry, and protobuf
export PATH="${brew_prefix}/opt/sqlite/bin:$PATH"
export PATH="$PATH:${brew_prefix}/opt/tidy-html5/bin"
export PATH="${brew_prefix}/opt/protobuf/bin:$PATH"

# Set PLANTUML_JAR
export PLANTUML_JAR="${brew_prefix}/opt/plantuml/libexec/plantuml.jar"

# Initialize rbenv
eval "$(${brew_prefix}/opt/rbenv/bin/rbenv init - zsh)"

alias node=${brew_prefix}/opt/node@20/bin/node
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#  Secrets from 1Password.
# -----------------------------------------------------------------------------
# Define a function to load a secret from 1Password and export it as an environment variable
load_secret() {
    local secret_path=$1
    local var_name=$2
    export "$var_name"="$(op read --account my.1password.com "op://$secret_path")"
}

# Define a function to load all secrets
load_all_secrets() {
    load_secret "Private/SumoLogic Level/Access ID" "SUMOLOGIC_ACCESS_ID"
    load_secret "Private/SumoLogic Level/Access Key" "SUMOLOGIC_ACCESS_KEY"
    load_secret "pvsttlycpwhbo6vjsedtjbgyc4/mdu_pypi_readonly/username" "POETRY_HTTP_BASIC_DEFAULT_USERNAME"
    load_secret "pvsttlycpwhbo6vjsedtjbgyc4/mdu_pypi_readonly/password" "POETRY_HTTP_BASIC_DEFAULT_PASSWORD"
    load_secret "Private/Level Jira API token/password" "JIRA_API_TOKEN"
    load_secret "Private/Level Jira API token/server" "JIRA_API_SERVER"
    load_secret "Private/Level Jira API token/email" "JIRA_API_EMAIL"
    load_secret "Private/LocalStack Auth Token/password" "LOCALSTACK_AUTH_TOKEN"
    load_secret "Private/OpenAPI API key work/password" "OPENAI_API_KEY"
    load_secret "Private/Notion API key for Level workspace/credential" "NOTION_KEY"
    load_secret "Private/Anthropic API key/credential" "ANTHROPIC_API_KEY"
    load_secret "Private/Huggingface Token/credential" "HUGGINGFACE_TOKEN"
    load_secret "Private/hlru5i AppStore API key 2/private key" "APPLE_APP_STORE_CONNECT_PRIVATE_KEY"
    load_secret "Private/hlru5i AppStore API key 2/issuer id" "APPLE_APP_STORE_CONNECT_ISSUER_ID"
    load_secret "Private/hlru5i AppStore API key 2/key ID" "APPLE_APP_STORE_CONNECT_KEY_ID"
    echo "All secrets have been loaded."
}

# You can now call `load_all_secrets` manually whenever you need to populate the environment variables
# -----------------------------------------------------------------------------

export PATH="$HOME/flutter:$PATH"

alias ll='exa -lh --git'
alias ls="gls --color"
alias pmc='coyote test'
alias zstd=$(brew --prefix zstd)/bin/zstd
eval "$(gh copilot alias -- zsh)"
alias vim=nvim

export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

eval "$(starship init zsh)"

export _ZO_RESOLVE_SYMLINKS=1  # resolve symlinks
eval "$(zoxide init zsh)"
alias cd='z'

eval "$(direnv hook zsh)"

# -----------------------------------------------------------------------------
#  atuin configuration.
# -----------------------------------------------------------------------------
if [[ $options[zle] = on ]]; then
  eval "$(atuin init zsh)"
fi
# -----------------------------------------------------------------------------


[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
