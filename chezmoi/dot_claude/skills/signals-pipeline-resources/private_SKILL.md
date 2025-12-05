---
name: signals-pipeline-resources
description: |
  Reference for signals pipeline AWS resources across dev/stage/prod environments.
  Use when working with telemetry S3 buckets, SQS queues, Athena workgroups, Glue tables,
  or running redrive/verification commands. Includes account IDs, bucket names, queue URLs,
  and common operational commands.
---

# Signals Pipeline Resources

## AWS Accounts

| Environment | AWS Account ID | AWS Profile |
|-------------|---------------|-------------|
| dev | 905418337205 | platform-dev |
| stage | 339713005884 | platform-stage |
| prod | 891377356712 | platform-prod |

**Region:** `us-west-2`

---

## S3 Buckets

### Raw Telemetry (Input)

| Environment | Bucket |
|-------------|--------|
| dev | `dev-signal-data-lake-raw` |
| stage | `stage-signal-data-lake-raw` |
| prod | `prod-signal-data-lake-raw` |

**Path pattern:** `raw/json_telemetry/year=YYYY/month=MM/day=DD/hour=HH/*.gz`

### Verified Parquet (Output)

| Environment | Bucket |
|-------------|--------|
| dev | `dev-verified-parquet-v2-df1e4600` |
| stage | `stage-verified-parquet-v2-c2408546` |
| prod | `prod-verified-parquet-v2-8b99b916` |

**Path pattern:** `telemetry_flat/type={lock,bridge,video_doorbell}/day=YYYY-MM-DD/hour=HH/*.parquet`

---

## SQS Queues

### Telemetry Processing

| Environment | Queue | Purpose |
|-------------|-------|---------|
| dev | `telemetry-processing-queue` | Main processing queue |
| dev | `telemetry-processing-queue_dlq` | Dead letter queue |
| stage | `telemetry-processing-queue` | Main processing queue |
| stage | `telemetry-processing-queue_dlq` | Dead letter queue |
| prod | `telemetry-processing-queue` | Main processing queue |
| prod | `telemetry-processing-queue_dlq` | Dead letter queue |

### Redrive Queue

| Environment | Queue | Purpose |
|-------------|-------|---------|
| dev | `telemetry-processing-redrive-queue` | Redrive S3 files |
| dev | `telemetry-processing-redrive-queue_dlq` | Redrive DLQ |
| stage | `telemetry-processing-redrive-queue` | Redrive S3 files |
| stage | `telemetry-processing-redrive-queue_dlq` | Redrive DLQ |
| prod | `telemetry-processing-redrive-queue` | Redrive S3 files |
| prod | `telemetry-processing-redrive-queue_dlq` | Redrive DLQ |

---

## Athena Configuration

### Workgroups

| Environment | Workgroup | Purpose |
|-------------|-----------|---------|
| dev | `dev-tps-telemetry-human-wg` | Ad-hoc queries |
| dev | `dev-tps-telemetry-dbt-wg` | DBT model queries |
| stage | `stage-tps-telemetry-human-wg` | Ad-hoc queries |
| stage | `stage-tps-telemetry-dbt-wg` | DBT model queries |
| prod | `prod-tps-telemetry-signals_e2e-wg` | Ad-hoc queries |
| prod | `prod-tps-telemetry-dbt-wg` | DBT model queries |

### Glue Databases

| Database | Description |
|----------|-------------|
| `telemetry-parser-db` | Raw Parquet from telemetry-parser-service |
| `telemetry_alerts_{env}` | DBT-transformed tables from signals-pipeline-dbt |

### Glue Tables (telemetry-parser-db)

| Table | Device Type | Description |
|-------|-------------|-------------|
| `telemetry_lock_flat` | lock | Lock device telemetry |
| `telemetry_bridge_flat` | bridge | Bridge (SETI) telemetry |
| `telemetry_video_doorbell_flat` | video_doorbell | Video doorbell telemetry |

---

## Key Commands

### Check SQS Queue Status

```bash
# Dev
AWS_PROFILE=platform-dev aws sqs get-queue-attributes \
  --queue-url https://sqs.us-west-2.amazonaws.com/905418337205/telemetry-processing-redrive-queue \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible

# Prod
AWS_PROFILE=platform-prod aws sqs get-queue-attributes \
  --queue-url https://sqs.us-west-2.amazonaws.com/891377356712/telemetry-processing-redrive-queue \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

### Redrive Telemetry

```bash
cd ~/workplace/platform-tools

# Redrive specific day
AWS_PROFILE=platform-dev go run ./cmd/telemetry-redrive \
  --env dev \
  --s3-prefix "s3://dev-signal-data-lake-raw/raw/json_telemetry/year=2025/month=12/day=01/" \
  --no-assume-role \
  --monitor --max-queue-visible 500
```

### Delete Parquet Files for Redrive

```bash
# Delete a day's Parquet files before redrive
AWS_PROFILE=platform-dev aws s3 rm \
  s3://dev-verified-parquet-v2-df1e4600/telemetry_flat/type=lock/day=2025-12-01/ \
  --recursive
```

### Verify Telemetry Data

```bash
cd ~/workplace/platform-tools

# Check for at-least-once duplicates
uv run python -m platform_tools.telemetry_verify \
  --env dev --date 2025-12-01 --table bolt_controller_v2 --check-duplicates -v

# Brute-force verification (dev only - small datasets)
uv run python -m platform_tools.telemetry_verify \
  --env dev --date 2025-12-01 --table bolt_controller_v2 --brute-force -v
```

### Query Parquet with DuckDB

```bash
uv run python -c "
from platform_tools.telemetry_verify.duckdb_client import DuckDBClient
from platform_tools.telemetry_verify.config import ENV_CONFIG
import os

os.environ['AWS_PROFILE'] = 'platform-dev'
client = DuckDBClient(ENV_CONFIG['dev'])
result = client.query('''
    SELECT envelope__event_kind, count(*) as cnt
    FROM read_parquet('s3://dev-verified-parquet-v2-df1e4600/telemetry_flat/type=lock/day=2025-12-01/hour=*/*.parquet')
    GROUP BY 1
    ORDER BY 2 DESC
''')
for row in result:
    print(row)
"
```

### Parse Raw Telemetry with bixby-rs

```bash
cd ~/workplace/bixby-rs
cargo run -p bixby-cli -- parse --hex '<telemetry_raw_hex>'
```

---

## Lambda Functions

| Environment | Lambda | Purpose |
|-------------|--------|---------|
| dev | `telemetry-parser-service` | Parses raw telemetry to Parquet |
| stage | `telemetry-parser-service` | Parses raw telemetry to Parquet |
| prod | `telemetry-parser-service` | Parses raw telemetry to Parquet |

---

## Related Repositories

| Repository | Purpose |
|------------|---------|
| `~/workplace/platform-tools` | CLI tools (telemetry-redrive, telemetry-verify) |
| `~/workplace/signals-pipeline-dbt` | DBT models for Athena tables |
| `~/workplace/bixby-rs` | Rust telemetry parser (bixby-cli) |
| `~/workplace/LevelServer` | Houston CLI for Postgres queries |
