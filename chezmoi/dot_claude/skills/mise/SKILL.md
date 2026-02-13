---
name: mise
description: Use mise to manage tool versions, runtime environments, and task automation for local repositories and CI. Apply this skill when creating or editing `mise.toml` or `.mise.toml`, defining `tasks` or `task_config.includes`, writing environment source scripts with `_.source`, adding `hooks.postinstall` or `hooks.enter`, scaffolding new mise projects, troubleshooting `mise install` or `mise run` failures, or interpreting official mise docs and lockfiles.
---

# Mise

Use this skill to implement and debug mise workflows with repeatable project patterns.

## Execution Flow

1. Identify scope: bootstrap project, edit config, add tasks, add env or hook scripts, or debug.
2. Read `references/workflows.md` for procedural steps and validation commands.
3. Load targeted docs from `references/docs/` for exact mise semantics.
4. Reuse conventions in `references/project-patterns.md` when you need production examples.
5. Reuse templates in `assets/templates/` or run `scripts/new_mise_project.sh`.
6. Validate with `mise install`, `mise tasks`, and `mise run <task>` that exercises the change.

## Grep-First Doc Lookup

`references/docs/` is large. Search first, then open only the needed file.

```bash
rg -n "postinstall|enter|hooks" references/docs
rg -n "task_config|includes|file tasks|toml tasks" references/docs
rg -n "_.source|environment|secrets" references/docs
rg -n "doctor|troubleshooting|debug" references/docs
```

High-value docs for common requests:
- `references/docs/getting-started.md`
- `references/docs/configuration.md`
- `references/docs/hooks.md`
- `references/docs/tasks/index.md`
- `references/docs/tasks/toml-tasks.md`
- `references/docs/tasks/file-tasks.md`
- `references/docs/tasks/task-configuration.md`
- `references/docs/environments/index.md`
- `references/docs/troubleshooting.md`
- `references/docs/cli/doctor/index.md`

## Bundled Resources

- `scripts/new_mise_project.sh`: scaffold a starter mise project from local templates.
- `assets/templates/mise.toml`: baseline config with tools, task includes, env source, and hooks.
- `assets/templates/tasks.core.toml`: starter task file for format, lint, test, and doctor tasks.
- `assets/templates/scripts/env.sh`: sourced environment script template.
- `assets/templates/scripts/postinstall.sh`: post-install hook template.
- `references/project-patterns.md`: distilled conventions from `bixby-rs` and `signals-pipeline-dbt`.
- `references/workflows.md`: implementation playbooks for bootstrap, tasks, hooks, env, and debugging.

## Quality Bar

- Prefer split task files with `task_config.includes` once tasks exceed a small set.
- Keep hooks idempotent and fast.
- Put non-trivial environment logic in a sourced script via `_.source`.
- Add debug toggles in scripts (example: `PROJECT_ENV_DEBUG=1`).
- Avoid storing secrets in `mise.toml`; rely on secret tooling and env providers.
- Keep lockfiles (`mise.lock`) committed for reproducibility when the repository uses them.
