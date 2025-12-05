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

## Full Bulk Redrive Workflow

When performing a bulk redrive (e.g., after a parser bug fix), follow these steps:

### Step 1: Delete Existing Parquet Data

Use the `s3_bulk_delete` tool for fast deletion (~100x faster than `aws s3 rm`):

```bash
cd ~/workplace/platform-tools

# Dry run first to see what would be deleted
python -m platform_tools.s3_bulk_delete --env stage --all-types --dry-run

# Delete all telemetry types
python -m platform_tools.s3_bulk_delete --env stage --all-types

# Or delete specific type only
python -m platform_tools.s3_bulk_delete --env stage --type lock
```

The tool uses DeleteObjects API (1000 objects/batch) with parallelism, achieving ~1000-2000 objects/second vs ~10-20 objects/second with `aws s3 rm --recursive`.

**Environment shortcuts:**
- `--env dev|stage|prod`: Uses predefined bucket and profile
- `--type lock|bridge|video_doorbell`: Delete specific type
- `--all-types`: Delete all three types
- `--workers N`: Parallel workers (default: 8)

### Step 2: Run MSCK REPAIR TABLE (After Deletion)

Sync Glue partitions to reflect the deletions:

```bash
# Lock table
aws --profile platform-stage --region us-west-2 athena start-query-execution \
  --work-group "stage-tps-telemetry-human-wg" \
  --query-execution-context Catalog=AwsDataCatalog,Database=telemetry-parser-db \
  --query-string "MSCK REPAIR TABLE telemetry_lock_flat"

# Bridge table
aws --profile platform-stage --region us-west-2 athena start-query-execution \
  --work-group "stage-tps-telemetry-human-wg" \
  --query-execution-context Catalog=AwsDataCatalog,Database=telemetry-parser-db \
  --query-string "MSCK REPAIR TABLE telemetry_bridge_flat"

# Video doorbell table
aws --profile platform-stage --region us-west-2 athena start-query-execution \
  --work-group "stage-tps-telemetry-human-wg" \
  --query-execution-context Catalog=AwsDataCatalog,Database=telemetry-parser-db \
  --query-string "MSCK REPAIR TABLE telemetry_video_doorbell_flat"
```

### Step 3: Verify Queue is Empty

```bash
aws --profile platform-stage --region us-west-2 sqs get-queue-attributes \
  --queue-url https://sqs.us-west-2.amazonaws.com/339713005884/telemetry-processing-redrive-queue \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

### Step 4: Run the Redrive

```bash
cd ~/workplace/platform-tools

# Redrive each day with queue monitoring
for day in 28 29 30; do
  echo "Redriving Nov $day..."
  AWS_PROFILE=platform-stage go run ./cmd/telemetry-redrive \
    --env stage \
    --s3-prefix "s3://stage-signal-data-lake-raw/raw/json_telemetry/year=2025/month=11/day=$day/" \
    --no-assume-role \
    --monitor --max-queue-visible 500
done
```

The `--monitor --max-queue-visible 500` flags pause sending when queue depth exceeds 500, preventing Lambda throttling.

### Step 5: Wait for Processing to Complete

**IMPORTANT**: After redrive finishes, wait for queue to stay at 0 for **1-2 minutes** before verification. Lambda may have in-flight invocations.

```bash
# Monitor until both values stay at 0
watch -n 10 'aws --profile platform-stage --region us-west-2 sqs get-queue-attributes \
  --queue-url https://sqs.us-west-2.amazonaws.com/339713005884/telemetry-processing-redrive-queue \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --query "Attributes" --output table'
```

Also check DLQ for errors:

```bash
aws --profile platform-stage --region us-west-2 sqs get-queue-attributes \
  --queue-url https://sqs.us-west-2.amazonaws.com/339713005884/telemetry-processing-redrive-queue-dlq \
  --attribute-names ApproximateNumberOfMessages
```

### Step 6: Run MSCK REPAIR TABLE (After Redrive)

**CRITICAL**: Run MSCK REPAIR again after Lambda writes new Parquet files. Athena will show 0 rows until this is done!

```bash
# Same commands as Step 2 - run for all three tables
aws --profile platform-stage --region us-west-2 athena start-query-execution \
  --work-group "stage-tps-telemetry-human-wg" \
  --query-execution-context Catalog=AwsDataCatalog,Database=telemetry-parser-db \
  --query-string "MSCK REPAIR TABLE telemetry_lock_flat"

# ... repeat for bridge and video_doorbell
```

### Step 7: Verify Results

Use `telemetry_verify` with Athena backend (recommended for stage/prod):

```bash
cd ~/workplace/platform-tools

# Check for at-least-once duplicates (the bug we're fixing)
uv run python -m platform_tools.telemetry_verify \
  --env stage --date 2025-11-28 --all-tables --use-athena --check-duplicates -v

# Standard verification (Parquet vs Postgres counts)
uv run python -m platform_tools.telemetry_verify \
  --env stage --date 2025-11-28 --all-tables --use-athena -v

# Assertion data quality check
uv run python -m platform_tools.telemetry_verify \
  --env stage --date 2025-11-28 --use-athena --check-assertion-quality -v
```

**Expected results after successful redrive:**
- 0 at-least-once duplicates (same event_id appearing multiple times)
- Parquet unique counts = Postgres counts
- Fan-out duplicates (different ordinals, same batch) are expected and OK

## Environment-Specific Resources

| Env | Account | Verified Bucket | Workgroup |
|-----|---------|-----------------|-----------|
| dev | 905418337205 | `dev-verified-parquet-v2-df1e4600` | `dev-tps-telemetry-human-wg` |
| stage | 339713005884 | `stage-verified-parquet-v2-c2408546` | `stage-tps-telemetry-human-wg` |
| prod | 891377356712 | `prod-verified-parquet-v2-8b99b916` | `prod-tps-telemetry-signals_e2e-wg` |
