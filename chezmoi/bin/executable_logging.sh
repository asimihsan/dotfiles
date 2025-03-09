#!/bin/zsh
# shellcheck shell=bash
# Terminal session recording and log management utilities

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

    # Create a session-specific PID file
    PID_FILE="/tmp/terminal_record_${TIMESTAMP}.pid"

    # Cleanup function to handle all processes
    cleanup() {
        echo "Cleaning up processes..."

        # Kill the cleaner process if it exists
        if [[ -n "$CLEANER_PID" ]]; then
            pkill -P "$CLEANER_PID" 2>/dev/null
            kill "$CLEANER_PID" 2>/dev/null
        fi

        # Kill any remaining script/ttyrec processes for this session
        pgrep -f "script.*$TXT_FILE" | xargs kill -TERM 2>/dev/null
        pgrep -f "ttyrec.*$TTY_FILE" | xargs kill -TERM 2>/dev/null

        # Remove PID file
        rm -f "$PID_FILE"

        # Remove trap
        trap - EXIT HUP TERM INT
    }

    # Set up comprehensive trap
    trap cleanup EXIT HUP TERM INT

    # Start the background cleaner process
    nohup bash -c "stdbuf -oL tail -f -n +1 \"$TXT_FILE\" | \"$LOGGER_SCRIPT\" > \"$CLEAN_FILE\"" >/dev/null 2>&1 &
    CLEANER_PID=$!
    echo "$CLEANER_PID" > "$PID_FILE"

    # Run script and ttyrec in the foreground
    script -q "$TXT_FILE" /bin/sh -c "exec ttyrec \"$TTY_FILE\""

    # Ensure cleanup runs
    cleanup
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

rotate_logs() {
    # Create temporary file for open files list
    local tmp_exclusions=$(mktemp)

    # Get list of open files in the log directory
    lsof -F n "$LOGDIR"/* 2>/dev/null | grep '^n/' | cut -c 2- > "$tmp_exclusions"

    # Find files and filter out open ones
    fd . "$LOGDIR" \
        --changed-before 1d \
        --type f \
        --threads 1 \
        --exclude "*.zst" \
        -0 | \
    grep -vzZf "$tmp_exclusions" | \
    xargs -0 -I {} zstd -7 --rm "{}"

    # Clean up
    rm -f "$tmp_exclusions"
}

# Check if a TTY is active
is_tty_active() {
    local tty="$1"
    local active_ttys="$2"
    
    # No TTY (shown as "??") is never active
    [[ "$tty" == "??" ]] && return 1
    
    # Strip "tty" prefix if present for comparison
    local tty_short="${tty#tty}"
    
    # Check if TTY (without prefix) is in the active list
    echo "$active_ttys" | grep -q "^$tty_short$"
    return $?
}

# Extract timestamp from command
extract_timestamp() {
    local command="$1"
    
    # Try to extract timestamp using grep
    local timestamp
    timestamp=$(echo "$command" | grep -o "terminal_[0-9]\{8\}_[0-9]\{6\}" | head -1 | sed 's/terminal_//')
    
    if [[ -n "$timestamp" ]]; then
        echo "$timestamp"
        return 0
    fi
    
    return 1
}

# Terminate a process group related to a timestamp
terminate_process_group() {
    local timestamp="$1"
    
    # Find all related processes
    local related_pids=$(ps -eo pid,command | grep "terminal_${timestamp}" | grep -v grep | awk '{print $1}')
    
    # If no related processes found, return early
    [[ -z "$related_pids" ]] && return 0
    
    echo "Found $(echo "$related_pids" | wc -l | tr -d ' ') related processes"
    
    # First try TERM signal
    echo "Sending TERM signal to all processes..."
    echo "$related_pids" | xargs -n1 kill -TERM 2>/dev/null
    
    # Wait a second
    sleep 1
    
    # Check if any processes are still running and use KILL if needed
    local still_running=$(echo "$related_pids" | xargs -n1 ps -p 2>/dev/null | grep -v PID | awk '{print $1}')
    if [[ -n "$still_running" ]]; then
        echo "Some processes still running, sending KILL signal..."
        echo "$still_running" | xargs -n1 kill -KILL 2>/dev/null
    fi
    
    return 0
}

# Clean up PID file for a timestamp
cleanup_pid_file() {
    local timestamp="$1"
    local pid_file="/tmp/terminal_record_${timestamp}.pid"
    
    if [[ -f "$pid_file" ]]; then
        rm -f "$pid_file"
        echo "Removed PID file: $pid_file"
    fi
}

# Function to reap orphaned terminal recording processes
function reap_orphaned_processes() {
    echo "Checking for orphaned terminal recording processes..."
    
    # Get list of active TTYs (one per line)
    local active_ttys=$(w -h | awk '{print $2}' | sort | uniq)
    echo "Active TTYs: $(echo "$active_ttys" | tr '\n' ' ')"
    
    # Create a temporary file to store processed timestamps
    local tmp_processed=$(mktemp)
    trap "rm -f $tmp_processed" EXIT
    
    # Find all ttyrec processes
    local ttyrec_processes=$(ps -eo pid,ppid,tty,lstart,command | grep ttyrec | grep -v grep)
    
    if [[ -z "$ttyrec_processes" ]]; then
        echo "No ttyrec processes found."
        rm -f "$tmp_processed"
        return 0
    fi
    
    local total_processes=$(echo "$ttyrec_processes" | wc -l)
    echo "Found $total_processes ttyrec processes"
    
    local orphaned_count=0
    local processed_count=0
    
    # Process each ttyrec process
    echo "$ttyrec_processes" | while read -r line; do
        local pid=$(echo "$line" | awk '{print $1}')
        local tty=$(echo "$line" | awk '{print $3}')
        local command=$(echo "$line" | awk '{for(i=5;i<=NF;i++) printf "%s ", $i; print ""}')
        
        # Extract timestamp from command
        local timestamp=$(extract_timestamp "$command")
        
        # Skip if no timestamp found
        [[ -z "$timestamp" ]] && continue
        
        # Skip if we've already processed this timestamp
        if grep -q "^$timestamp$" "$tmp_processed"; then
            continue
        fi
        
        # Mark this timestamp as processed
        echo "$timestamp" >> "$tmp_processed"
        ((processed_count++))
        
        # Check if session is active
        if is_tty_active "$tty" "$active_ttys"; then
            continue
        fi
        
        # If we get here, the session is orphaned
        echo "Found orphaned session: Timestamp $timestamp, TTY $tty"
        ((orphaned_count++))
        
        # Terminate process group and clean up PID file
        terminate_process_group "$timestamp"
        cleanup_pid_file "$timestamp"
    done
    
    echo "Processed $processed_count unique sessions, terminated $orphaned_count orphaned sessions"
    echo "Orphaned process check complete"
}
