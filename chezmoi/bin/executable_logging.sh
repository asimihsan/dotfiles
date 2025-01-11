LOGDIR="$HOME/logs"
LOGGER_SCRIPT="$HOME/bin/clean_logger.sh"
mkdir -p "$LOGDIR"

# Function to start recording session
function record_session() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    mkdir -p "$LOGDIR"

    TTY_FILE="$LOGDIR/terminal_${TIMESTAMP}.tty"
    TXT_FILE="$LOGDIR/terminal_${TIMESTAMP}.txt"
    CLEAN_FILE="$LOGDIR/terminal_${TIMESTAMP}_clean.txt"

    echo "Starting recording session..."
    echo "TTY file: $TTY_FILE"
    echo "Text file: $TXT_FILE"
    echo "Clean file: $CLEAN_FILE"

    # Create empty file first
    touch "$TXT_FILE"

    # Start the background cleaner process with nohup
    nohup bash -c "stdbuf -oL tail -f -n +1 \"$TXT_FILE\" | \"$LOGGER_SCRIPT\" > \"$CLEAN_FILE\"" >/dev/null 2>&1 &
    CLEANER_PID=$!

    # Set up cleanup trap for just the cleaner
    trap 'kill $CLEANER_PID 2>/dev/null' EXIT

    # Run script with shell command to execute ttyrec
    script -q "$TXT_FILE" /bin/sh -c "exec ttyrec \"$TTY_FILE\""
}

# Function to view last recording (cleaned)
function lastlog() {
    local LATEST=""

    echo "Searching for log files in $LOGDIR..."

    # List all matching files first
    echo "Found files:"
    cd "$LOGDIR" && fd "terminal.*\.txt$" --type f

    # Try clean file first
    LATEST=$(cd "$LOGDIR" && fd "terminal.*clean\.txt$" --type f --exec-batch ls -t | head -n 1)

    if [[ -z "$LATEST" ]]; then
        echo "No clean files found, trying raw text files..."
        # Try raw text file, excluding clean files
        LATEST=$(cd "$LOGDIR" && fd "terminal.*\.txt$" --type f --exclude "*clean.txt*" --exec-batch ls -t | head -n 1)
    fi

    if [[ -n "$LATEST" && -f "$LOGDIR/$LATEST" && -s "$LOGDIR/$LATEST" ]]; then
        echo "Opening log file: $LATEST"
        less -R "$LOGDIR/$LATEST"
    else
        echo "No valid log files found in $LOGDIR"
        echo "All terminal-related files:"
        cd "$LOGDIR" && fd "terminal" --type f
    fi
}

# Function to open terminal on macOS
function open_new_terminal() {
    local cmd="$1"
    osascript -e "tell application \"Terminal\" to do script \"$cmd\""
}

# Function to play TTY recording
function playtty() {
    local FILE="$1"
    if [[ -z "$FILE" ]]; then
        # Find most recent tty file
        FILE=$(cd "$LOGDIR" && fd "terminal.*\.tty$" --type f --exec-batch ls -t | head -n 1)
        if [[ -n "$FILE" ]]; then
            FILE="$LOGDIR/$FILE"
        fi
    fi

    if [[ -n "$FILE" && -f "$FILE" && -s "$FILE" ]]; then
        echo "Playing TTY file: $FILE"

        if [[ "$TERM" == "xterm-kitty" ]]; then
            # Try kitty first
            if kitty @ ls-windows > /dev/null 2>&1; then
                kitty @ new-window --new-tab ttyplay -n "$FILE"
            else
                echo "Kitty remote control disabled, falling back to new Terminal window..."
                open_new_terminal "ttyplay -n '$FILE'"
            fi
        else
            # For non-Kitty terminals, open in new Terminal window
            open_new_terminal "ttyplay -n '$FILE'"
        fi
    else
        echo "Error: Cannot find valid TTY file"
        echo "Specified file: $FILE"
        echo "Available TTY files:"
        cd "$LOGDIR" && fd "terminal.*\.tty$" --type f
    fi
}

# Function to rotate logs
rotate_logs() {
    fd . "$LOGDIR" --changed-before 7d --type f --threads 1 --exclude "*.zst" --exec zstd -7 --rm {}
}
