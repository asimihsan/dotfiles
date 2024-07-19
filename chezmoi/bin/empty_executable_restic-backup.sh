#!/bin/bash

set -euo pipefail

eval "$(devbox global shellenv)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the configuration file
CONFIG_FILE="${SCRIPT_DIR}/restic-config.sh"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi
source "$CONFIG_FILE"

# Function to run restic commands
run_restic() {
    restic -r "rclone:$ALIAS_REMOTE:" \
        --verbose \
        --password-command "$PASSWORD_COMMAND" \
        "$@"
}

# Function to setup rclone
setup_rclone() {
    echo "Setting up rclone..."
    rclone config create "$DROPBOX_REMOTE" dropbox
    rclone config create "$ALIAS_REMOTE" alias "remote=$DROPBOX_REMOTE:$DROPBOX_PATH"
}

# Function to initialize restic repository
init_restic() {
    echo "Initializing restic repository..."
    run_restic init
}

# Function to perform backup
do_backup() {
    echo "Performing backup..."
    run_restic backup \
        --exclude-caches \
        --pack-size 64 \
        "${BACKUP_PATHS[@]}"
}

# Function to list snapshots
list_snapshots() {
    echo "Listing snapshots..."
    run_restic snapshots
}

# Function to restore a snapshot
restore_snapshot() {
    if [ $# -ne 2 ]; then
        echo "Usage: $0 restore <snapshot-id> <target-path>"
        exit 1
    fi
    local snapshot_id="$1"
    local target_path="$2"
    echo "Restoring snapshot $snapshot_id to $target_path..."
    run_restic restore "$snapshot_id" --target "$target_path"
}

# Function to forget old snapshots and prune
forget_and_prune() {
    local cleanup_cache=""
    if [[ "${1-}" == "--cleanup-cache" ]]; then
        cleanup_cache="--cleanup-cache"
    fi
    echo "Forgetting old snapshots and pruning..."
    run_restic forget \
        --keep-hourly 4 \
        --keep-daily 7 \
        --keep-weekly 4 \
        --keep-monthly 1 \
        --prune \
        ${cleanup_cache}
}

# Main function
main() {
    case "${1:-}" in
        setup)
            setup_rclone
            init_restic
            ;;
        backup)
            do_backup
            ;;
        list)
            list_snapshots
            ;;
        restore)
            restore_snapshot "${@:2}"
            ;;
        prune)
            forget_and_prune
            ;;
        prune-cache)
            forget_and_prune --cleanup-cache
            ;;
        *)
            echo "Usage: $0 {setup|backup|list|restore|prune|prune-cache}"
            exit 1
            ;;
    esac
}

main "$@"
