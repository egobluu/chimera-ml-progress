# Candidate Runtime Dataset Merge

## Summary

| Item | Count |
| --- | ---: |
| Base rows | 67 |
| Added train-ready rows | 14 |
| Output rows | 81 |
| Output columns | 124 |

## Label Counts

```json
{
  "0": 46,
  "1": 35
}
```

## Input

- Base dataset: `reports\evaluations\ranker-schema-backfill-redis-grafana-v01\target-exploitability-family-ranking-backfill-plus-redis-grafana.csv`
- Added features: `reports\evaluations\vulhub-50-target-scan-v01\curation-v01\train_ready_strict-features.jsonl`
- Added targets: `reports\evaluations\vulhub-50-target-scan-v01\curation-v01\train_ready_strict-runtime-targets.jsonl`

## Decision

นี่คือ candidate training dataset สำหรับ experiment เท่านั้น ยังไม่ใช่ production promote
