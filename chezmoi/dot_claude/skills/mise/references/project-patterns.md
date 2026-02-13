# Project Patterns

This file captures reusable mise patterns observed in two active repositories.

## bixby-rs

Primary files:
- `/Users/asimi/workplace/bixby-rs/mise.toml`
- `/Users/asimi/workplace/bixby-rs/scripts/env.sh`
- `/Users/asimi/workplace/bixby-rs/scripts/setup.sh`

Reusable patterns:
- Keep rich `[tools]` pinning in a single `mise.toml`, including tool-specific backends.
- Use `[env] _.source` for platform-specific logic in a script instead of overloading TOML.
- Keep post-install orchestration in `[hooks].postinstall`, then call project setup commands.
- Add focused mise tasks that call scripts (example: install binary dependencies, setup local storage).
- Add script-level debug switches (`BIXBY_ENV_DEBUG=1`) for environment diagnostics.
- Use explicit comments in `mise.toml` for why environment variables exist.

Apply when:
- You need cross-platform environment setup logic.
- You need post-install setup that prepares local tooling beyond version installs.

## signals-pipeline-dbt

Primary files:
- `/Users/asimi/workplace/signals-pipeline-dbt/mise.toml`
- `/Users/asimi/workplace/signals-pipeline-dbt/tasks.dbt.toml`
- `/Users/asimi/workplace/signals-pipeline-dbt/scripts/fix-mise-awscli.sh`
- `/Users/asimi/workplace/signals-pipeline-dbt/scripts/refresh_device_mapping_seeds.sh`

Reusable patterns:
- Use `[task_config].includes` to split tasks by domain (`lint`, `test`, `dbt`, `ops`, `grafana`).
- Keep tasks declarative with `description`, optional `alias`, `sources`, `outputs`, and `run`.
- Keep `uv run ...` as the consistent execution wrapper for Python and dbt commands.
- Use `[hooks].postinstall` for dependency synchronization and tool-specific fixes.
- Use `[hooks].enter` for lightweight housekeeping commands (cleanup/status refresh).
- Inject environment per command for multi-environment workflows (`AWS_PROFILE=...`).

Apply when:
- Task count is large and domain-oriented grouping improves maintainability.
- Setup requires predictable post-install and on-enter automation.

## Cross-project conventions

1. Keep top-level `mise.toml` as the authoritative entrypoint.
2. Split detail into scripts and task include files.
3. Treat hooks as lifecycle glue, not business logic.
4. Add low-cost debug pathways in scripts and tasks.
5. Keep installation reproducible with explicit versions and lockfiles when used.
