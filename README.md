# dotfiles

This repo contains dotfiles (configuration files and directories) used for personal and work machines.

## How to use

### Prerequisites

If on Mac:

-   Clone this repo:

```
git clone git@github.com:asimihsan/dotfiles.git ~/.dotfiles
```

-   Run the setup script

```
cd ~/.dotfiles
./mac_setup.sh
```

Running `mac_setup.sh` installs Homebrew, mise, and chezmoi if needed and then
initializes the dotfiles from this repository.

## Watchman Project Config

Global Watchman settings are synced to `/etc/watchman.json`, but `ignore_dirs`
must live in each repo's `.watchmanconfig`.

This repo ships a reusable template at:

- `~/.config/watchman/watchmanconfig-universal.json`

and a helper script at:

- `~/bin/watchman-apply-config.sh`

Example usage:

```bash
watchman-apply-config.sh --reload ~/workplace/bixby-rs
```

Use `--force` to replace an existing `.watchmanconfig`.

## License

`dotfiles` is distributed under the terms of the Apache License (Version 2.0).
See [LICENSE](LICENSE) for details.
