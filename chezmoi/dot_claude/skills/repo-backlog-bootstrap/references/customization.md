# Customization Checklist

Use this checklist after running `scripts/bootstrap_repo.py`.

## 1) Set project-specific AGENTS goal

If AGENTS was written from template, replace the goal sentence with a concrete
repo goal (one sentence).

## 2) Confirm eight-digit task-id convention

Default templates use strict eight-digit IDs, for example:
- `task-00000001_<slug>.md`
- `task-00000042_fix-retry-loop.md`

If this repository already has older task IDs, migrate them and update references
in open plans/tasks so IDs stay consistent.

## 3) Wire `mise run dev`

Template tasks intentionally use placeholders. Replace in `tasks.core.toml`:
- `fmt`
- `lint`
- `test`

Then validate:

```bash
mise install
mise tasks
mise run dev
```

## 4) Decide backlog tracking policy

Default behavior keeps backlog local-only by adding `backlog/` to `.git/info/exclude`.

If you want backlog files tracked in Git:
1. Run bootstrap with `--track-backlog` (or remove `backlog/` from `.git/info/exclude`).
2. Add and commit backlog files normally.

## 5) Validate jujutsu status

For existing Git repositories with no `.jj` directory:

```bash
jj git init --colocate
```

Then check:

```bash
jj st --no-pager
jj log -n 5
```
