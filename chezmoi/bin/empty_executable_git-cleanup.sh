#!/usr/bin/env bash

# Enable strict mode and debugging
set -euo pipefail

# Default values
DEFAULT_DAYS=30
DEFAULT_DRY_RUN=true
DEFAULT_MAIN_BRANCH="master"
DEFAULT_REMOVE_WORKTREES=false

# Function to display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Cleanup old and obsolete Git branches"
    echo
    echo "Options:"
    echo "  -d, --days DAYS    Delete branches older than DAYS days (default: $DEFAULT_DAYS)"
    echo "  -f, --force        Actually delete branches (default: dry run)"
    echo "  -m, --main BRANCH  Specify the main branch (default: $DEFAULT_MAIN_BRANCH)"
    echo "  -w, --worktrees    Remove worktrees associated with deleted branches"
    echo "  -h, --help         Display this help message"
}

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Parse command line arguments
days=$DEFAULT_DAYS
dry_run=$DEFAULT_DRY_RUN
main_branch=$DEFAULT_MAIN_BRANCH
remove_worktrees=$DEFAULT_REMOVE_WORKTREES

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--days)
            days="$2"
            shift 2
            ;;
        -f|--force)
            dry_run=false
            shift
            ;;
        -m|--main)
            main_branch="$2"
            shift 2
            ;;
        -w|--worktrees)
            remove_worktrees=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Ensure we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    log "Error: Not in a git repository"
    exit 1
fi

# Fetch updates for all branches
log "Fetching updates for all branches..."
git fetch --all

# Function to check if a branch is used by a worktree
is_branch_in_worktree() {
    local branch="$1"
    git worktree list --porcelain | grep -q "branch refs/heads/${branch}"
}

# Function to remove a worktree associated with a branch
remove_worktree() {
    local branch="$1"
    local worktree_path
    worktree_path=$(git worktree list | grep -F "refs/heads/${branch}" | awk '{print $1}')
    if [ -z "$worktree_path" ]; then
        echo "No worktree found for branch '$branch'"
        return 1
    fi
    if [ "$dry_run" = true ]; then
        echo "Would remove worktree for branch '$branch' at path: $worktree_path"
    else
        if git worktree remove --force "$worktree_path"; then
            echo "Removed worktree for branch '$branch' at path: $worktree_path"
        else
            echo "Failed to remove worktree for branch '$branch' at path: $worktree_path"
            return 1
        fi
    fi
}

# Function to delete or echo branch names
process_branch() {
    local branch="$1"
    if [[ "$branch" == "+" ]]; then
        return  # Skip the '+' character
    fi
    if is_branch_in_worktree "$branch"; then
        if [ "$remove_worktrees" = true ]; then
            if remove_worktree "$branch"; then
                if [ "$dry_run" = false ]; then
                    if git branch -D "$branch"; then
                        echo "Deleted branch: $branch"
                    else
                        echo "Failed to delete branch: $branch"
                    fi
                else
                    echo "Would delete branch: $branch"
                fi
            else
                echo "Skipping deletion of branch '$branch' due to worktree removal failure"
            fi
        else
            echo "Cannot delete branch '$branch': It is used by a worktree. Use -w to remove worktrees."
        fi
    elif [ "$dry_run" = true ]; then
        echo "Would delete branch: $branch"
    else
        if git branch -D "$branch"; then
            echo "Deleted branch: $branch"
        else
            echo "Failed to delete branch: $branch"
        fi
    fi
}

# Delete branches without remote tracking branches
log "Processing branches without remote tracking branches..."
git -c pager.branch=false branch -vv | grep ': gone]' | sed 's/^[* ] //; s/ .*$//' | while IFS= read -r branch; do
    if [ "$branch" != "$main_branch" ]; then
        process_branch "$branch"
    fi
done

# Delete old branches
log "Processing branches older than $days days..."
git -c pager.branch=false for-each-ref --format='%(refname:short)' refs/heads/ | while IFS= read -r branch; do
    if [ "$branch" != "$main_branch" ]; then
        date=$(git log -1 --format=%cd --date=relative "$branch")
        if [[ "$date" =~ year|month ]] || \
           { [[ "$date" =~ "weeks ago" ]] && [[ "${date%% *}" -ge 8 ]]; } || \
           { [[ "$date" =~ "days ago" ]] && [[ "${date%% *}" -gt "$days" ]]; }; then
            process_branch "$branch"
        fi
    fi
done

# Final message
if [ "$dry_run" = true ]; then
    log "Dry run completed. Use -f or --force to actually delete branches."
else
    log "Branch cleanup completed."
fi

# List remaining branches
log "Remaining branches:"
git -c pager.branch=false for-each-ref --format='%(refname:short) (%(committerdate:relative))' refs/heads/
