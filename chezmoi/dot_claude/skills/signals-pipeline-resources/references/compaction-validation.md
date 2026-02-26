# Compaction Validation

## Purpose
Use this file to validate which compacted tables are actively written now.

## Quick Procedure
1. Confirm workflow config intent.
2. Confirm runtime behavior from recent GitHub Actions runs.
3. Confirm model mapping in repo compaction config.
4. Confirm table presence in Glue/Athena catalog.

## 1) Workflow Config Intent
Run in `~/workplace/signals-pipeline-dbt`.

```bash
rg -n "compaction-variant|run_compaction_windows.py|int_.*compacted" .github/workflows
```

Expectations (as of 2026-02-26):
- `dbt-compaction-requests.yml` uses `--compaction-variant daily_kind`.
- `dbt-compaction-requests-otlp.yml` uses `--compaction-variant daily_kind`.
- `dbt-schedule-daily.yml` still references both daily and daily_kind model names in backlog jobs.

## 2) Runtime Behavior (GitHub Actions)
Use `github-actions-runs` skill workflow.

```bash
gh-actions-runs --help
gh-actions-runs list --repo LevelHome/signals-pipeline-dbt --limit 20 --format json
gh-actions-runs jobs 22461464355 --repo LevelHome/signals-pipeline-dbt --format json
gh-actions-runs jobs 22461690045 --repo LevelHome/signals-pipeline-dbt --format json
```

Download and inspect logs:

```bash
mkdir -p /tmp/gha-signals
gh-actions-runs logs 22461464355 --repo LevelHome/signals-pipeline-dbt --output /tmp/gha-signals --format json
gh-actions-runs logs 22461690045 --repo LevelHome/signals-pipeline-dbt --output /tmp/gha-signals --format json

rg -n "compaction_variant|=== Running int_|START sql incremental model telemetry_alerts_.*int_.*compacted" \
  /tmp/gha-signals/run-22461464355/logs \
  /tmp/gha-signals/run-22461690045/logs
```

Expected observations (2026-02-26):
- request sweeps run `int_lock_compacted_daily_kind`, `int_bridge_compacted_daily_kind`, `int_video_doorbell_compacted_daily_kind`.
- OTLP request sweeps run `int_otlp_logs_compacted_daily_v2`.

## 3) Repo Model Mapping
Check compaction dataset mapping:

```bash
sed -n '1,220p' scripts/compaction/config.py
```

Interpretation rules:
- If dataset tuple has both daily and daily_kind, variant controls which writes occur.
- If dataset tuple has single target (for example OTLP v2), that model is the active writer target for that runner path.

## 4) Glue Catalog Presence
Use explicit profile and region.

```bash
aws --profile platform-prod --region us-west-2 glue get-tables \
  --database-name telemetry_alerts_prod \
  --query 'TableList[].Name' --output text | tr '\t' '\n' | rg '^int_.*compacted'
```

This confirms table existence, not writer activity.

## Status Decision Rules
Classify table status using all evidence together:
- `active-default`:
  - current workflows write it in routine paths, and
  - team guidance points to it as default query surface.
- `active-dual-write`:
  - workflow/config still writes it, but another surface is preferred.
- `candidate-deprecation`:
  - no current writer references in workflows for gate window,
  - successor table validated for parity,
  - no active consumer dependencies.
- `stale`:
  - all deprecation gates passed and owner approved cleanup.
