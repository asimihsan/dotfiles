export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git)
source $ZSH/oh-my-zsh.sh

export PATH="$HOME/.bin:$PATH"
export PATH="/usr/local/bin:$HOME/bin:$PATH"
eval "$(/opt/homebrew/bin/brew shellenv)"

. "$HOME/.cargo/env"

export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"                   # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion" # This loads nvm bash_completion

. "$HOME/.nvm/nvm.sh"

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

brew_path() {
    brew list $1 | sponge | head -1 | xargs dirname | sed 's/\(^.*\/hbase\/[^\/]*\).*/\1/'
}

export PATH=$HOME/.emacs.d/bin:"$PATH"

export PATH=$(brew_path sqlite)/bin:"$PATH"
export PATH="$PATH":$(brew_path tidy-html5)/bin
export PATH=$(brew_path poetry)/bin:"$PATH"

export PLANTUML_JAR=$(brew_path plantuml)/libexec/plantuml.jar

# brew install coreutils

# brew install vivid
export LS_COLORS="$(vivid generate molokai)"

# brew install exa

export PATH="$HOME"/go/bin:"$PATH"

eval "$($(brew_path rbenv)/bin/rbenv init - zsh)"

autoload -U +X bashcompinit && bashcompinit
complete -o nospace -C /opt/homebrew/bin/terraform terraform

# Hishtory Config:
export PATH="$PATH:/Users/asimi/.hishtory"
source /Users/asimi/.hishtory/config.zsh

# Better history
# bindkey -s '^e' "hishtory export | tac | awk '!a[\$0]++' | tac | fzf --scheme=history --tac --no-sort --preview 'echo {}' --preview-window down:5:wrap --bind '?:toggle-preview'^M"

#THIS MUST BE AT THE END OF THE FILE FOR SDKMAN TO WORK!!!
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"

test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"

source /Users/asimi/.docker/init-zsh.sh || true # Added by Docker Desktop

if which pyenv-virtualenv-init >/dev/null; then eval "$(pyenv virtualenv-init -)"; fi

export DOTNET_CLI_TELEMETRY_OPTOUT=1

export POETRY_HTTP_BASIC_DEFAULT_USERNAME=$(op read "op://pvsttlycpwhbo6vjsedtjbgyc4/mdu_pypi_readonly/username")
export POETRY_HTTP_BASIC_DEFAULT_PASSWORD=$(op read "op://pvsttlycpwhbo6vjsedtjbgyc4/mdu_pypi_readonly/password")
export JIRA_API_TOKEN=$(op read "op://Private/Level Jira API token/password")
export LOCALSTACK_AUTH_TOKEN=$(op read "op://Private/LocalStack Auth Token/password")
export OPENAI_API_KEY=$(op read "op://Private/OpenAPI API key work/password")

#export OTEL_EXPORTER_OTLP_ENDPOINT="https://api.honeycomb.io/"
#export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=gqCJm5CcK4koptUfObqTQH"
#export OTEL_SERVICE_NAME="mdu-cloud-integration-gateway"

export PATH=$(brew_path protobuf)/bin:"$PATH"

[[ -s "/Users/asimi/.gvm/scripts/gvm" ]] && source "/Users/asimi/.gvm/scripts/gvm"

GO_VERSION=1.21
export PATH="/opt/homebrew/opt/go@$GO_VERSION/bin:$PATH"
export GOROOT=$(brew_path go@$GO_VERSION)/libexec

export SUMOLOGIC_ACCESS_ID=$(op read "op://Private/SumoLogic Level/Access ID")
export SUMOLOGIC_ACCESS_KEY=$(op read "op://Private/SumoLogic Level/Access Key")

export PATH=$PATH:$(go env GOPATH)/bin

alias ll='exa -lh --git'
alias ls="gls --color"
alias make=$(brew_path make)/bin/gmake
alias pmc='coyote test'
alias poetry=$(brew_path poetry)/bin/poetry
alias rsync=$(brew_path rsync)/bin/rsync
alias wget=$(brew_path wget)/bin/wget
alias zstd=$(brew --prefix zstd)/bin/zstd
