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

error() {
    echo "Error: $1" >&2
    exit 1
}

cmd_restore() {
    local snapshot_id=""
    local target_path=""
    local subfolder=""
    local verify=false
    local exclude=()
    local include=()

    parse_restore_args "$@"

    if [[ -z "$snapshot_id" || -z "$target_path" ]]; then
        error "Both snapshot ID and target path are required for restore"
    fi

    local restore_cmd=(run_restic restore)

    if [[ -n "$subfolder" ]]; then
        restore_cmd+=("$snapshot_id:$subfolder")
    else
        restore_cmd+=("$snapshot_id")
    fi

    restore_cmd+=("--target" "$target_path")

    if $verify; then
        restore_cmd+=("--verify")
    fi

    if [[ ${#exclude[@]} -gt 0 ]]; then
        for pattern in "${exclude[@]}"; do
            restore_cmd+=("--exclude" "$pattern")
        done
    fi

    if [[ ${#include[@]} -gt 0 ]]; then
        for pattern in "${include[@]}"; do
            restore_cmd+=("--include" "$pattern")
        done
    fi

    echo "Restoring snapshot $snapshot_id to $target_path..."
    if [[ -n "$subfolder" ]]; then
        echo "Restoring subfolder: $subfolder"
    fi
    "${restore_cmd[@]}"
}

parse_restore_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
        --snapshot-id)
            snapshot_id="$2"
            shift 2
            ;;
        --target)
            target_path="$2"
            shift 2
            ;;
        --subfolder)
            subfolder="$2"
            shift 2
            ;;
        --verify)
            verify=true
            shift
            ;;
        --exclude)
            exclude+=("$2")
            shift 2
            ;;
        --include)
            include+=("$2")
            shift 2
            ;;
        *)
            error "Unknown option for restore: $1"
            ;;
        esac
    done
}

cmd_ls() {
    local snapshot_id="latest"
    local long_format=false
    local human_readable=false
    local recursive=false
    local hosts=()
    local paths=()
    local tags=()
    local dirs=()

    parse_ls_args "$@"

    local ls_cmd=(run_restic ls "$snapshot_id")

    if $long_format; then
        ls_cmd+=("--long")
    fi

    if $human_readable; then
        ls_cmd+=("--human-readable")
    fi

    if $recursive; then
        ls_cmd+=("--recursive")
    fi

    if [[ ${#hosts[@]} -gt 0 ]]; then
        for host in "${hosts[@]}"; do
            ls_cmd+=("--host" "$host")
        done
    fi

    if [[ ${#paths[@]} -gt 0 ]]; then
        for path in "${paths[@]}"; do
            ls_cmd+=("--path" "$path")
        done
    fi

    if [[ ${#tags[@]} -gt 0 ]]; then
        for tag in "${tags[@]}"; do
            ls_cmd+=("--tag" "$tag")
        done
    fi

    if [[ ${#dirs[@]} -eq 0 ]]; then
        dirs=("/")
    fi
    ls_cmd+=("${dirs[@]}")

    echo "Listing files for snapshot: $snapshot_id, dirs: ${dirs[*]}"
    "${ls_cmd[@]}"
}

parse_ls_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
        --snapshot-id)
            snapshot_id="$2"
            shift 2
            ;;
        -l | --long)
            long_format=true
            shift
            ;;
        --human-readable)
            human_readable=true
            shift
            ;;
        --recursive)
            recursive=true
            shift
            ;;
        -H | --host)
            hosts+=("$2")
            shift 2
            ;;
        --path)
            paths+=("$2")
            shift 2
            ;;
        --tag)
            tags+=("$2")
            shift 2
            ;;
        -*)
            error "Unknown option for ls: $1"
            ;;
        *)
            dirs+=("$1")
            shift
            ;;
        esac
    done
}

cmd_setup() {
    setup_rclone
    init_restic
}

cmd_backup() {
    do_backup
}

cmd_list() {
    list_snapshots
}

cmd_prune() {
    forget_and_prune
}

cmd_unlock() {
    unlock
}

cmd_mount() {
    mount "$@"
}

cmd_stats() {
    stats
}

# Function to run restic commands
run_restic() {
    restic -r "rclone:$ALIAS_REMOTE:" \
        --verbose \
        --password-command "$PASSWORD_COMMAND" \
        --limit-download 1024 \
        --limit-upload 1024 \
        --option rclone.connections=10 \
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
        --exclude-file "${SCRIPT_DIR}/restic-excludes" \
        --pack-size 16 \
        --read-concurrency 4 \
        "${BACKUP_PATHS[@]}"
    forget_and_prune --cleanup-cache
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
        --keep-monthly 1
    run_restic prune \
        --repack-small \
        --repack-uncompressed \
        --max-repack-size 1G \
        ${cleanup_cache}
}

unlock() {
    echo "Unlocking repository..."
    run_restic unlock
}

mount() {
    if [ $# -ne 1 ]; then
        echo "Usage: $0 mount <mount-path>"
        exit 1
    fi
    local mount_path="$1"
    echo "Mounting repository at $mount_path..."
    restic -r "rclone:$ALIAS_REMOTE:" \
        --password-command "$PASSWORD_COMMAND" \
        mount "$mount_path"
}

stats() {
    echo "Getting repository stats..."
    run_restic stats --mode blobs-per-file
}

usage() {
    cat <<EOF
Usage: $0 <command> [options]

Commands:
  setup               Setup rclone and initialize restic repository
  backup              Perform a backup
  list                List snapshots
  restore             Restore files from a snapshot
  ls                  List files in a snapshot
  prune               Forget old snapshots and prune the repository
  unlock              Unlock the repository
  mount               Mount the repository
  stats               Show repository statistics

Use "$0 <command> --help" for more information about a command.
EOF
    exit 1
}

cmd_help() {
    local command="$1"
    case "$command" in
    restore)
        cat <<EOF
Usage: $0 restore [options] --snapshot-id <id> --target <path>

Options:
  --snapshot-id <id>   ID of the snapshot to restore (use "latest" for the most recent)
  --target <path>      Directory to extract data to
  --subfolder <path>   Only restore a specific subfolder from the snapshot
  --verify             Verify restored files content
  --exclude <pattern>  Exclude files/dirs that match the pattern (can be specified multiple times)
  --include <pattern>  Include only files/dirs that match the pattern (can be specified multiple times)
EOF
        ;;
    ls)
        cat <<EOF
Usage: $0 ls [options] [<snapshot-id>] [<dir>...]

Options:
  --snapshot-id <id>   ID of the snapshot to list (default: latest)
  -l, --long           Use a long listing format showing size and mode
  --human-readable     Print sizes in human readable format
  --recursive          Include files in subfolders of the listed directories
  -H, --host <host>    Only consider snapshots for this host (can be specified multiple times)
  --path <path>        Only consider snapshots including this path (can be specified multiple times)
  --tag <tag>          Only consider snapshots with this tag (can be specified multiple times)
EOF
        ;;
    *)
        error "No help available for command: $command"
        ;;
    esac
    exit 0
}

main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi

    local command="$1"
    shift

    case "$command" in
    setup)
        cmd_setup "$@"
        ;;
    backup)
        cmd_backup "$@"
        ;;
    list)
        cmd_list "$@"
        ;;
    restore)
        cmd_restore "$@"
        ;;
    ls)
        cmd_ls "$@"
        ;;
    prune)
        cmd_prune "$@"
        ;;
    prune-cache)
        cmd_prune --cleanup-cache
        ;;
    unlock)
        cmd_unlock "$@"
        ;;
    mount)
        cmd_mount "$@"
        ;;
    stats)
        cmd_stats "$@"
        ;;
    help|--help|-h)
        if [[ $# -eq 0 ]]; then
            usage
        else
            cmd_help "$1"
        fi
        ;;
    *)
        error "Unknown command: $command"
        ;;
    esac
}

main "$@"
