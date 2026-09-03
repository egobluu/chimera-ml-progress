# Candidate Runtime Dataset Merge

## Summary

| Item | Count |
| --- | ---: |
| Base rows | 111 |
| Added train-ready rows | 12 |
| Output rows | 123 |
| Output columns | 124 |

## Label Counts

```json
{
  "0": 69,
  "1": 54
}
```

## Input

- Base dataset: `reports\experiments\candidate-vulhub50-rawfill-combined-v01\candidate-training-dataset.csv`
- Added features: `reports\evaluations\vulhub-recheck-pilot-ready-2026-09-03-v01\curation-baseline-strict12-v01\train_ready_strict-features.jsonl`
- Added targets: `reports\evaluations\vulhub-recheck-pilot-ready-2026-09-03-v01\curation-baseline-strict12-v01\train_ready_strict-runtime-targets.jsonl`

## Decision

นี่คือ candidate training dataset สำหรับ experiment เท่านั้น ยังไม่ใช่ production promote
