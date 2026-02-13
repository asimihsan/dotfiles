# Mise Workflows

## Table of Contents
- Project bootstrap
- Add or refactor tasks
- Add environment scripts
- Add hooks
- Debugging checklist

## Project bootstrap

1. Initialize files from templates.

```bash
./scripts/new_mise_project.sh /path/to/new-project
```

2. Edit `/path/to/new-project/mise.toml`.
- Set concrete tool versions in `[tools]`.
- Keep `task_config.includes` aligned with actual task files.
- Keep `_.source` pointing to a real script path.

3. Install and trust the project.

```bash
cd /path/to/new-project
mise trust
mise install
mise tasks
```

4. Run one lifecycle task.

```bash
mise run doctor
```

5. Commit `mise.toml` and lockfile (`mise.lock`) if generated in your workflow.

## Add or refactor tasks

1. Prefer task file splitting for medium and large projects.

```toml
[task_config]
includes = [
  "tasks.core.toml",
  "tasks.dbt.toml",
  "tasks.ops.toml",
]
```

2. Keep each task explicit.

```toml
[tasks.lint]
description = "Run static checks"
sources = ["src/**/*", "pyproject.toml"]
outputs = [".cache/lint.ok"]
run = ["uv run ruff check .", "touch .cache/lint.ok"]
```

3. Use aliases for frequent commands.

```toml
[tasks.test]
alias = ["t"]
run = ["uv run pytest -q"]
```

4. Re-validate discovery and execution.

```bash
mise tasks
mise run lint
mise run test
```

## Add environment scripts

1. Move complex environment logic out of `mise.toml` and into `scripts/env.sh`.
2. Source it with `_.source`.

```toml
[env]
_.source = "{{ config_root }}/scripts/env.sh"
```

3. Keep the script idempotent and gated by debug flags.
- Use a debug variable such as `PROJECT_ENV_DEBUG=1`.
- Avoid failing when optional system dependencies are missing.
- Do not hardcode secrets.

4. Validate in shell and in task execution.

```bash
PROJECT_ENV_DEBUG=1 mise run doctor
mise x -- env | rg "PROJECT_ROOT|PATH"
```

## Add hooks

1. Keep hooks fast and repeatable.
2. Put non-trivial hook logic in scripts.

```toml
[hooks]
postinstall = [
  "./scripts/postinstall.sh",
]
enter = [
  "mise run doctor || true",
]
```

3. Use hooks for setup actions, not long-running workloads.
4. Re-run install to verify behavior.

```bash
mise install
```

## Debugging checklist

1. Run built-in diagnostics.

```bash
mise doctor
mise tasks
```

2. Isolate execution context.

```bash
mise x -- which python
mise x -- env | rg "MISE|PATH"
```

3. Validate hook scripts directly.

```bash
bash -x scripts/postinstall.sh
```

4. Validate sourced env script behavior with debug enabled.

```bash
PROJECT_ENV_DEBUG=1 mise run doctor
```

5. Inspect task file includes and naming.
- Confirm every include file exists.
- Confirm task names in `mise run <name>` match declaration names.

6. Confirm permission and trust issues.

```bash
mise trust
ls -l scripts
```

7. Use official docs for exact CLI and config behavior.
- Start at `references/docs/tasks/index.md` for task behavior.
- Start at `references/docs/hooks.md` for lifecycle hooks.
- Start at `references/docs/troubleshooting.md` for failures and known caveats.
