# Loglens Reference

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
  - tables: `telemetry_otlp_logs_flat`, `int_otlp_logs_compacted_daily`
- **stage**
  - region: `us-west-2`
  - role: `arn:aws:iam::339713005884:role/platform-stage-signals-pipeline-viewer`
  - workgroup: `stage-tps-telemetry-human-wg`
  - databases: `telemetry-parser-db`, `telemetry_alerts_stage`
  - tables: `telemetry_otlp_logs_flat`, `int_otlp_logs_compacted_daily`
- **prod**
  - region: `us-west-2`
  - role: `arn:aws:iam::891377356712:role/platform-prod-signals-pipeline-viewer`
  - workgroup: `prod-tps-telemetry-human-wg`
  - databases: `telemetry-parser-db`, `telemetry_alerts_prod`
  - tables: `telemetry_otlp_logs_flat`, `int_otlp_logs_compacted_daily`

Use `--no-assume-role` if you want to rely on ambient credentials (AWS_PROFILE, IMDS, etc.).

## Table notes

- **Compacted table**: de-duplicated hourly rollups.
- **Flat table**: freshest data, not deduped. Column names are more verbose (payload_*/attributes paths).
- Partitioning uses `day` (DATE) and `hour` (string).

## Example commands

```bash
# Compacted + JSON output
loglens logs --env dev --day 2026-01-06 --service push-server --severity error --limit 20 --output json

# Flat table with substring match
loglens logs --env dev --table flat --day 2026-01-06 --hour 23 --contains "error"

# Raw SQL, explicit database
loglens query --env dev --database telemetry_alerts_dev \
  --sql "DESCRIBE int_otlp_logs_compacted_daily" --output json
```
