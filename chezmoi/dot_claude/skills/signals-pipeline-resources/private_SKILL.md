---
name: signals-pipeline-resources
description: |
  Reference for signals pipeline AWS resources, architecture, and debugging workflows across dev/stage/prod. Use when working with telemetry S3 buckets, SQS queues, Firehose, Lambda, Glue/Athena, registry/DynamoDB, CloudWatch dashboards, or running redrive/verification commands.
---

# Signals Pipeline Resources

## Quick map (data flow)
1) API Gateway -> telemetry-signals-ingester -> Firehose -> raw S3 (raw/json_telemetry or raw/otlp_logs)
2) raw S3 -> SQS processing queues -> telemetry-parser-service -> verified parquet (telemetry_flat/...)
3) verified S3 -> telemetry-registry-queue -> DynamoDB registry + Glue partitions (EventBridge reconciler)
4) Athena/Glue -> dbt Iceberg tables in *-signal-data-lake-dbt/dbt/data

## AWS accounts and profiles

| Environment | Account ID   | AWS Profile    |
| ----------- | ------------ | -------------- |
| dev         | 905418337205 | platform-dev   |
| stage       | 339713005884 | platform-stage |
| prod        | 891377356712 | platform-prod  |

Region: us-west-2

## S3 buckets (current as of 2026-01-26; verify if recreated)

### Data lake + verified
| Environment | Raw bucket                 | Verified parquet v2                | Parquet output (simple)     | Quarantine                                      |
| ----------- | -------------------------- | ---------------------------------- | --------------------------- | ----------------------------------------------- |
| dev         | dev-signal-data-lake-raw   | dev-verified-parquet-v2-df1e4600   | dev-parquet-output-simple   | dev-parquet-output-simple-quarantine-7c0d2f9a   |
| stage       | stage-signal-data-lake-raw | stage-verified-parquet-v2-c2408546 | stage-parquet-output-simple | stage-parquet-output-simple-quarantine-4b6e13c2 |
| prod        | prod-signal-data-lake-raw  | prod-verified-parquet-v2-8b99b916  | prod-parquet-output-simple  | prod-parquet-output-simple-quarantine-9f2a7d31  |

### dbt + Athena
| Environment | dbt data bucket            | dbt artifacts bucket         | Athena query results                |
| ----------- | -------------------------- | ---------------------------- | ----------------------------------- |
| dev         | dev-signal-data-lake-dbt   | dev-dbt-artifacts-8f5c3a12   | dev-athena-query-results-19303e8d   |
| stage       | stage-signal-data-lake-dbt | stage-dbt-artifacts-7bd8f1a4 | stage-athena-query-results-19303e8d |
| prod        | prod-signal-data-lake-dbt  | prod-dbt-artifacts-5c9b02de  | prod-athena-query-results-19303e8d  |

### S3 inventory bucket (random suffix; discover dynamically)
| Environment | Bucket                          |
| ----------- | ------------------------------- |
| dev         | dev-tps-s3-inventory-5fa82ae0   |
| stage       | stage-tps-s3-inventory-192d6b30 |
| prod        | prod-tps-s3-inventory-cd0b7a86  |

Discovery command (prefix search):
```bash
aws --profile platform-dev --region us-west-2 s3api list-buckets \
  --query 'Buckets[?contains(Name, `tps-s3-inventory`)].Name' --output text
```

### Prefixes and layouts
- Raw JSON telemetry: raw/json_telemetry/... (partitioned by date/hour)
- Raw OTLP logs: raw/otlp_logs/... (partitioned by date/hour)
- Verified parquet: telemetry_flat/type={lock,bridge,video_doorbell,otlp_logs}/day=YYYY-MM-DD/hour=HH/*.parquet
- dbt staging: dbt/staging/
- dbt data (Iceberg): dbt/data/...
- dbt exports: dbt/exports/
- dbt temp: dbt/temp/

## SQS queues

### Processing
- telemetry-processing-queue (+ _dlq)
- telemetry-processing-redrive-queue (+ _dlq)
- telemetry-registry-queue (+ _dlq)
- otlp-logs-processing-queue (+ _dlq)

Discovery:
```bash
aws --profile platform-dev --region us-west-2 sqs list-queues --queue-name-prefix telemetry
aws --profile platform-dev --region us-west-2 sqs list-queues --queue-name-prefix otlp
```

## Firehose delivery streams
- telemetry-signals-lake-firehose (json_telemetry)
- otlp-logs-firehose

Discovery:
```bash
aws --profile platform-dev --region us-west-2 firehose list-delivery-streams
```

## Lambda functions
- telemetry-parser-service
- telemetry-signals-ingester

Discovery:
```bash
aws --profile platform-dev --region us-west-2 \
  lambda list-functions --query 'Functions[?starts_with(FunctionName, `telemetry-`)].FunctionName' --output text
```

## API Gateway + domains
- API: telemetry-signals-ingester-api
- Domains:
  - dev: signals-pipeline-ingest.dev-public.level.co
  - stage: signals-pipeline-ingest.stage-public.level.co
  - prod: signals-pipeline-ingest.prod-public.level.co

## DynamoDB registry table
- {env}-tps-telemetry-file-registry-v2

Discovery:
```bash
aws --profile platform-dev --region us-west-2 dynamodb list-tables \
  --query 'TableNames[?contains(@, `telemetry-file-registry`)]' --output text
```

## EventBridge reconciler
- {env}-tps-telemetry-registry-reconciler (cron 0/15 * * * ? *)

Discovery:
```bash
aws --profile platform-dev --region us-west-2 events list-rules --name-prefix dev-tps-telemetry-registry
```

## Athena workgroups
- {env}-tps-telemetry-human-wg (ad-hoc)
- {env}-tps-telemetry-dbt-wg (dbt writes; overrides disabled)
- {env}-tps-telemetry-signals_e2e-wg (human verification)
- {env}-tps-telemetry-registry-wg (registry maintenance)
- {env}-tps-telemetry-s3_inventory-wg (inventory/debug)

Discovery:
```bash
aws --profile platform-dev --region us-west-2 athena list-work-groups \
  --query 'WorkGroups[?contains(Name, `tps-telemetry`)].Name' --output text
```

## Glue catalog

Databases:
- telemetry-parser-db
- telemetry_alerts_{env}
- telemetry_alerts_{env}_dq_audit
- {env}-tps_s3_inventory

Tables in telemetry-parser-db (this is a Hive table where "verified" data is stored, first place where JSONL GZIP data is converted to Parquet):
- telemetry_lock_flat
- telemetry_bridge_flat
- telemetry_video_doorbell_flat
- telemetry_otlp_logs_flat

"Compacted" tables in telemetry_alerts_{env} (this is where verified data is de-duplicated and stored in Iceberg table):
- int_lock_compacted_daily
- int_bridge_compacted_daily
- int_video_doorbell_compacted_daily
- int_otlp_logs_compacted_daily

Discovery:
```bash
aws --profile platform-dev --region us-west-2 glue get-databases \
  --query 'DatabaseList[?contains(Name, `telemetry`)].Name' --output text
aws --profile platform-dev --region us-west-2 glue get-tables \
  --database-name telemetry-parser-db --query 'TableList[].Name' --output text
```

## CloudWatch dashboards
- telemetry-app-metrics
- telemetry-parser-metrics

Discovery:
```bash
aws --profile platform-dev --region us-west-2 cloudwatch list-dashboards --dashboard-name-prefix telemetry
```

## Debug playbook (fast checks)
1) Firehose -> raw S3
   - Check Firehose delivery metrics (AWS/Firehose) and list raw S3 prefix.
2) Raw S3 -> processing queue
   - Check SQS ApproximateAgeOfOldestMessage and DLQ counts.
3) Parser Lambda
   - Inspect /aws/lambda/telemetry-parser-service logs and telemetry-app-metrics dashboard.
4) Verified parquet
   - List telemetry_flat/... prefix for expected day/hour.
5) Registry
   - Check telemetry-registry-queue age + DDB table for failed partitions.
6) Glue/Athena
   - Ensure Glue table location matches verified prefix and run a partition-filtered query.
7) dbt layer
   - Use $github-actions-runs skill to look at GHA runs in `LevelHome/signals-pipeline-dbt` repo, this is where e.g. compaction is run regularly.
   - Check dbt run artifacts in dbt artifacts bucket and Iceberg tables in telemetry_alerts_{env}.

## Key commands

Check SQS queue health:
```bash
AWS_PROFILE=platform-dev aws sqs get-queue-attributes \
  --queue-url https://sqs.us-west-2.amazonaws.com/905418337205/telemetry-processing-queue \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible ApproximateAgeOfOldestMessage
```

List recent raw objects:
```bash
AWS_PROFILE=platform-dev aws s3 ls \
  s3://dev-signal-data-lake-raw/raw/json_telemetry/ --recursive | head
```

Athena quick sanity (SHOW TABLES):
```bash
aws --profile platform-dev --region us-west-2 athena start-query-execution \
  --work-group dev-tps-telemetry-human-wg \
  --query-execution-context Catalog=AwsDataCatalog,Database=telemetry-parser-db \
  --query-string "SHOW TABLES"
```

Glue table location:
```bash
aws --profile platform-dev --region us-west-2 glue get-table \
  --database-name telemetry-parser-db \
  --name telemetry_lock_flat \
  --query 'Table.StorageDescriptor.Location' --output text
```

Registry DDB count (rough):
```bash
aws --profile platform-dev --region us-west-2 dynamodb scan \
  --table-name dev-tps-telemetry-file-registry-v2 --select COUNT
```

## Related repositories
- ~/workplace/telemetry-parser-service-iac (Terraform infra)
- ~/workplace/telemetry-parser-service (parser + registry Lambda)
- ~/workplace/signals-pipeline-dbt (dbt models / Iceberg maintenance)
- ~/workplace/signals-pipeline-ingester (ingest app)
- ~/workplace/platform-tools (telemetry-redrive, telemetry-verify)
- ~/workplace/bixby-rs (telemetry schema / parquet FFI)
- ~/workplace/llm/signals-pipeline/*.md (architecture + investigation notes)
