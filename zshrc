export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git)
source $ZSH/oh-my-zsh.sh

export PATH="$HOME/.bin:$HOME/bin:$PATH"
export PATH="/usr/local/bin:$HOME/bin:$PATH"
eval "$(/opt/homebrew/bin/brew shellenv)"

. "$HOME/.cargo/env"

export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

export NVM_DIR="$HOME/.nvm"
[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion

export PATH="$PATH":$HOME/flutter/bin

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Add .NET Core SDK tools
export PATH="$PATH:/Users/asimi/.dotnet/tools"

export ANDROID_HOME=/$HOME/Library/Android/sdk
export ANDROID_NDK_HOME=$ANDROID_HOME/ndk/25.1.8937393
export ANDROID_NDK=$ANDROID_NDK_HOME
export NDK=$ANDROID_HOME/ndk/25.1.8937393

export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"

export GRAALVM_HOME="/Library/Java/JavaVirtualMachines/graalvm-ce-java17-22.3.0/Contents/Home"
export PATH="${PATH}":"${GRAALVM_HOME}"/bin
export PATH=$HOME/.emacs.d/bin:"$PATH"

# brew install coreutils

# brew install vivid
export LS_COLORS="$(vivid generate molokai)"

# brew install exa

export PATH="$HOME"/go/bin:"$PATH"

autoload -U +X bashcompinit && bashcompinit
complete -o nospace -C /opt/homebrew/bin/terraform terraform

# Hishtory Config:
export PATH="$PATH:/Users/asimi/.hishtory"
source /Users/asimi/.hishtory/config.zsh

# Better history
# bindkey -s '^e' "hishtory export | tac | awk '!a[\$0]++' | tac | fzf --scheme=history --tac --no-sort --preview 'echo {}' --preview-window down:5:wrap --bind '?:toggle-preview'^M"

test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"

if which pyenv-virtualenv-init >/dev/null; then eval "$(pyenv virtualenv-init -)"; fi

export DOTNET_CLI_TELEMETRY_OPTOUT=1

[[ -s "/Users/asimi/.gvm/scripts/gvm" ]] && source "/Users/asimi/.gvm/scripts/gvm"

GO_VERSION=1.21
export PATH="/opt/homebrew/opt/go@$GO_VERSION/bin:$PATH"


export PATH="${PATH}":/Users/asimi/Library/Application\ Support/JetBrains/Toolbox/scripts/
export PATH=$PATH:$(go env GOPATH)/bin

export PATH="$PATH":"$HOME/.pub-cache/bin"
export LOCALSTACK_API_KEY=6xxZjUgHLg
export NDK_HOME=$HOME/Library/Android/sdk/ndk/25.1.8937393
export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home

# -----------------------------------------------------------------------------
#   Homebrew paths.
# -----------------------------------------------------------------------------
# Get the Homebrew base installation directory once
brew_prefix=$(brew --prefix)

# If you have a specific version of Go set in GO_VERSION, use that
# Otherwise, it will default to the latest version installed by Homebrew
if [[ -n "$GO_VERSION" ]]; then
    export GOROOT="${brew_prefix}/opt/go@$GO_VERSION/libexec"
else
    export GOROOT="${brew_prefix}/opt/go/libexec"
fi

# Set alias for make to use gmake
alias make="${brew_prefix}/opt/make/bin/gmake"

# Update PATH for sqlite, tidy-html5, poetry, and protobuf
export PATH="${brew_prefix}/opt/sqlite/bin:$PATH"
export PATH="$PATH:${brew_prefix}/opt/tidy-html5/bin"
export PATH="${brew_prefix}/opt/poetry/bin:$PATH"
export PATH="${brew_prefix}/opt/protobuf/bin:$PATH"

# Set PLANTUML_JAR
export PLANTUML_JAR="${brew_prefix}/opt/plantuml/libexec/plantuml.jar"

# Initialize rbenv
eval "$(${brew_prefix}/opt/rbenv/bin/rbenv init - zsh)"

alias make=${brew_prefix}/opt/make/bin/gmake
alias poetry=${brew_prefix}/opt/poetry/bin/poetry
alias rsync=${brew_prefix}/opt/rsync/bin/rsync
alias wget=${brew_prefix}/opt/wget/bin/wget
alias ctags=${brew_prefix}/opt/universal-ctags/bin/ctags
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#  Secrets from 1Password.
# -----------------------------------------------------------------------------
# Define a function to load a secret from 1Password and export it as an environment variable
load_secret() {
    local secret_path=$1
    local var_name=$2
    export "$var_name"="$(op read "op://$secret_path")"
}

# Define a function to load all secrets
load_all_secrets() {
    load_secret "Private/SumoLogic Level/Access ID" "SUMOLOGIC_ACCESS_ID"
    load_secret "Private/SumoLogic Level/Access Key" "SUMOLOGIC_ACCESS_KEY"
    load_secret "pvsttlycpwhbo6vjsedtjbgyc4/mdu_pypi_readonly/username" "POETRY_HTTP_BASIC_DEFAULT_USERNAME"
    load_secret "pvsttlycpwhbo6vjsedtjbgyc4/mdu_pypi_readonly/password" "POETRY_HTTP_BASIC_DEFAULT_PASSWORD"
    load_secret "Private/Level Jira API token/password" "JIRA_API_TOKEN"
    load_secret "Private/LocalStack Auth Token/password" "LOCALSTACK_AUTH_TOKEN"
    load_secret "Private/OpenAPI API key work/password" "OPENAI_API_KEY"
    echo "All secrets have been loaded."
}

# You can now call `load_all_secrets` manually whenever you need to populate the environment variables
# -----------------------------------------------------------------------------

alias ll='exa -lh --git'
alias ls="gls --color"
alias pmc='coyote test'
alias zstd=$(brew --prefix zstd)/bin/zstd

eval "$(github-copilot-cli alias -- "$0")"
