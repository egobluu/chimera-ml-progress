# Scanner Batch Ingestion Plan v01

เป้าหมายของรอบนี้คือเตรียม ML repo ให้พร้อมรับข้อมูลจำนวนมากจาก scanner box โดยไม่ต้องปรับมือเยอะทุก batch

## หลักคิด

เครื่องสแกนมีหน้าที่ผลิตข้อมูล:

```text
features.jsonl
targets.jsonl
validation-results.jsonl
cve-enrichment.jsonl
raw/<target_id>/*
```

ฝั่ง Codex/ML repo มีหน้าที่รับเข้าแบบควบคุมคุณภาพ:

```text
copy top-level files
normalize JSONL
map family aliases
join enrichment metadata
audit schema/label
run runtime evaluation
แยก train_candidate / validation_ready / quarantine
```

## สคริปต์ที่เพิ่ม

```text
scripts/import_scan_batch.py
```

หน้าที่:

1. รับ `--source-dir` จาก shared folder หรือ output ของ scanner box
2. copy เฉพาะ top-level files เข้า report folder
3. normalize JSON stream เป็น JSONL
4. สร้าง `runtime-targets.jsonl`
5. join `cve-enrichment.jsonl` เข้า `features.enriched.jsonl`
6. เขียน `import-audit.json`
7. เขียน `IMPORT-AUDIT-TH.md`

## วิธีใช้

ตัวอย่าง:

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py scripts\import_scan_batch.py `
  --source-dir C:\Users\rapii\Desktop\kali-share\dataset\dec-overnight-lab-scan-enrichment-2026-09-02 `
  --out-dir reports\evaluations\overnight-lab-scan-enrichment-v01 `
  --model-dir runtime\models\prototype
```

แล้ว evaluate:

```powershell
& $py scripts\evaluate_runtime_predictions.py `
  --features-jsonl reports\evaluations\overnight-lab-scan-enrichment-v01\features.enriched.jsonl `
  --targets-jsonl reports\evaluations\overnight-lab-scan-enrichment-v01\runtime-targets.jsonl `
  --model-dir runtime\models\prototype `
  --out-dir reports\evaluations\overnight-lab-scan-enrichment-v01\runtime-evaluation-current
```

## Family Mapping

ชื่อจาก scanner/lab อาจไม่ตรงกับ runtime family จึง map ก่อน evaluate:

| Source label | Runtime family |
| --- | --- |
| `redis_lua` | `redis` |
| `grafana_path_traversal` | `grafana` |
| `couchdb` | `couchdb_auth` |
| `couchdb_rce` | `couchdb_auth` |
| `solr_velocity_rce` | `solr_velocity` |
| `shiro_deserialize` | `shiro_key` |
| `shiro_rce` | `shiro_key` |
| `thinkphp` | `thinkphp_rce` |
| `jenkins_rce` | `jenkins` |
| `elasticsearch_rce` | `elasticsearch` |

ถ้า map แล้วไม่อยู่ใน candidate families ของ runtime จะถูกจัดเป็น:

```text
category = unknown_family
expected_family = unknown
```

## Enrichment Timing

CISA KEV / EPSS / NVD จะถูก join หลัง scanner feature แล้ว แต่ก่อน evaluation/train

ตอนนี้ใช้เป็น metadata/context ก่อน:

```text
in_cisa_kev
epss_score
epss_percentile
cvss_base_score
cvss_base_severity_*
nvd_cwe_count
```

ยังไม่ควรให้ model runtime ปัจจุบันใช้เป็น decision feature โดยตรงจนกว่าจะทำ training profile ใหม่ เช่น:

```text
precondition_only
precondition_plus_cve_context
precondition_plus_kev_epss_nvd
```

## Audit ที่ต้องดู

ดูไฟล์:

```text
IMPORT-AUDIT-TH.md
import-audit.json
```

issue สำคัญ:

| Issue | ความหมาย |
| --- | --- |
| `missing_feature_row` | target มี label แต่ไม่มี feature |
| `missing_validation_row` | ยังไม่มีผล validation |
| `postcheck_field_used_as_feature` | มี field ที่ควรเป็น label-only หลุดเข้า feature |
| `mapped_to_unknown_family` | source family ไม่อยู่ใน runtime candidate |
| `missing_cve_enrichment` | target มี CVE แต่ enrichment ยังไม่ครบ |

## Decision

หลัง import + runtime evaluation:

```text
ไม่มี error + runtime safe -> validation_ready
มี label/evidence ขัดกัน -> quarantine
เป็นข้อมูลใหม่แต่ยังไม่มี validation -> needs_manual_review
สะอาดและไม่ใช่ validation holdout -> train_candidate
```

## ข้อห้าม

อย่าเอา batch ทั้งคืนเข้า train ทันที

ให้ใช้ importer/audit ก่อนเสมอ เพราะข้อมูลจาก scanner box จะมีทั้ง:

```text
positive
negative
weak/noisy
unknown-family
incomplete container runs
metadata-only CVE context
```

