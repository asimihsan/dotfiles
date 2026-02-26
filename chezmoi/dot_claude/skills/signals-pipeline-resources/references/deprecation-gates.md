# Deprecation Gates

## Purpose
Use this checklist before labeling compacted tables as stale or dropping them.

## Gate Policy
A table can move from `active-dual-write` to `candidate-deprecation` and then `stale` only when all gates pass.

## Gate 1: No Active Writers For 30 Days
Confirm no workflow/task/script still writes the table.

```bash
cd ~/workplace/signals-pipeline-dbt
rg -n "<TABLE_NAME>|compaction-variant|run_compaction_windows.py" .github/workflows tasks.dbt.toml scripts/compaction
```

Required outcome:
- No writer references for at least 30 days of mainline workflow history.

## Gate 2: No Active Consumers
Confirm no downstream models, views, exports, or services depend on the table.

```bash
cd ~/workplace/signals-pipeline-dbt
rg -n "ref\('<TABLE_NAME>'\)|source\(.*<TABLE_NAME>.*\)|<TABLE_NAME>" models macros scripts
```

Required outcome:
- No critical consumers remain, or all are migrated.

## Gate 3: Successor Parity Checks
Compare row counts and freshness with successor over agreed windows.

Example parity SQL pattern:
```sql
-- Replace names/window as needed.
WITH old_counts AS (
  SELECT date_trunc('day', event_ts) AS d, count(*) AS c
  FROM telemetry_alerts_prod.<OLD_TABLE>
  WHERE event_ts >= date_add('day', -14, current_timestamp)
  GROUP BY 1
),
new_counts AS (
  SELECT date_trunc('day', event_ts) AS d, count(*) AS c
  FROM telemetry_alerts_prod.<NEW_TABLE>
  WHERE event_ts >= date_add('day', -14, current_timestamp)
  GROUP BY 1
)
SELECT coalesce(o.d, n.d) AS d, o.c AS old_c, n.c AS new_c
FROM old_counts o
FULL OUTER JOIN new_counts n ON o.d = n.d
ORDER BY d DESC;
```

Required outcome:
- Differences are explained/accepted by owner.

## Gate 4: Owner Approval
Record approval in ticket/PR/incident notes.

Required outcome:
- Named owner approves transition and drop timeline.

## Gate 5: Rollback Plan
Define explicit rollback path before delete.

Include:
- How to re-enable writer workflow references quickly.
- How to restore table metadata/data if needed.
- Who executes rollback and expected SLA.

## Execution Order For Cleanup
1. Mark table `candidate-deprecation`.
2. Monitor for 1 full release window.
3. Remove writer references.
4. Re-run parity checks.
5. Drop table and cleanup paths only after approval.
6. Update `signals-pipeline-resources` status snapshot date and evidence.

## Guardrail
Do not drop compacted tables solely because a newer variant exists.
