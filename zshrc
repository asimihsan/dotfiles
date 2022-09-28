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
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

. "$HOME/.nvm/nvm.sh"

export PATH="$PATH":$HOME/flutter/bin

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# For P
alias dotnet=/usr/local/share/dotnet/x64/dotnet
# Add .NET Core SDK tools
export PATH="$PATH:/Users/asimi/.dotnet/tools"
alias pmc='coyote test'

eval "$(rbenv init - zsh)"

export ANDROID_NDK_HOME=$HOME/Library/Android/sdk/ndk/25.1.8937393

export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/llvm/lib"
export CPPFLAGS="-I/opt/homebrew/opt/llvm/include"

brew_path() {
    brew list $1 | sponge | head -1 | xargs dirname | sed 's/\(^.*\/hbase\/[^\/]*\).*/\1/'
}

export GOROOT=$(brew_path go)/libexec
