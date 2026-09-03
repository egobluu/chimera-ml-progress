# Candidate Runtime Model Comparison

## Training Metrics

| Model | Train targets | Ranker positive targets | Gate precision | Gate recall | Gate F1 | Gate FP/FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 67 | 28 | 0.9333 | 1.0 | 0.9655 | 2/0 |
| candidate | 111 | 40 | 0.9 | 1.0 | 0.9474 | 5/0 |

## Regression Comparison

| Suite | Baseline safety | Candidate safety | Baseline strict | Candidate strict | Candidate status |
| --- | ---: | ---: | ---: | ---: | --- |
| multifamily_unseen_v01 | 1.0 | 1.0 | 1.0 | 1.0 | pass |
| ranker_guard_unknown_v01 | 1.0 | 1.0 | 1.0 | 1.0 | pass |
| runtime_stress_v01 | 1.0 | 1.0 | 1.0 | 1.0 | pass |
| unseen_solr_schema_v01 | 1.0 | 1.0 | 1.0 | 1.0 | pass |
| vulhub_50_scan_v01 | 1.0 | 1.0 | 1.0 | 1.0 | pass |

## Decision

Candidate ผ่าน gate promotion ขั้นต้น: regression ทุก suite ผ่าน, Gate FN เป็น 0, และ safety ไม่ถอยหลัง แต่ยังควร promote เป็น candidate/staging ก่อน ไม่ใช่ production ถาวร เพราะข้อมูลเพิ่มมี strict raw evidence เพียง 14 rows

## Notes

- Candidate model trained from base 67 rows + 14 strict train-ready rows from Vulhub 50 scan.
- The remaining 37 rows stay validation-only until raw evidence is filled in.
- Do not promote automatically just because the small train-ready subset scores 100%.
