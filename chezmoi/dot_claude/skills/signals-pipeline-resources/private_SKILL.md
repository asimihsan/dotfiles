---
name: signals-pipeline-resources
description: |
  Reference for signals pipeline AWS resources and query routing across dev/stage/prod. Use when working with telemetry S3/SQS/Firehose/Lambda/Glue/Athena resources, choosing between near-real-time flat telemetry and dbt compacted tables, validating active compaction targets from GitHub Actions, or planning compaction table deprecation/cleanup.
---

# Signals Pipeline Resources

## Query Routing
Choose query surface by intent.

1) Use near-real-time verified telemetry when debugging parser/ingestion behavior.
- Database: `telemetry-parser-db`
- Tables: `telemetry_lock_flat`, `telemetry_bridge_flat`, `telemetry_video_doorbell_flat`, `telemetry_otlp_logs_flat`
- Always include partition predicates: `day` and `hour`.

2) Use compacted telemetry for deduped analytics.
- Databases: `telemetry_alerts_dev`, `telemetry_alerts_stage`, `telemetry_alerts_prod`
- Current default compacted surfaces:
  - lock: `int_lock_compacted_daily_kind`
  - bridge: `int_bridge_compacted_daily_kind`
  - video_doorbell: `int_video_doorbell_compacted_daily_kind`
  - otlp_logs: `int_otlp_logs_compacted_daily_v2`

3) Use lock serving view for identity-sensitive/user-facing lock analysis.
- Default: `int_lock_compacted_daily_kind_serving`
- Use base compacted lock table only for low-level/debug analysis.

4) Do not assume `*_compacted_daily` is stale.
- These tables are still active in some scheduled flows unless deprecation gates are met.

## Status Snapshot (Verified 2026-02-26)
Treat this as current only until revalidated.

| Dataset | Surface | Status | Evidence |
| --- | --- | --- | --- |
| lock | `int_lock_compacted_daily_kind` | active-default | GHA run `22461464355` (compaction requests) |
| lock | `int_lock_compacted_daily` | active-dual-write | scheduled backlog workflow references + run `22436101426` |
| lock | `int_lock_compacted_daily_kind_serving` | active-default (serving) | downstream refs in dbt models |
| bridge | `int_bridge_compacted_daily_kind` | active-default | GHA run `22461464355` |
| bridge | `int_bridge_compacted_daily` | active-dual-write | scheduled backlog workflow references + run `22436101426` |
| video_doorbell | `int_video_doorbell_compacted_daily_kind` | active-default | GHA run `22461464355` |
| video_doorbell | `int_video_doorbell_compacted_daily` | active-dual-write | scheduled backlog workflow references + run `22436101426` |
| otlp_logs | `int_otlp_logs_compacted_daily_v2` | active-default | GHA run `22461690045` |
| otlp_logs | `int_otlp_logs_compacted_daily` | active-dual-write | scheduled backlog workflow still references it |

## Reference Navigation
Open only the reference you need.

- Open `references/dbt-data-surfaces.md` when user asks where data lives, which table to query, or wants SQL templates.
- Open `references/compaction-validation.md` when you need to confirm active compaction targets from workflow/config/run evidence.
- Open `references/deprecation-gates.md` only for cleanup/drop planning.

## Quick Map (Data Flow)
1) API Gateway -> `telemetry-signals-ingester` -> Firehose -> raw S3 (`raw/json_telemetry` or `raw/otlp_logs`)
2) raw S3 -> SQS processing queues -> `telemetry-parser-service` -> verified parquet (`telemetry_flat/...`)
3) verified parquet -> registry queue -> DynamoDB registry + Glue partition lifecycle
4) Athena/Glue -> dbt compacted Iceberg tables in `*-signal-data-lake-dbt/dbt/data`

## Environment Accounts
Region: `us-west-2`

| Environment | Account ID | AWS Profile |
| --- | --- | --- |
| dev | 905418337205 | platform-dev |
| stage | 339713005884 | platform-stage |
| prod | 891377356712 | platform-prod |

## Athena Workgroups
Prefer human workgroup for ad-hoc queries.

- `{env}-tps-telemetry-human-wg`
- `{env}-tps-telemetry-dbt-wg`
- `{env}-tps-telemetry-registry-wg`
- `{env}-tps-telemetry-s3_inventory-wg`

## Core Databases
- `telemetry-parser-db`
- `telemetry_alerts_{env}`
- `telemetry_alerts_{env}_dq_audit`
- `{env}-tps_s3_inventory`

## Minimal Discovery Commands
```bash
# Databases
aws --profile platform-dev --region us-west-2 glue get-databases \
  --query 'DatabaseList[].Name' --output text

# Parser flat tables
aws --profile platform-dev --region us-west-2 glue get-tables \
  --database-name telemetry-parser-db \
  --query 'TableList[].Name' --output text

# Alert/compacted tables (example: prod)
aws --profile platform-prod --region us-west-2 glue get-tables \
  --database-name telemetry_alerts_prod \
  --query 'TableList[].Name' --output text
```
