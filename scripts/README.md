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
| `train_gate_model.py` | train XGBoost binary classifier สำหรับ ML-only Exploitability Gate |
| `rank_target_two_stage.py` | ใช้ model ที่ train แล้ว inference target ใหม่แบบ exploit/no_exploit |

## Flow การใช้งาน

```bash
python3 generate_gate_features.py
python3 build_dataset.py
python3 train_gate_model.py
python3 rank_target_two_stage.py --evidence-dir raw-curated/tomcat_CVE-2020-1938 --json
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

