---
name: aws-cli
description: |
  AWS CLI commands for dev/stage/prod environments. Use when running any aws CLI 
  command, interacting with S3, Lambda, Glue, Athena, CloudWatch, or other AWS 
  services. Ensures correct profile and region are used per environment.
---

# AWS CLI Environment Configuration

## Profiles and Regions

| Environment | Profile | Region |
|-------------|---------|--------|
| dev | platform-dev | us-west-2 |
| stage | platform-stage | us-west-2 |
| prod | platform-prod | us-west-2 |

**Always specify both profile and region explicitly:**

```bash
aws --profile platform-prod --region us-west-2 <service> <command>
```

## Environment Variables Alternative

For repeated commands or scripts:

```bash
export AWS_PROFILE=platform-prod
export AWS_REGION=us-west-2

aws s3 ls s3://my-bucket/
```

Or inline for a single command:

```bash
AWS_PROFILE=platform-prod aws s3 ls s3://my-bucket/
```

## Common Patterns

### S3

```bash
# List bucket contents
aws --profile platform-prod --region us-west-2 \
  s3 ls s3://bucket-name/prefix/ --recursive

# Copy file locally
aws --profile platform-prod --region us-west-2 \
  s3 cp s3://bucket-name/path/to/file.parquet ~/Downloads/

# Sync directory
aws --profile platform-prod --region us-west-2 \
  s3 sync s3://bucket-name/prefix/ ./local-dir/
```

### Lambda

```bash
# List functions
aws --profile platform-prod --region us-west-2 \
  lambda list-functions --query 'Functions[].FunctionName'

# Invoke function
aws --profile platform-prod --region us-west-2 \
  lambda invoke \
    --function-name my-function \
    --payload '{"key": "value"}' \
    response.json

# Get function configuration
aws --profile platform-prod --region us-west-2 \
  lambda get-function-configuration \
    --function-name my-function
```

### CloudWatch Logs

```bash
# List log groups
aws --profile platform-prod --region us-west-2 \
  logs describe-log-groups \
    --log-group-name-prefix /aws/lambda/

# Tail logs (requires aws cli v2)
aws --profile platform-prod --region us-west-2 \
  logs tail /aws/lambda/my-function --follow

# Filter log events
aws --profile platform-prod --region us-west-2 \
  logs filter-log-events \
    --log-group-name /aws/lambda/my-function \
    --start-time $(date -d '1 hour ago' +%s)000 \
    --filter-pattern "ERROR"
```

### Glue

```bash
# List databases
aws --profile platform-prod --region us-west-2 \
  glue get-databases \
    --query 'DatabaseList[].Name' | jq -r '.[]'

# List tables
aws --profile platform-prod --region us-west-2 \
  glue get-tables \
    --database-name my-database \
    --query 'TableList[].Name'

# Get table schema
aws --profile platform-prod --region us-west-2 \
  glue get-table \
    --database-name my-database \
    --name my-table \
    --query 'Table.StorageDescriptor.Columns'
```

### STS (Identity Check)

```bash
# Verify which identity/role you're using
aws --profile platform-prod --region us-west-2 \
  sts get-caller-identity
```

## Output Formatting

### JSON with jq

```bash
# Pretty print
aws ... | jq .

# Extract specific field
aws ... | jq -r '.Field.SubField'

# Filter arrays
aws ... | jq '.Items[] | select(.Status == "ACTIVE")'
```

### Built-in Query

```bash
# Use --query for server-side filtering (faster for large responses)
aws ... --query 'Items[?Status==`ACTIVE`].Name' --output text
```

### Output Formats

```bash
--output json   # Default, parseable
--output text   # Tab-separated, good for shell scripts
--output table  # Human-readable tables
--output yaml   # YAML format
```

## Pagination

For commands that return paginated results:

```bash
# Automatic pagination (default in CLI v2)
aws --profile platform-prod --region us-west-2 \
  s3api list-objects-v2 \
    --bucket my-bucket \
    --prefix my-prefix/ \
    --query 'Contents[].Key'

# Manual pagination
aws ... --max-items 100 --starting-token $NEXT_TOKEN
```

## Debugging

```bash
# Verbose output
aws --debug ...

# Dry run (supported by some commands)
aws ec2 run-instances ... --dry-run
```
