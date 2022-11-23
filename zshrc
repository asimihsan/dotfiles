export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git)
source $ZSH/oh-my-zsh.sh

export PATH="$HOME/.bin:$PATH"
export PATH="/usr/local/bin:$HOME/bin:$PATH"
eval "$(/opt/homebrew/bin/brew shellenv)"

alias zstd=$(brew --prefix zstd)/bin/zstd

. "$HOME/.cargo/env"

export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

. "$HOME/.nvm/nvm.sh"

export PATH="$PATH":$HOME/flutter/bin

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Add .NET Core SDK tools
export PATH="$PATH:/Users/asimi/.dotnet/tools"
alias pmc='coyote test'

export ANDROID_NDK_HOME=$HOME/Library/Android/sdk/ndk/25.1.8937393

export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"

brew_path() {
    brew list $1 | sponge | head -1 | xargs dirname | sed 's/\(^.*\/hbase\/[^\/]*\).*/\1/'
}

export GOROOT=$(brew_path go)/libexec

export JAVA_HOME="/Library/Java/JavaVirtualMachines/amazon-corretto-11.jdk/Contents/Home"
export GRAALVM_HOME="/Library/Java/JavaVirtualMachines/graalvm-ce-java17-22.3.0/Contents/Home"
export PATH="${PATH}":"${GRAALVM_HOME}"/bin

alias make=$(brew_path make)/bin/gmake

export PATH=$HOME/.emacs.d/bin:"$PATH"

alias rsync=$(brew_path rsync)/bin/rsync

export PATH=$(brew_path sqlite)/bin:"$PATH"
export PATH="$PATH":$(brew_path tidy-html5)/bin

export PLANTUML_JAR=$(brew_path plantuml)/libexec/plantuml.jar

# brew install coreutils
alias ls="gls --color"

# brew install vivid
export LS_COLORS="$(vivid generate molokai)"

# brew install exa
alias ll='exa -lh --git'

export PATH="$HOME"/go/bin:"$PATH"

eval "$($(brew_path rbenv)/bin/rbenv init - zsh)"

autoload -U +X bashcompinit && bashcompinit
complete -o nospace -C /opt/homebrew/bin/terraform terraform

# Hishtory Config:
export PATH="$PATH:/Users/asimi/.hishtory"
source /Users/asimi/.hishtory/config.zsh
