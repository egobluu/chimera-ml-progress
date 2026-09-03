# Raw Fill Candidate Retrain Result v01

วันที่: 2026-09-03

## สรุปสั้น

รับ batch `vulhub-50-target-scan-v01-raw-fill-v01` เข้ามาแล้ว แต่ยังไม่ promote เป็น runtime default

เหตุผล:

```text
รอบ raw-fill ช่วยเติม train-ready ได้จริง
แต่ full batch ยังมี positive 7 ตัวที่ feature หลักว่างและ raw evidence หาย
ถ้าใช้ทั้งก้อนจะทำให้ Ranker/CVE Resolver ดูแย่ลงแบบผิดธรรมชาติ
```

## สิ่งที่ทำ

1. Import batch ใหม่จาก Kali share
2. Run runtime evaluation บน full raw-fill batch
3. แก้ curation rule ให้ `train_ready_strict` ต้องอยู่ใน `safe-to-merge-targets.txt` และ validation status ต้องเป็นมาตรฐาน
4. Curate batch ใหม่
5. รวม train-ready รอบเดิม 14 targets + raw-fill 30 targets เป็น combined train-ready 44 targets
6. สร้าง candidate training dataset 111 rows
7. Train candidate runtime model ใหม่
8. Run regression 5 suites
9. Evaluate candidate บน combined train-ready และ full raw-fill batch

## Curation Result

Raw-fill batch:

| Split | Count |
| --- | ---: |
| train_ready_strict | 30 |
| validation_only | 14 |
| needs_recheck | 7 |

Combined train-ready:

| Source | Count |
| --- | ---: |
| previous Vulhub 50 curation | 14 |
| raw-fill curation | 30 |
| total combined train-ready | 44 |

## Train Dataset

| Item | Count |
| --- | ---: |
| base rows | 67 |
| added train-ready rows | 44 |
| output rows | 111 |
| positive labels | 45 |
| negative labels | 66 |

Candidate model:

```text
runtime/models/candidate-vulhub50-rawfill-combined-v01/
```

## Candidate Training Metrics

Gate leave-one-out:

| Metric | Value |
| --- | ---: |
| accuracy | 0.9550 |
| precision | 0.9000 |
| recall | 1.0000 |
| F1 | 0.9474 |
| TP/FP/TN/FN | 45 / 5 / 61 / 0 |

Ranker:

| Metric | Value |
| --- | ---: |
| positive train targets | 40 |
| candidate families | 16 |

## Regression Result

Candidate ผ่าน runtime regression:

```text
5/5 suites pass
```

Suites:

```text
ranker_guard_unknown_v01
multifamily_unseen_v01
unseen_solr_schema_v01
runtime_stress_v01
vulhub_50_scan_v01
```

## Combined Train-ready Evaluation

บน combined train-ready 44 targets:

| Metric | Result |
| --- | ---: |
| Gate TP/FP/TN/FN | 17 / 2 / 25 / 0 |
| Gate precision | 0.8947 |
| Gate recall | 1.0000 |
| Family Ranker Top-1 | 12/12 = 1.0000 |
| CVE Resolver Top-1 | 12/12 = 1.0000 |
| Unknown-family rejection | 5/5 = 1.0000 |
| Safety flow | 44/44 = 1.0000 |
| Strict flow | 44/44 = 1.0000 |

## Full Raw-fill Evaluation Warning

บน full raw-fill 51 targets:

| Metric | Prototype | Candidate |
| --- | ---: | ---: |
| Gate precision | 0.7188 | 0.7188 |
| Gate recall | 1.0000 | 1.0000 |
| Family Ranker Top-1 | 0.5333 | 0.6000 |
| CVE Resolver Top-1 | 0.5000 | 0.5000 |
| Safety flow | 0.8627 | 0.8627 |

สาเหตุหลักไม่ใช่ model อย่างเดียว แต่เป็น data quality:

```text
known-positive 7 targets มี feature หลักว่างและ raw evidence folder หาย
จึงไม่ควรใช้ full raw-fill batch เป็นตัววัด production accuracy
```

Targets ที่ต้อง recheck:

```text
grafana_cve_2021_43798_positive_001
redis_lua_positive_001
tomcat_put_positive_001
tomcat_ajp_positive_001
couchdb_positive_001
solr_velocity_positive_001
shiro_positive_001
```

## Decision

ยังไม่ promote candidate เป็น `runtime/models/prototype`

เหตุผล:

1. Regression ผ่านจริง
2. Combined train-ready ผ่านดี
3. แต่ Gate LOO precision/F1 ลดจาก baseline
4. Full raw-fill ยังมี sparse-feature failure ที่ต้อง recheck
5. ข้อมูลใหม่เพิ่ม positive known family แค่ 5 ตัว ส่วนใหญ่เป็น negative/unknown guard data

สถานะที่ถูกต้อง:

```text
candidate/staging only
not production default
```

## Next

ให้ OpenCode/Kali กลับไปเติม raw evidence + feature สำหรับ 7 targets ใน `needs_recheck` ก่อน แล้วค่อย retrain/promote รอบถัดไป
