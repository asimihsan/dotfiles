# DBT Data Surfaces

## Purpose
Use this file to answer: "Where should I query telemetry data?"

- Prefer compacted tables for deduped analytics.
- Prefer serving views when semantics require masking/serving-safe behavior.
- Use flat tables for ingestion/parser debugging and near-real-time checks.

## Environment Mapping
| Environment | Alerts DB |
| --- | --- |
| dev | `telemetry_alerts_dev` |
| stage | `telemetry_alerts_stage` |
| prod | `telemetry_alerts_prod` |

## Surface Matrix (Verified 2026-02-26)
| Dataset | Layer | Table/View | Status | Typical Use |
| --- | --- | --- | --- | --- |
| lock | parser flat | `telemetry-parser-db.telemetry_lock_flat` | active | raw/near-real-time checks |
| lock | compacted | `telemetry_alerts_{env}.int_lock_compacted_daily_kind` | active-default | deduped lock analytics (debug/technical) |
| lock | compacted | `telemetry_alerts_{env}.int_lock_compacted_daily` | active-dual-write | compatibility/migration checks |
| lock | serving | `telemetry_alerts_{env}.int_lock_compacted_daily_kind_serving` | active-default (serving) | identity-sensitive/user-facing lock analysis |
| bridge | parser flat | `telemetry-parser-db.telemetry_bridge_flat` | active | parser/debug checks |
| bridge | compacted | `telemetry_alerts_{env}.int_bridge_compacted_daily_kind` | active-default | deduped bridge analytics |
| bridge | compacted | `telemetry_alerts_{env}.int_bridge_compacted_daily` | active-dual-write | compatibility/migration checks |
| video_doorbell | parser flat | `telemetry-parser-db.telemetry_video_doorbell_flat` | active | parser/debug checks |
| video_doorbell | compacted | `telemetry_alerts_{env}.int_video_doorbell_compacted_daily_kind` | active-default | deduped video doorbell analytics |
| video_doorbell | compacted | `telemetry_alerts_{env}.int_video_doorbell_compacted_daily` | active-dual-write | compatibility/migration checks |
| otlp_logs | parser flat | `telemetry-parser-db.telemetry_otlp_logs_flat` | active | parser/debug checks |
| otlp_logs | compacted | `telemetry_alerts_{env}.int_otlp_logs_compacted_daily_v2` | active-default | deduped logs analytics |
| otlp_logs | compacted | `telemetry_alerts_{env}.int_otlp_logs_compacted_daily` | active-dual-write | compatibility/migration checks |

## Query Templates

### 1) Recent lock telemetry (serving-safe default)
```sql
SELECT *
FROM telemetry_alerts_prod.int_lock_compacted_daily_kind_serving
WHERE event_ts >= date_add('hour', -6, current_timestamp)
ORDER BY event_ts DESC
LIMIT 500;
```

### 2) Recent lock telemetry (base compacted debug)
```sql
SELECT *
FROM telemetry_alerts_prod.int_lock_compacted_daily_kind
WHERE event_ts >= date_add('hour', -6, current_timestamp)
ORDER BY event_ts DESC
LIMIT 500;
```

### 3) Bridge compacted by event kind
```sql
SELECT event_kind, count(*) AS row_count
FROM telemetry_alerts_prod.int_bridge_compacted_daily_kind
WHERE event_ts >= date_add('day', -1, current_timestamp)
GROUP BY 1
ORDER BY 2 DESC;
```

### 4) Video doorbell compacted, recent window
```sql
SELECT *
FROM telemetry_alerts_prod.int_video_doorbell_compacted_daily_kind
WHERE event_ts >= date_add('hour', -24, current_timestamp)
ORDER BY event_ts DESC
LIMIT 500;
```

### 5) OTLP compacted v2, recent window
```sql
SELECT service_name, severity_text, count(*) AS row_count
FROM telemetry_alerts_prod.int_otlp_logs_compacted_daily_v2
WHERE event_ts >= date_add('hour', -2, current_timestamp)
GROUP BY 1, 2
ORDER BY row_count DESC
LIMIT 200;
```

### 6) Flat table near-real-time check (partition pruned)
```sql
SELECT *
FROM telemetry_lock_flat
WHERE day = DATE '2026-02-26'
  AND hour IN ('20', '21', '22')
ORDER BY envelope__timestamp DESC
LIMIT 200;
```

## Selection Rules
- Use flat tables when investigating parser lag, missing partitions, or bad payload mapping.
- Use compacted default tables for deduped analytics and most incident investigation.
- Use lock serving view by default when user-facing identity semantics matter.
- Treat non-kind `*_compacted_daily` as non-default until deprecation gates are completed.
