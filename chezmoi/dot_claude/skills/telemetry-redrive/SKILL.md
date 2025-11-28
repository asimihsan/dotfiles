---
name: telemetry-redrive
description: |
  Redrive telemetry data through the telemetry-parser-service Lambda. Use when
  reprocessing raw JSONL files, fixing corrupted Parquet output, or validating
  parser changes. Supports single file, prefix-based, Parquet-driven, and surgical
  day-based redrives with automatic Parquet deletion.
---

# Telemetry Parser Redrive Tool

Located at `~/workplace/platform-tools/cmd/telemetry-redrive/`

## Environment Configuration

Configuration in `~/workplace/platform-tools/config.toml`:

| Environment | Queue ARN | Raw Bucket |
|-------------|-----------|------------|
| dev | `arn:aws:sqs:us-west-2:905418337205:telemetry-processing-redrive-queue` | `dev-signal-data-lake-raw` |
| stage | `arn:aws:sqs:us-west-2:339713005884:telemetry-processing-redrive-queue` | `stage-signal-data-lake-raw` |
| prod | `arn:aws:sqs:us-west-2:891377356712:telemetry-processing-redrive-queue` | `prod-signal-data-lake-raw` |

## Basic Usage

### Single File Redrive

```bash
# Dry run (recommended first)
go run ./cmd/telemetry-redrive \
  --env stage \
  --s3-uri "s3://stage-signal-data-lake-raw/raw/json_telemetry/year=2025/month=11/day=24/hour=21/telemetry-signals-lake-firehose-1-2025-11-24-21-09-35-xxx.gz" \
  --aws-profile platform-stage \
  --no-assume-role \
  --dry-run

# Actual redrive
go run ./cmd/telemetry-redrive \
  --env stage \
  --s3-uri "s3://stage-signal-data-lake-raw/raw/json_telemetry/year=2025/month=11/day=24/hour=21/telemetry-signals-lake-firehose-1-2025-11-24-21-09-35-xxx.gz" \
  --aws-profile platform-stage \
  --no-assume-role
```

### Prefix-Based Redrive (Multiple Files)

```bash
# Redrive all files for a specific hour
go run ./cmd/telemetry-redrive \
  --env prod \
  --s3-prefix "s3://prod-signal-data-lake-raw/raw/json_telemetry/year=2025/month=11/day=24/hour=21/" \
  --aws-profile platform-prod \
  --no-assume-role \
  --dry-run
```

### Parquet-Driven Redrive

This mode DELETES the Parquet file first, then redrives its source files:

```bash
go run ./cmd/telemetry-redrive \
  --env stage \
  --parquet-uri "s3://stage-verified-parquet-v2-c2408546/telemetry_flat/type=lock/day=2025-11-24/hour=21/lock_2025_11_24_21__h=xxx.parquet" \
  --aws-profile platform-stage \
  --no-assume-role \
  --dry-run
```

### Surgical Day-Based Redrive (Recommended for Bug Fixes)

This mode queries Athena for all source_refs on a day, deletes ALL Parquet files for that day/type, then redrives:

```bash
# Dry run first - see what would be deleted and redriven
go run ./cmd/telemetry-redrive \
  --env stage \
  --source-ref-day 2025-11-24 \
  --type lock \
  --aws-profile platform-stage \
  --no-assume-role \
  --dry-run

# Execute the surgical redrive
go run ./cmd/telemetry-redrive \
  --env stage \
  --source-ref-day 2025-11-24 \
  --type lock \
  --aws-profile platform-stage \
  --no-assume-role
```

**Best for:** Fixing parser bugs where all data for a day needs reprocessing. Automatically:
1. Queries Athena for unique source_refs on that day
2. Finds and deletes all Parquet files for that day/type
3. Sends redrive messages for each source_ref

**Note:** The `--type` flag filters the S3 path (e.g., `telemetry_flat/type=lock/day=...`), not the Athena query. The table (e.g., `telemetry_lock_flat`) is already type-specific.

## Key Flags

| Flag | Description |
|------|-------------|
| `--env` | Environment: `dev`, `stage`, `prod` |
| `--s3-uri` | Single raw JSONL file to redrive |
| `--s3-prefix` | Prefix to recursively redrive all files under |
| `--parquet-uri` | Verified Parquet file; extracts source_ref URIs and redrives each |
| `--source-ref-day` | Surgical mode: Query Athena for source_refs on this day (YYYY-MM-DD) |
| `--type` | Filter by type tag for surgical mode (e.g., `lock`, `bridge`) |
| `--delete-parquet` | Delete Parquet files before redriving (default: true) |
| `--dry-run` | Print payload without sending to SQS |
| `--aws-profile` | AWS profile to use |
| `--no-assume-role` | Skip role assumption, use profile credentials directly |
| `--json` | Emit machine-readable JSON output |
| `--limit` | Limit number of messages (sanity check mode) |
| `--monitor` | Enable SQS queue monitoring - pause when queue is full |

## Critical Considerations

### Duplicate Data Warning

**Redriving raw files WITHOUT deleting old Parquet first creates duplicates!**

The Lambda will produce new Parquet files, but old files remain. DBT compaction will see duplicates for the same `event_id`.

**Recommended workflow for fix verification:**
1. Use `--parquet-uri` mode which auto-deletes old Parquet
2. Or manually delete old Parquet files before raw file redrive
3. Or query with `$path` filter to isolate new vs old files

### Fan-Out Pattern

One raw JSONL file produces multiple Parquet files across different:
- Event time partitions (day/hour)
- Type tags (lock, bridge, etc.)

When redriving to fix a bug, all output Parquet files from the original processing should be deleted.

### Verifying Redrive Success

After redrive, verify with Athena:

```sql
-- Check event distribution for a source file
SELECT
    envelope__event_kind,
    payload__assertion__component_name IS NOT NULL as has_assertion_payload,
    COUNT(*) as cnt
FROM telemetry_lock_flat
WHERE envelope__source_ref = 's3://...'
GROUP BY 1, 2
ORDER BY cnt DESC
```

### Lambda Version

Ensure the Lambda is running the correct version before redriving:

```bash
# Check current Lambda version
aws --profile platform-stage --region us-west-2 \
  lambda list-aliases --function-name telemetry-parser-service

# Update alias to new version if needed
aws --profile platform-stage --region us-west-2 \
  lambda update-alias \
    --function-name telemetry-parser-service \
    --name live \
    --function-version 13
```

## SQS Message Format

The tool sends messages with this payload structure:

```json
{
  "kind": "redrive_raw_file",
  "bucket": "stage-signal-data-lake-raw",
  "key": "raw/json_telemetry/year=2025/month=11/day=24/hour=21/telemetry-signals-lake-firehose-1-xxx.gz"
}
```

## IAM Requirements

The role/profile must have:
- `s3:GetObject` on raw bucket
- `s3:DeleteObject` on verified Parquet bucket (for `--parquet-uri` mode)
- `s3:ListBucket` on raw bucket (for `--s3-prefix` mode)
- `sqs:SendMessage` on the redrive queue
