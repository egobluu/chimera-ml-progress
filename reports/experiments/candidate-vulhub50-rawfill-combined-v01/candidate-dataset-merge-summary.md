# Candidate Runtime Dataset Merge

## Summary

| Item | Count |
| --- | ---: |
| Base rows | 67 |
| Added train-ready rows | 44 |
| Output rows | 111 |
| Output columns | 124 |

## Label Counts

```json
{
  "0": 66,
  "1": 45
}
```

## Input

- Base dataset: `reports\evaluations\ranker-schema-backfill-redis-grafana-v01\target-exploitability-family-ranking-backfill-plus-redis-grafana.csv`
- Added features: `reports\evaluations\vulhub50-combined-trainready-v01\combined-train-ready-features.jsonl`
- Added targets: `reports\evaluations\vulhub50-combined-trainready-v01\combined-train-ready-targets.jsonl`

## Decision

นี่คือ candidate training dataset สำหรับ experiment เท่านั้น ยังไม่ใช่ production promote
