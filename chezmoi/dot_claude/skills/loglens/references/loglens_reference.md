# Loglens Reference

To use loglens, set the working directory to `~/workplace/platform-tools/`. The loglens source code and built binary both live in this repo.

Preferred LLM workflow:
- Use `--output json --out-file <path>` (not shell redirection) so results are captured reproducibly.
- Run `go run ./cmd/loglens --help`, `go run ./cmd/loglens <subcommand> --help`, or `build/loglens --help` to confirm exact flags supported by the current version.

Recommended command pattern:

```bash
cd ~/workplace/platform-tools
AWS_PROFILE=platform-prod AWS_REGION=us-west-2 GOTOOLCHAIN=local \
  /Users/asimi/.local/share/mise/installs/go/1.25.6/bin/go run ./cmd/loglens \
  --no-assume-role --env prod \
  --workgroup prod-tps-telemetry-human-wg \
  --output-location s3://prod-athena-query-results-19303e8d/manual/ \
  query --sql "<SQL>" --limit 0 --output json \
  --out-file ~/workplace/llm/<ticket>/evidence/<date>/loglens/<name>.jsonl
```

## Config loading order

1. `--config /path/to/signals-logs.toml`
2. `SIGNALS_LOGS_CONFIG` env var
3. `./signals-logs.toml`
4. `~/.config/signals-logs/config.toml` (or `$XDG_CONFIG_HOME`)
5. `/etc/signals-logs/config.toml`
6. Embedded defaults

The repo includes a default `signals-logs.toml` with environment mappings.

## Environment mapping (from repo default config)

- **dev**
  - region: `us-west-2`
  - role: `arn:aws:iam::905418337205:role/platform-dev-signals-pipeline-viewer`
  - workgroup: `dev-tps-telemetry-human-wg`
  - databases: `telemetry-parser-db`, `telemetry_alerts_dev`
  - tables: `telemetry_otlp_logs_flat`, `int_otlp_logs_compacted_daily_v2`
- **stage**
  - region: `us-west-2`
  - role: `arn:aws:iam::339713005884:role/platform-stage-signals-pipeline-viewer`
  - workgroup: `stage-tps-telemetry-human-wg`
  - databases: `telemetry-parser-db`, `telemetry_alerts_stage`
  - tables: `telemetry_otlp_logs_flat`, `int_otlp_logs_compacted_daily_v2`
- **prod**
  - region: `us-west-2`
  - role: `arn:aws:iam::891377356712:role/platform-prod-signals-pipeline-viewer`
  - workgroup: `prod-tps-telemetry-human-wg`
  - databases: `telemetry-parser-db`, `telemetry_alerts_prod`
  - tables: `telemetry_otlp_logs_flat`, `int_otlp_logs_compacted_daily_v2`

Use `--no-assume-role` if you want to rely on ambient credentials (AWS_PROFILE, IMDS, etc.).

### Prod note (SSO + human workgroup)

Ensure your profile can assume `prod-tps-signals-human-ro-role` (via the `ReadOnlyAccessSignalsPipeline` permission set).

```bash
AWS_PROFILE=platform-prod AWS_REGION=us-west-2 \
  go run ./cmd/loglens --no-assume-role --env prod \
  --workgroup prod-tps-telemetry-human-wg \
  --output-location s3://prod-athena-query-results-19303e8d/manual/ \
  logs --day 2026-02-03 --service seti-server --severity error --limit 20 --output json
```

## Table notes

- **Compacted table**: de-duplicated hourly rollups.
- **Flat table**: freshest data, not deduped. Column names are more verbose (payload_*/attributes paths).
 - Partitioning uses `day` (DATE) and `hour` (int in compacted tables).

## Example commands

```bash
# Compacted + JSON output
loglens logs --env dev --day 2026-01-06 --service push-server --severity error --limit 20 --output json

# Flat table with substring match
loglens logs --env dev --table flat --day 2026-01-06 --hour 23 --contains "error"

# Raw SQL, explicit database
loglens query --env dev --database telemetry_alerts_dev \
  --sql "DESCRIBE int_otlp_logs_compacted_daily_v2" --output json
```
