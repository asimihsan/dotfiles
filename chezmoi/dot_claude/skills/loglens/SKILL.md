---
name: loglens
description: Query signals pipeline OTLP logs via the loglens Athena-backed CLI. Use when you need to search or inspect signals logs, run opinionated filters (logs/top-errors/schema), or execute raw SQL against the compacted or flat log tables in dev/stage/prod. Triggers include requests mentioning loglens, signals logs, OTLP logs, telemetry alerts, push-server logs, or Athena log queries.
---

# Loglens

## Quick start

- Ensure AWS credentials for the target environment. If you are using AWS_PROFILE/SSO credentials directly, add `--no-assume-role`.
- Run from repo: `go run ./cmd/loglens ...` (or use `build/loglens` if already built).
- Confirm environments: `loglens envs`.
- Run a bounded query (required): `--day`/`--hour` or `--since`/`--until`.
- Prod note: if `AWS_PROFILE=platform-prod` resolves to `prod-tps-signals-e2e-audit-role`, you must add `--no-assume-role` and override `--workgroup` + `--output-location` to the signals-e2e workgroup (see example below). The default `platform-prod-signals-pipeline-viewer` assume role + `prod-tps-telemetry-human-wg` will fail with `AccessDenied` for that profile.

Example:

```bash
AWS_PROFILE=platform-dev AWS_REGION=us-west-2 \
  go run ./cmd/loglens --no-assume-role --env dev logs \
  --day 2026-01-06 --service push-server --severity error --limit 20 --output json
```

Prod example (signals-e2e workgroup):

```bash
AWS_PROFILE=platform-prod AWS_REGION=us-west-2 \
  go run ./cmd/loglens --no-assume-role --env prod \
  --workgroup prod-tps-telemetry-signals_e2e-wg \
  --output-location s3://prod-athena-query-results-19303e8d/signals-e2e/ \
  logs --day 2026-02-03 --service seti-server --severity error --limit 20 --output json
```

## Core workflows

### 1) Opinionated log search (default compacted)

- `loglens logs` targets the **compacted + deduped** table by default.
- Always include a time filter to avoid full scans.
- Use `--service`, `--severity`, `--contains`, and repeatable `--filter` for column/JSON predicates.
- Add `--columns` or `--include-attributes` to inspect specific fields.
- Use `--table flat` for freshest (non-deduped) data in the raw table.

Examples:

```bash
# Compacted (deduped) logs
loglens logs --env dev --day 2026-01-06 --service push-server --severity error --limit 50

# Fresh logs from the flat table
loglens logs --env dev --table flat --day 2026-01-06 --hour 23 --contains "error"

# JSON attribute filter
loglens logs --env dev --day 2026-01-06 --service push-server \
  --filter "attributes.app_id IS NOT NULL"
```

### 2) Raw SQL

Use `loglens query` for schema inspection or complex SQL. Prefer explicit databases if needed.

```bash
loglens query --env dev \
  --sql "SELECT event_ts, service_name, severity, body FROM telemetry_alerts_dev.int_otlp_logs_compacted_daily WHERE day=DATE '2026-01-06' AND hour=23 LIMIT 20" \
  --output json
```

### 3) Top errors

```bash
loglens top-errors --env stage --day 2026-01-06 --limit 20 --trace-samples 2 --output json
```

### 4) Schema discovery

```bash
loglens schema --env dev --table compacted
loglens schema --env dev --table flat
```

## Data sources and Athena alternative

- Loglens queries **AWS Glue tables via Athena**.
- Tables:
  - `telemetry-parser-db.telemetry_otlp_logs_flat` (fresh, not deduped)
  - `telemetry_alerts_{env}.int_otlp_logs_compacted_daily` (compacted + deduped)
- If you need direct Athena access or Glue catalog exploration, use the `$athena-queries` skill as an alternative.
- Prod has data; always include `day`/`hour` predicates and prefer the signals-e2e workgroup if using the `platform-prod` profile.

## References

See `references/loglens_reference.md` for configuration details, environment mappings, and additional examples.
