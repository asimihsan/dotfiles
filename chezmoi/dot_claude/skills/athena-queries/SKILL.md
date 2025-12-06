---
name: athena-queries
description: |
  Run AWS Athena queries against telemetry data. Use when executing SQL against 
  telemetry-parser-db (raw Parquet from telemetry-parser-service) or telemetry_alerts 
  (DBT-transformed tables). Also for Glue catalog exploration, partition debugging, 
  or filtering by $path pseudo-column.
---

# AWS Athena Query Patterns

## Environment Configuration

| Environment | AWS Profile | Workgroup Pattern | DBT Target |
|-------------|-------------|-------------------|------------|
| dev | platform-dev | dev-tps-telemetry-{purpose}-wg | athena_dev |
| stage | platform-stage | stage-tps-telemetry-{purpose}-wg | athena_stage |
| prod | platform-prod | prod-tps-telemetry-{purpose}-wg | athena_prod |

**Region:** `us-west-2`

**Workgroup purposes:**
- `signals_e2e-wg` - General queries, signals end-to-end
- `dbt-wg` - DBT model queries

## Glue Databases

| Database | Description |
|----------|-------------|
| `telemetry-parser-db` | Raw Parquet from telemetry-parser-service (verified S3 data) |
| `telemetry_alerts_{env}` | DBT-transformed tables from signals-pipeline-dbt |

## Glue Catalog Exploration

```bash
# List all databases
aws --profile platform-prod --region us-west-2 \
  glue get-databases \
  --query 'DatabaseList[].Name' | jq -r

# List tables in a database
aws --profile platform-prod --region us-west-2 \
  glue get-tables \
    --database-name telemetry-parser-db \
  | jq '.TableList[].Name'

# Get table details (location, format, columns)
aws --profile platform-prod --region us-west-2 \
  glue get-table \
    --database-name telemetry-parser-db \
    --name telemetry_lock_flat \
    --query 'Table.StorageDescriptor.{Location:Location,InputFormat:InputFormat,OutputFormat:OutputFormat,SerdeInfo:SerdeInfo.Name,Columns:Columns}' \
  | jq .
```

## Query Execution Workflow

### 1. Start Query

```bash
QUERY_EXECUTION_ID=$(
  aws --profile platform-prod --region us-west-2 athena start-query-execution \
    --work-group "prod-tps-telemetry-signals_e2e-wg" \
    --query-execution-context Catalog=AwsDataCatalog,Database=telemetry-parser-db \
    --query-string "SELECT * FROM telemetry_lock_flat
                    WHERE day=DATE '2025-11-09'
                      AND hour='02'
                    LIMIT 10" \
  | jq -r '.QueryExecutionId'
)
echo "$QUERY_EXECUTION_ID"
```

### 2. Poll for Completion

```bash
QUERY_STATUS="RUNNING"
while [ "$QUERY_STATUS" != "SUCCEEDED" ]; do
  QUERY_STATUS=$(aws --profile platform-prod --region us-west-2 \
    athena get-query-execution \
    --query-execution-id $QUERY_EXECUTION_ID | jq -r '.QueryExecution.Status.State')
  echo "$QUERY_STATUS"

  if [ "$QUERY_STATUS" = "FAILED" ]; then
    echo "Query execution failed:"
    aws --profile platform-prod --region us-west-2 \
      athena get-query-execution \
      --query-execution-id $QUERY_EXECUTION_ID | jq -r '.QueryExecution.Status'
    break
  fi

  sleep 1
done
```

### 3. Download Results

```bash
OUTPUT_LOCATION=$(aws --profile platform-prod --region us-west-2 \
  athena get-query-execution \
  --query-execution-id $QUERY_EXECUTION_ID | jq -r '.QueryExecution.ResultConfiguration.OutputLocation')

aws --profile platform-prod --region us-west-2 \
  s3 cp "$OUTPUT_LOCATION" ~/Downloads/signals-pipeline/
```

## Filtering by Specific Parquet File

Use the `$path` pseudo-column to query specific files. Note shell escaping:

```bash
--query-string "SELECT * FROM telemetry_lock_flat
                WHERE day=DATE '2025-11-09'
                  AND hour='02'
                  AND \"\$path\" LIKE '%lock_2025_11_09_02__h=bdf9fcbe979b.parquet%'
                LIMIT 10"
```

## DBT Commands

Run these in `~/workplace/signals-pipeline-dbt/`.

```bash
# Run specific models with full refresh
AWS_PROFILE=platform-prod uv run dbt run \
  --target athena_prod \
  --full-refresh \
  --select int_bolt_high_current_state int_bolt_high_current_current_run alerts__bolt_high_current

# Reset DBT environment for specific tables
AWS_PROFILE=platform-prod uv run python scripts/reset_dbt_environment.py \
  --only-table int_bolt_high_current_state \
  --only-table int_bolt_high_current_current_run \
  --profile telemetry_athena \
  --target prod
```

## Partition Columns

Tables in `telemetry-parser-db` are partitioned by:
- `day` (DATE type, use `DATE 'YYYY-MM-DD'` syntax)
- `hour` (string format: '00'-'23')

Always include partition predicates to avoid full table scans.

## Troubleshooting

### HIVE_CURSOR_ERROR
Usually indicates Parquet schema issues. Check:
1. Column types match between Parquet files and Glue table definition
2. No corrupt Parquet files in the partition
3. Use `$path` filter to isolate problematic files

### Query Shows QUEUED Forever
Check workgroup concurrent query limits. The signals_e2e workgroup may have lower limits than dbt workgroup.
