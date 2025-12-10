---
name: jujutsu
description: |
  Jujutsu (jj) version control commands. Use when working in a jj repository, 
  running version control operations, viewing commit history, managing bookmarks 
  (branches), creating or splitting commits, pushing to Git remotes, or any VCS 
  task in a repo with a .jj directory. Also use when the user mentions jj, 
  change IDs, revsets, or working-copy commits.
---

# Jujutsu (jj) Version Control

Jujutsu is a Git-compatible VCS. Key differences from Git:

- **Working copy IS the commit**: No staging area. Your filesystem is always the current commit (`@`).
- **Changes vs commits**: Mutable "changes" have stable IDs even when rewritten.
- **Bookmarks**: Named pointers to revisions (analogous to Git branches).
- **Automatic snapshots**: Every command snapshots working copy first.

## Quick Reference

| Task | Command |
|------|---------|
| Status | `jj st` or `jj status` |
| Log | `jj log -n 10` |
| Diff working copy | `jj diff` |
| Diff specific revision | `jj diff -r @-` |
| Create new empty change | `jj new` |
| Describe current change | `jj describe -m "message"` |
| Commit (describe + new) | `jj commit -m "message"` |
| Edit historical change | `jj edit <rev>` |
| Split change | `jj split` (interactive) or `jj split <paths>` |
| Abandon change | `jj abandon` |
| Undo last operation | `jj undo` |

## Status and Inspection

```bash
# Current status (working copy, parents, changes, conflicts)
jj st --no-pager

# View log with graph
jj log -n 10

# Full history
jj log -r 'all()'

# Log with file change summary
jj log --summary -n 5

# Show specific revision
jj show <rev>
```

## Diffing

```bash
# Diff working copy vs parent
jj diff

# Diff specific revision vs its parent
jj diff -r @-

# Diff between two revisions
jj diff --from main --to @

# Output formats
jj diff --summary          # Modified/added/deleted per file
jj diff --stat             # Line histogram
jj diff --name-only        # Just paths (good for scripting)
jj diff --git              # Git-format patch

# Specific paths only
jj diff src/lib.rs tests/
```

## Creating and Modifying Changes

```bash
# Start new empty change on top of current
jj new

# Start new change with description
jj new -m "Start feature X"

# Update description of current change
jj describe -m "Better description"

# Commit: describe current + create new empty change
jj commit -m "Finished feature"

# Edit a historical change (descendants auto-rebase)
jj edit <rev>
```

Do not include "Generated with Claude Code" in the commit message.

Remember `jj squash` is an interactive command, try to avoid it and it is OK to have code in separate changes. If you need to squash first consult `jj squash --help` for more information.

Remember, after doing `jj describe` to describe a change, you need to create a new change with `jj new` to create a new change on top so that at the end there is no changes left. Another way to do this is to run `jj new && jj tug && jj gp`, this will:

- Create a new change on top of the current change
- Tug the top bookmark (branch) to the previous change
- Push that bookmark to the remote repository

## Splitting Changes

Split separates a revision into two. By default interactive; provide paths for non-interactive.

```bash
# Interactive split (opens diff editor)
jj split

# Non-interactive: put only src/utils.rs in first commit
jj split src/utils.rs -m "Extract utils"

# Split with parallel changes (not parent/child)
jj split --parallel src/utils.rs
```

When paths are provided, those files go into the **first** commit; everything else becomes a new commit on top.

## Bookmarks (Branches)

Bookmarks are named pointers to revisions. They do NOT auto-advance with new commits.

```bash
# List bookmarks
jj bookmark list

# Create bookmark at current revision
jj bookmark create feature-x

# Create at specific revision
jj bookmark create -r <rev> feature-x

# Move bookmark to current revision
jj bookmark set feature-x

# Delete bookmark
jj bookmark delete feature-x

# Track remote bookmark
jj bookmark track main@origin
```

## Git Operations

```bash
# Fetch from origin (or configured default)
jj git fetch

# Fetch from specific remote
jj git fetch --remote upstream

# Push bookmarks to remote
jj git push

# Push allowing new bookmarks
jj git push --allow-new

# Push specific bookmark
jj git push --bookmark feature-x
```

## Revsets (Revision Selection)

Revsets select commits. Common expressions:

| Revset | Meaning |
|--------|---------|
| `@` | Working copy commit |
| `@-` | Parent of working copy |
| `@--` | Grandparent |
| `root()` | Root commit |
| `heads(x)` | Heads of revset x |
| `x::y` | x to y (inclusive) |
| `::@` | All ancestors of @ |
| `@::` | All descendants of @ |
| `x..y` | Ancestors of y not ancestors of x |
| `bookmarks()` | All local bookmarks |
| `remote_bookmarks()` | All remote bookmarks |
| `mutable()` | Mutable revisions |
| `mine()` | Commits authored by you |

Examples:

```bash
jj log -r '::@'              # All ancestors
jj log -r 'bookmarks()'      # All bookmarked commits
jj log -r 'main..@'          # Commits since main
jj rebase -r @ -d main       # Rebase current onto main
```

## Rebasing

```bash
# Rebase current change onto main
jj rebase -d main

# Rebase specific revision
jj rebase -r <rev> -d main

# Rebase a branch (revision and descendants)
jj rebase -b <rev> -d main

# Rebase source onto multiple destinations (merge)
jj rebase -s <rev> -d dest1 -d dest2
```

## Conflict Resolution

Conflicts appear as conflict markers in files. Jujutsu tracks both sides.

```bash
# See conflicts in status
jj st

# Resolve with external tool
jj resolve <path>

# After manual edit, conflicts auto-resolve on next snapshot
```

## Operation Log and Undo

Every jj command creates an operation. You can undo/redo.

```bash
# View operation history
jj op log

# Undo last operation
jj undo

# Restore to specific operation
jj op restore <op-id>
```

## Typical LLM Agent Workflow

1. **Inspect state**:
   ```bash
   jj st --no-pager
   jj log -n 5
   ```

2. **Make changes** (just edit files - they're auto-snapshotted)

3. **Review changes**:
   ```bash
   jj diff --summary
   jj diff
   ```

4. **Describe the change**:
   ```bash
   jj describe -m "Implement feature X"
   ```

5. **Create new change for next task**:
   ```bash
   jj new
   ```

6. **Before pushing, update bookmark**:
   ```bash
   jj bookmark set feature-x
   jj git push --allow-new
   ```

## Tips for Agents

- Use `--no-pager` when capturing output programmatically.
- Working copy is always a commit - no need to stage.
- `jj new` without args creates empty change on top of @.
- Bookmark must be explicitly set before push (they don't auto-advance).
- `jj undo` is your friend - every operation is reversible.
- Change IDs (like `xyz`) are stable across rewrites; commit IDs change.
