#!/usr/bin/env bash

# took https://gist.github.com/railwaycat/4043945, fixed lints

t=()

if [ ${#@} -ne 0 ]; then
  while IFS= read -r file; do
    [ ! -f "$file" ] && t+=("$file") && /usr/bin/touch "$file"
    file=$(cd "$(dirname "$file")" && pwd -P)/$(basename "$file")
    (/usr/bin/osascript <<-END
      if application "Emacs.app" is running then
        tell application id (id of application "Emacs.app") to open POSIX file "$file"
      else
        tell application ((path to applications folder as text) & "Emacs.app")
          activate
          open POSIX file "$file"
        end tell
      end if
END
    ) &  # Note: END on the previous line may be indented with tabs but not spaces
  done <<<"$(printf '%s\n' "$@")"
fi

if [ -n "${t[0]}" ]; then
  /bin/sleep 10; for file in "${t[@]}"; do
    [ ! -s "$file" ] && /bin/rm "$file";
  done &
fi
