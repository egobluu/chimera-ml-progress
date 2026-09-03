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
  "0": 66,
  "1": 57
}
```

## Input

- Base dataset: `reports\experiments\candidate-vulhub50-rawfill-combined-v01\candidate-training-dataset.csv`
- Added features: `reports\evaluations\vulhub-longrun-gate-ranker-cve-v02\curation-candidate-v03\train_ready_strict-features.jsonl`
- Added targets: `reports\evaluations\vulhub-longrun-gate-ranker-cve-v02\curation-candidate-v03\train_ready_strict-runtime-targets.jsonl`

## Decision

นี่คือ candidate training dataset สำหรับ experiment เท่านั้น ยังไม่ใช่ production promote
