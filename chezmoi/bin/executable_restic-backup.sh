#!/bin/bash

set -euo pipefail

if command -v devbox >/dev/null 2>&1; then
    eval "$(devbox global shellenv)"
fi

if command -v mise >/dev/null 2>&1; then
    eval "$(mise activate bash)"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ORIGINAL_ALIAS_REMOTE="${ALIAS_REMOTE:-}"
ORIGINAL_PASSWORD_COMMAND="${PASSWORD_COMMAND:-}"

# Source the configuration file
CONFIG_FILE="${SCRIPT_DIR}/restic-config.sh"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi
source "$CONFIG_FILE"

# If ORIGINAL_ALIAS_REMOTE is set then restore it
if [[ -n "$ORIGINAL_ALIAS_REMOTE" ]]; then
    ALIAS_REMOTE="$ORIGINAL_ALIAS_REMOTE"
fi

# If ORIGINAL_PASSWORD_COMMAND is set then restore it
if [[ -n "$ORIGINAL_PASSWORD_COMMAND" ]]; then
    PASSWORD_COMMAND="$ORIGINAL_PASSWORD_COMMAND"
fi

expand_password_command() {
    # Restic executes the command without shell expansion, so replace common env vars here.
    PASSWORD_COMMAND="${PASSWORD_COMMAND//\$USER/$USER}"
    PASSWORD_COMMAND="${PASSWORD_COMMAND//\${USER}/$USER}"
    PASSWORD_COMMAND="${PASSWORD_COMMAND//\$HOME/$HOME}"
    PASSWORD_COMMAND="${PASSWORD_COMMAND//\${HOME}/$HOME}"
}

validate_config() {
    if [[ -z "${ALIAS_REMOTE:-}" ]]; then
        error "ALIAS_REMOTE is not set. Check restic-config.sh or export ALIAS_REMOTE."
    fi
    if [[ -z "${PASSWORD_COMMAND:-}" ]]; then
        error "PASSWORD_COMMAND is not set. Check restic-config.sh or export PASSWORD_COMMAND."
    fi
}

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

cmd_forget() {
    local keep_last=""
    local keep_hourly=""
    local keep_daily=""
    local keep_weekly=""
    local keep_monthly=""
    local keep_yearly=""
    local keep_within=""
    local keep_within_hourly=""
    local keep_within_daily=""
    local keep_within_weekly=""
    local keep_within_monthly=""
    local keep_within_yearly=""
    local keep_tags=()
    local hosts=()
    local tags=()
    local paths=()
    local group_by="host,paths"
    local dry_run=false
    local prune=false
    local compact=false
    local snapshot_ids=()

    parse_forget_args "$@"

    local forget_cmd=(run_restic forget)

    if [[ -n "$keep_last" ]]; then
        forget_cmd+=("--keep-last" "$keep_last")
    fi
    if [[ -n "$keep_hourly" ]]; then
        forget_cmd+=("--keep-hourly" "$keep_hourly")
    fi
    if [[ -n "$keep_daily" ]]; then
        forget_cmd+=("--keep-daily" "$keep_daily")
    fi
    if [[ -n "$keep_weekly" ]]; then
        forget_cmd+=("--keep-weekly" "$keep_weekly")
    fi
    if [[ -n "$keep_monthly" ]]; then
        forget_cmd+=("--keep-monthly" "$keep_monthly")
    fi
    if [[ -n "$keep_yearly" ]]; then
        forget_cmd+=("--keep-yearly" "$keep_yearly")
    fi
    if [[ -n "$keep_within" ]]; then
        forget_cmd+=("--keep-within" "$keep_within")
    fi
    if [[ -n "$keep_within_hourly" ]]; then
        forget_cmd+=("--keep-within-hourly" "$keep_within_hourly")
    fi
    if [[ -n "$keep_within_daily" ]]; then
        forget_cmd+=("--keep-within-daily" "$keep_within_daily")
    fi
    if [[ -n "$keep_within_weekly" ]]; then
        forget_cmd+=("--keep-within-weekly" "$keep_within_weekly")
    fi
    if [[ -n "$keep_within_monthly" ]]; then
        forget_cmd+=("--keep-within-monthly" "$keep_within_monthly")
    fi
    if [[ -n "$keep_within_yearly" ]]; then
        forget_cmd+=("--keep-within-yearly" "$keep_within_yearly")
    fi
    if [ ${#keep_tags[@]} -gt 0 ]; then
        for tag in "${keep_tags[@]}"; do
            forget_cmd+=("--keep-tag" "$tag")
        done
    fi
    if [ ${#hosts[@]} -gt 0 ]; then
        for host in "${hosts[@]}"; do
            forget_cmd+=("--host" "$host")
        done
    fi

    if [ ${#tags[@]} -gt 0 ]; then
        for tag in "${tags[@]}"; do
            forget_cmd+=("--tag" "$tag")
        done
    fi

    if [ ${#paths[@]} -gt 0 ]; then
        for path in "${paths[@]}"; do
            forget_cmd+=("--path" "$path")
        done
    fi
    forget_cmd+=("--group-by" "$group_by")
    if $dry_run; then
        forget_cmd+=("--dry-run")
    fi
    if $prune; then
        forget_cmd+=("--prune")
    fi
    if $compact; then
        forget_cmd+=("--compact")
    fi

    forget_cmd+=("${snapshot_ids[@]}")

    echo "Forgetting snapshots..."
    "${forget_cmd[@]}"
}

parse_forget_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
        --keep-last)
            keep_last="$2"
            shift 2
            ;;
        --keep-hourly)
            keep_hourly="$2"
            shift 2
            ;;
        --keep-daily)
            keep_daily="$2"
            shift 2
            ;;
        --keep-weekly)
            keep_weekly="$2"
            shift 2
            ;;
        --keep-monthly)
            keep_monthly="$2"
            shift 2
            ;;
        --keep-yearly)
            keep_yearly="$2"
            shift 2
            ;;
        --keep-within)
            keep_within="$2"
            shift 2
            ;;
        --keep-within-hourly)
            keep_within_hourly="$2"
            shift 2
            ;;
        --keep-within-daily)
            keep_within_daily="$2"
            shift 2
            ;;
        --keep-within-weekly)
            keep_within_weekly="$2"
            shift 2
            ;;
        --keep-within-monthly)
            keep_within_monthly="$2"
            shift 2
            ;;
        --keep-within-yearly)
            keep_within_yearly="$2"
            shift 2
            ;;
        --keep-tag)
            keep_tags+=("$2")
            shift 2
            ;;
        --host)
            hosts+=("$2")
            shift 2
            ;;
        --tag)
            tags+=("$2")
            shift 2
            ;;
        --path)
            paths+=("$2")
            shift 2
            ;;
        --group-by)
            group_by="$2"
            shift 2
            ;;
        --dry-run)
            dry_run=true
            shift
            ;;
        --prune)
            prune=true
            shift
            ;;
        -c|--compact)
            compact=true
            shift
            ;;
        -*)
            error "Unknown option for forget: $1"
            ;;
        *)
            snapshot_ids+=("$1")
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
    forget_and_prune "$@"
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
        --limit-download 5120 \
        --limit-upload 2048 \
        --option rclone.connections=5 \
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

# ====================================================================
#  🚩  APFS-snapshot helpers  (macOS only; no-ops elsewhere)
# ====================================================================

# Keep a fixed mount-point so everything is deterministic
SNAP_MNT=/tmp/restic-snap

SNAP_MOUNTED=false

sudo_nonint() { sudo -n "$@"; }   # -n = “no password prompt”

create_apfs_snapshot() {
    [[ "$(uname)" != "Darwin" ]] && return 0    # no-op on Linux

    if ! out=$(sudo_nonint /usr/bin/tmutil localsnapshot 2>&1); then
        echo "tmutil localsnapshot failed – sudo rule missing?" >&2
        exit 1
    fi
    SNAP_DATE=$(grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{6}' <<<"$out")
    SNAP_NAME="com.apple.TimeMachine.${SNAP_DATE}.local"
}

mount_apfs_snapshot() {
    [[ -z "${SNAP_NAME:-}" ]] && return 0
    mkdir -p "$SNAP_MNT"

    disk="$(diskutil info -plist /System/Volumes/Data | plutil -extract DeviceNode xml1 -o - - | xmllint --xpath '//string/text()' -)"
    if sudo_nonint mount_apfs -o ro -s "$SNAP_NAME" "$disk" "$SNAP_MNT"; then
        SNAP_MOUNTED=true
    fi
}

unmount_apfs_snapshot() {
    [[ "$SNAP_MOUNTED" = false ]] && return 0
    disk="$(diskutil info -plist /System/Volumes/Data | plutil -extract DeviceNode xml1 -o - - | xmllint --xpath '//string/text()' -)"
    sudo_nonint umount "$SNAP_MNT" || sudo_nonint diskutil unmount "$SNAP_MNT"
    rmdir "$SNAP_MNT"
    SNAP_MOUNTED=false
}

delete_apfs_snapshot() {
    [[ -z "${SNAP_DATE:-}" ]] && return 0
    sudo_nonint /usr/bin/tmutil deletelocalsnapshots "$SNAP_DATE" || true
}

thin_old_snapshots() {
    [[ "$(uname)" != "Darwin" ]] && return 0
    echo "Thinning old snapshots…"
    # free plenty of space - 200 GB – with highest urgency
    sudo_nonint /usr/bin/tmutil thinlocalsnapshots / 200000000000 4 2>/dev/null || true
}

purge_old_snapshots() {
    [[ "$(uname)" != "Darwin" ]] && return 0
    echo "Purging old snapshots…"
    local latest
    latest=$(/usr/bin/tmutil listlocalsnapshots / | tail -1)
    # Drop the prefix - tmutil wants just the timestamp component
    latest=${latest##*.}

    echo "Purging old snapshots (keeping $latest)…"
    for snap in $(/usr/bin/tmutil listlocalsnapshots / | sed 1d); do
        ts=${snap##*.}
        [[ "$ts" == "$latest" ]] && continue
        sudo_nonint /usr/bin/tmutil deletelocalsnapshots "$ts"
    done
}

cleanup_snapshot() {
    [[ "$(uname)" != "Darwin" ]] && return 0    # no-op on Linux
    unmount_apfs_snapshot   # silently succeeds if not mounted
    delete_apfs_snapshot    # silently succeeds if no snapshot
    thin_old_snapshots      # optional “vacuum”
    purge_old_snapshots     # optional harder “vacuum”
}

# Fire cleanup on normal exit, Ctrl-C (SIGINT), script error (ERR), or kill
trap cleanup_snapshot EXIT INT TERM
# ====================================================================

# Function to perform backup
do_backup() {
    echo "Creating APFS snapshot..."
    create_apfs_snapshot
    echo "Mounting APFS snapshot..."
    mount_apfs_snapshot

    local snap_prefix="$SNAP_MNT"
    # convert “~/foo” -> "$SNAP_MNT$HOME/foo"
    local -a snap_paths=("${BACKUP_PATHS[@]/#\~/$snap_prefix$HOME}")

    echo "Running restic backup from snapshot..."

    if command -v tag-cache-dirs >/dev/null 2>&1; then
        tag-cache-dirs --root-dir ~/workplace --root-dir ~/Downloads
    fi

    export MISE_DISABLE_TRUST_CHECK=1
    run_restic backup \
        --exclude-caches \
        --exclude-file "${SCRIPT_DIR}/restic-excludes" \
        --pack-size 16 \
        --read-concurrency 4 \
        "${snap_paths[@]}"

    echo "Pruning repository..."
    forget_and_prune
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
    echo "Forgetting old snapshots and pruning..."
    if [[ "${1-}" == "--cleanup-cache" ]]; then
        echo "Will also cleanup cache"
        cleanup_cache="--cleanup-cache"
    fi
    run_restic forget \
        --keep-hourly 4 \
        --keep-daily 7 \
        --keep-weekly 4 \
        --keep-monthly 1
    run_restic prune \
        --repack-small \
        --repack-uncompressed \
        --max-repack-size 2G \
        --max-unused 3% \
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
    forget              Forget snapshots according to a policy
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

    forget)
        cat <<EOF
Usage: $0 forget [options] [snapshot ID] [...]

Options:
    --keep-last n                    Keep the last n snapshots
    --keep-hourly n                  Keep the last n hourly snapshots
    --keep-daily n                   Keep the last n daily snapshots
    --keep-weekly n                  Keep the last n weekly snapshots
    --keep-monthly n                 Keep the last n monthly snapshots
    --keep-yearly n                  Keep the last n yearly snapshots
    --keep-within duration           Keep snapshots newer than duration
    --keep-within-hourly duration    Keep hourly snapshots newer than duration
    --keep-within-daily duration     Keep daily snapshots newer than duration
    --keep-within-weekly duration    Keep weekly snapshots newer than duration
    --keep-within-monthly duration   Keep monthly snapshots newer than duration
    --keep-within-yearly duration    Keep yearly snapshots newer than duration
    --keep-tag taglist               Keep snapshots with this taglist
    --host host                      Only consider snapshots for this host
    --tag tag                        Only consider snapshots with this tag
    --path path                      Only consider snapshots including this path
    --group-by value                 Group snapshots by host,paths,tags
    --dry-run                        Don't delete anything, just print what would be done
    --prune                          Automatically run the 'prune' command
    -c, --compact                    Use compact output format
EOF
        ;;

    *)
        error "No help available for command: $command"
        ;;
    esac
    exit 0
}

check_dependencies() {
    local dependencies=("rclone" "restic" "jq")
    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            error "Dependency $dep is not installed. Please install it."
        fi
    done
}

main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi

    local command="$1"
    shift

    expand_password_command
    validate_config

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
        cmd_prune "$@" --cleanup-cache
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
    forget)
        cmd_forget "$@"
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

check_dependencies
main "$@"
