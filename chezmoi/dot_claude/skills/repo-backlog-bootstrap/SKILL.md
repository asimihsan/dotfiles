---
name: repo-backlog-bootstrap
description: Bootstrap or retrofit repositories with a standard backlog workflow (`backlog/docs`, `backlog/plans`, `backlog/tasks`), AGENTS.md conventions, and jujutsu/mise defaults. Use when creating a new repo or standardizing an existing repo to the backlog + `jj` + `mise` operating model.
---

# Repo Backlog Bootstrap

Use this skill to establish or retrofit repository operating standards around:
- backlog planning artifacts
- AGENTS.md collaboration guardrails
- jujutsu workflow expectations
- mise-based local task automation

## Quick Start

```bash
# Preview changes first
python scripts/bootstrap_repo.py --repo /path/to/repo --dry-run

# Apply bootstrap defaults
python scripts/bootstrap_repo.py --repo /path/to/repo

# For brand-new repos, replace AGENTS.md using the template
python scripts/bootstrap_repo.py \
  --repo /path/to/repo \
  --agents-mode overwrite \
  --project-goal "an easy to maintain service with reproducible local workflows"

# Initialize jj automatically when .jj is missing and .git exists
python scripts/bootstrap_repo.py --repo /path/to/repo --init-jj
```

## Workflow

1. Inspect target repository state (`AGENTS.md`, `backlog/`, `.jj`, `mise.toml`).
2. Create missing backlog directories:
   - `backlog/docs/`
   - `backlog/plans/`
   - `backlog/tasks/`
   - `backlog/tasks/completed/`
3. Install backlog templates from `assets/templates/backlog/`.
4. Ensure `backlog/` is listed in `.git/info/exclude` when `.git/` exists.
5. Update AGENTS.md:
   - `overwrite` mode: write `assets/templates/AGENTS.new.md` (for new repos).
   - `merge` mode: append missing workflow and backlog sections to existing AGENTS.md.
6. Ensure mise bootstrap defaults when missing:
   - `mise.toml`
   - `tasks.core.toml`
   - `scripts/env.sh`
   - `scripts/postinstall.sh`
7. Ensure jujutsu readiness:
   - If `.jj` exists, leave it unchanged.
   - If `.jj` is missing, recommend `jj git init --colocate`.
   - If `--init-jj` is passed and `.git` exists, run that command automatically.

## Script Interface

Run `python scripts/bootstrap_repo.py --help`.

Key flags:
- `--repo <path>`: target repository (defaults to current directory).
- `--agents-mode auto|overwrite|merge|skip`: AGENTS.md handling strategy.
- `--project-goal "<text>"`: project-goal sentence for AGENTS overwrite template.
- `--force`: overwrite generated templates.
- `--skip-mise`: skip mise bootstrap files.
- `--init-jj`: run `jj git init --colocate` if `.jj` is missing and `.git` exists.
- `--dry-run`: print planned changes without writing.

## Resources

- `scripts/bootstrap_repo.py`: deterministic bootstrap and merge utility.
- `assets/templates/backlog/`: plan/task templates and backlog docs README.
- `assets/templates/AGENTS*.md`: AGENTS full template plus merge sections.
- `assets/templates/mise*.toml`: baseline mise configuration templates.
- `references/customization.md`: follow-up customization checklist.

## Doc Lookup

When behavior needs verification, use these local docs:
- Jujutsu: `../jujutsu/docs/git-compatibility.md`, `../jujutsu/docs/bookmarks.md`
- Mise: `../mise/references/docs/getting-started.md`, `../mise/references/docs/hooks.md`, `../mise/references/docs/tasks/toml-tasks.md`
