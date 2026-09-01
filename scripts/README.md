# Scripts

โฟลเดอร์นี้เก็บ script ที่ใช้ในงาน ML ของ `chimera-scanner-dataset` ตั้งแต่การสร้าง dataset ไปจนถึงการ train และ inference

script เหล่านี้อ้าง path แบบ Kali report output เป็นหลัก เพราะถูกสร้างจาก workflow ที่รันใน Kali VM:

```text
/home/kali/reports/dec-ml-ranking-data-expand-2026-08-31/
/home/kali/reports/dec-gate-feature-improve-2026-08-31/
/home/kali/reports/dec-ml-only-gate-v02-2026-08-31/
```

## รายการ script

| script | ใช้ทำอะไร |
| --- | --- |
| `generate_gate_features.py` | สร้าง `gate-feature-evidence.jsonl` ให้ครบทุก validated target |
| `build_dataset.py` | รวม JSONL/raw evidence เป็น `target-exploitability-dataset.csv` |
| `merge_backfill_features.py` | รวม light backfill features เข้ากับ target-level dataset เดิม |
| `merge_ranker_backfill_dataset.py` | รวม JSONL backfill ที่ safe_to_merge เข้า CSV dataset สำหรับ train runtime/ranker |
| `train_gate_model.py` | train XGBoost binary classifier สำหรับ ML-only Exploitability Gate |
| `train_gate_profiles.py` | train/evaluate หลาย feature profile เพื่อดูว่าโมเดลพึ่ง feature รั่วมากแค่ไหน |
| `plan_precondition_probes.py` | สร้างแผน probe เจาะจงจาก false positive/false negative ของโมเดล |
| `rank_target_two_stage.py` | ใช้ model ที่ train แล้ว inference target ใหม่แบบ exploit/no_exploit |
| `audit_gate_features.py` | ตรวจ feature leak และแยก feature เป็น precheck/postcheck ก่อนเชื่อคะแนน model |
| `train_runtime_models.py` | train ชุด model runtime prototype ที่ใช้ส่งต่อให้ฝั่ง LLM/agentic |
| `predict_prototype.py` | entrypoint ใช้งานจริงระดับ prototype รับ feature JSON แล้วคืนผล Gate + Ranker + Unknown Guard |
| `evaluate_unknown_family.py` | ทดสอบว่า Ranker จะทำอย่างไรเมื่อเจอ target นอก family ที่รู้จัก |
| `evaluate_runtime_predictions.py` | rerun runtime prediction จาก feature JSONL แล้วคำนวณ corrected metrics แยก safety กับ ranking |

## Flow การใช้งาน

```bash
python3 generate_gate_features.py
python3 build_dataset.py
python3 merge_backfill_features.py --base-dataset target-exploitability-dataset.csv --backfill-jsonl merged-backfill-precheck-features.jsonl --out-csv target-exploitability-with-light-backfill.csv --summary-json merge-summary.json
python3 merge_ranker_backfill_dataset.py --base-dataset reports/evaluations/family-ranking-backfill-v01/target-exploitability-family-ranking-backfill.csv --backfill-jsonl reports/evaluations/ranker-schema-backfill-redis-grafana-v01/merged-ranker-schema-backfill-features.jsonl --audit-jsonl reports/evaluations/ranker-schema-backfill-redis-grafana-v01/label-consistency-audit.jsonl --out-csv reports/evaluations/ranker-schema-backfill-redis-grafana-v01/target-exploitability-family-ranking-backfill-plus-redis-grafana.csv --summary-json reports/evaluations/ranker-schema-backfill-redis-grafana-v01/dataset-merge-summary.json
python3 train_gate_model.py
python3 train_gate_profiles.py --dataset target-exploitability-dataset.csv --out-dir derived/profile-audit
python3 plan_precondition_probes.py --predictions derived/profile-audit/strict_precheck-predictions.csv --threshold 0.10 --out-dir derived/probe-plan
python3 rank_target_two_stage.py --evidence-dir raw-curated/tomcat_CVE-2020-1938 --json
python3 audit_gate_features.py --dataset target-exploitability-dataset.csv --out-dir derived/audit
python3 evaluate_runtime_predictions.py --features-jsonl reports/evaluations/unseen-validation-v02/unseen-v02-precheck-features.jsonl --targets-jsonl reports/evaluations/unseen-validation-v02/unseen-v02-targets.jsonl --out-dir reports/evaluations/unseen-validation-v02
```

## หลักการสำคัญ

- ใช้เฉพาะ `validated_positive` และ `validated_negative` ในการ train
- ข้าม `inconclusive`
- ห้ามใช้ `target_id`, folder path, CVE string, หรือ label ตรง ๆ เป็น feature
- แยก precheck feature กับ postcheck/verification evidence ให้ชัด
- ใช้ threshold tuning เพื่อลด false negative ก่อน แล้วค่อยลด false positive

## Output หลัก

```text
target-exploitability-dataset.csv
gate-feature-schema.json
gate-metrics.json
models/gate_xgb_v02.json
derived/gate-threshold-sweep.csv
derived/gate-feature-importance.csv
derived/gate-failure-analysis.csv
```
