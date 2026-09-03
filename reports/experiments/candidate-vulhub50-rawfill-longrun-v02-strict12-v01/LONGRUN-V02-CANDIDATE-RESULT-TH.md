# Longrun v02 Candidate Result

วันที่: 2026-09-03

## ทำอะไรไปแล้ว

1. import ชุด `vulhub-longrun-gate-ranker-cve-v02` จาก Kali share เข้า repo ฝั่ง Codex
2. แก้ `scripts/import_scan_batch.py` ให้ join `validation-results.jsonl` ด้วย `target_id` เพราะ v02 เก็บสถานะ validation ไว้คนละไฟล์กับ `targets.jsonl`
3. แก้ `scripts/evaluate_runtime_predictions.py` ให้มี `standard_label_metrics` เพื่อแยกคะแนนของ target ที่มี label ใช้งานจริงออกจาก `inconclusive`
4. แก้ `scripts/predict_prototype.py` ให้ blocking negative signal ใช้แบบสัมพันธ์กับ product/family มากขึ้น
5. แก้ readiness ให้ positive counterpart ชนะ negative counterpart เช่น `ajp_port_open=1` ไม่ควรถูก `ajp_port_closed=1` บล็อก
6. curate v02 ด้วย candidate evaluation ใหม่
7. รวม strict train-ready จาก v02 เข้า candidate dataset
8. retrain candidate runtime model
9. run runtime regression ครบ 5 suites

## v02 Import

ไฟล์ต้นทาง:

`C:\Users\rapii\Desktop\kali-share\dataset\vulhub-longrun-gate-ranker-cve-v02`

ผล import:

| รายการ | จำนวน |
| --- | ---: |
| targets | 31 |
| features | 31 |
| validation rows | 31 |
| safe_to_merge | 19 |
| quarantined | 12 |
| validated_positive | 19 |
| inconclusive | 12 |

## Curation หลังแก้ Guard

| Split | จำนวน |
| --- | ---: |
| train_ready_strict | 12 |
| validation_only | 1 |
| needs_recheck | 18 |

`train_ready_strict` รอบนี้:

- `couchdb_positive_001`
- `gitea_pos_001`
- `hugegraph_pos_001`
- `kibana_pos_001`
- `metabase_pos_001`
- `mongo_express_pos_001`
- `n8n_pos_001`
- `superset_pos_001`
- `supervisor_pos_001`
- `tomcat_ajp_positive_001`
- `tomcat_put_positive_001`
- `zabbix_pos_001`

ยังต้อง recheck:

- `confluence_pos_001`
- `gitlab_pos_001`
- `joomla_pos_002`
- `jupyter_pos_001`
- `minio_pos_001`
- `shiro_positive_001`
- `solr_velocity_positive_001`
- และกลุ่ม `inconclusive` อีก 11 ตัว

## Candidate Training

สร้าง candidate dataset:

| รายการ | จำนวน |
| --- | ---: |
| base rows | 111 |
| added v02 strict rows | 12 |
| output rows | 123 |
| positive rows | 57 |
| negative rows | 66 |

โมเดลที่ train:

- Gate: `gate_precondition_only.json`
- Family Ranker: `family_ranker.json`
- Candidate model dir: `runtime\models\candidate-vulhub50-rawfill-longrun-v02-strict12-v01`

Gate LOO metrics:

| Metric | Value |
| --- | ---: |
| accuracy | 0.9593 |
| precision | 0.9194 |
| recall | 1.0000 |
| F1 | 0.9580 |
| TP | 57 |
| FP | 5 |
| TN | 61 |
| FN | 0 |

Family Ranker:

| Metric | Value |
| --- | ---: |
| positive train targets | 43 |
| candidate families | 16 |

## Runtime Regression

รัน regression ผ่าน 5/5 suites:

- `ranker_guard_unknown_v01`
- `multifamily_unseen_v01`
- `unseen_solr_schema_v01`
- `runtime_stress_v01`
- `vulhub_50_scan_v01`

หมายเหตุ: `runtime_stress_v01` มี Gate FP 1 แต่ final safety/strict flow ยังผ่าน เพราะระบบยังไม่ปล่อยเป็น `ready_for_safe_verification`

## v02 Evaluation ด้วย Candidate strict12

นับเฉพาะ standard-label 19 targets:

| Metric | Value |
| --- | ---: |
| Gate TP | 12 |
| Gate FP | 0 |
| Gate TN | 0 |
| Gate FN | 7 |
| Gate precision | 1.0000 |
| Gate recall | 0.6316 |
| Gate F1 | 0.7742 |
| Known-family Ranker Top-1 | 3/6 |
| Known-family Ranker Top-3 | 3/6 |
| Unknown guard rejection | 9/13 |
| Safety flow accuracy | 12/19 |
| Strict flow accuracy | 12/19 |

Known-family ที่ผ่านครบ:

- CouchDB Auth -> `CVE-2017-12635`
- Tomcat AJP -> `CVE-2020-1938`
- Tomcat PUT -> `CVE-2017-12615`

Known-family ที่ยังไม่ผ่าน:

- Joomla -> Gate ยังเป็น `no_exploit`
- Shiro -> Gate ยังเป็น `low_confidence`
- Solr Velocity -> Gate ยังเป็น `low_confidence`

## สรุปตัดสินใจ

ยังไม่ควร promote เป็น production model ทันที แต่ candidate strict12 ถือว่าเป็น staging ที่ดีขึ้นจริง

เหตุผล:

- regression เดิมผ่าน 5/5
- Gate LOO ดีขึ้น
- เพิ่ม train-ready จาก v02 ได้ 12 targets
- แต่ v02 ยังมี FN 7/19 ใน standard-label
- batch นี้ไม่มี negative/weak ใหม่ ทำให้ยังไม่ควรเชื่อ precision โลกจริงมากเกินไป

## งานต่อไป

1. recheck `joomla_pos_002`, `shiro_positive_001`, `solr_velocity_positive_001` ให้ feature เฉพาะ family ชัดขึ้น
2. เติม negative/weak pair ให้ family ใหม่ เช่น GitLab, Confluence, MinIO, Jupyter, Zabbix
3. เพิ่ม unknown-family feature map สำหรับ product ใหม่ที่เจอบ่อย
4. ค่อย retrain รอบถัดไปเมื่อมี positive/negative/weak balance ดีกว่านี้
5. ยังไม่ push git จนกว่าจะสั่ง
