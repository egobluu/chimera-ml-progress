# Candidate Retrain Result: vulhub50-trainready-v01

## ทำอะไร

สร้าง candidate runtime model ใหม่จาก dataset:

```text
base training dataset 67 rows
+ train_ready_strict จาก vulhub-50-target-scan-v01 14 rows
= candidate training dataset 81 rows
```

ไม่ได้เอา 51 rows ทั้งหมดเข้า train เพราะ 37 rows ยังไม่มี raw evidence folder ครบ จึงใช้เป็น validation/regression ก่อน

## Training Dataset

| Item | Count |
| --- | ---: |
| Base rows | 67 |
| Added strict train-ready rows | 14 |
| Total rows | 81 |
| Label 0 / negative | 46 |
| Label 1 / positive | 35 |

## Candidate Gate LOO Metrics

| Metric | Baseline | Candidate |
| --- | ---: | ---: |
| Train targets | 67 | 81 |
| Ranker positive targets | 28 | 35 |
| Gate accuracy | 0.9701 | 0.9753 |
| Gate precision | 0.9333 | 0.9459 |
| Gate recall | 1.0000 | 1.0000 |
| Gate F1 | 0.9655 | 0.9722 |
| Gate TP/FP/TN/FN | 28/2/37/0 | 35/2/44/0 |

## Runtime Regression

Candidate model ผ่าน regression 5/5:

| Suite | Status |
| --- | --- |
| ranker_guard_unknown_v01 | pass |
| multifamily_unseen_v01 | pass |
| unseen_solr_schema_v01 | pass |
| runtime_stress_v01 | pass |
| vulhub_50_scan_v01 | pass |

## Decision

Candidate ผ่าน promotion gate ขั้นต้น:

- Gate FN ยังเป็น 0
- safety ไม่ถอยหลัง
- unknown-family guard ไม่ถอยหลัง
- Ranker known-positive ไม่ถอยหลัง

แต่ยังไม่ควร promote เป็น production ถาวรทันที เพราะข้อมูลใหม่ที่ strict raw evidence มีแค่ 14 rows

สถานะที่เหมาะสมตอนนี้:

```text
candidate-vulhub50-trainready-v01 = staging model
runtime/models/prototype = production/prototype model เดิม
```

ขั้นต่อไปคือเติม raw evidence ให้ `validation_only` 37 rows หรือเก็บ batch ใหม่อีกชุด แล้วค่อย retrain รอบใหญ่กว่า
