# Runtime Regression Plan v01

เป้าหมายคือทำให้ทุกครั้งที่แก้ runtime/model guard เราตรวจซ้ำได้ทันทีว่า behavior สำคัญยังไม่ถอย

## ทำไมต้องมี

ตอนนี้เรามี validation set ที่มีค่ามาก:

```text
multi-family unseen
unseen Solr schema
ranker guard unknown + weak/noisy
```

ชุดพวกนี้ควรทำหน้าที่เป็นข้อสอบประจำ ไม่ควรเอาเข้า train ทับทันที

## สคริปต์

```text
scripts/run_runtime_regression.py
```

สคริปต์นี้จะรัน `scripts/evaluate_runtime_predictions.py` กับชุด baseline ที่บันทึกไว้ แล้วเช็คว่า metric สำคัญยังผ่านเกณฑ์

## Baseline Suites

| Suite | เป้าหมาย |
| --- | --- |
| `ranker_guard_unknown_v01` | กัน unknown-family และ weak/noisy ไม่ให้หลุด |
| `multifamily_unseen_v01` | known family หลายตัวต้องยังผ่าน |
| `unseen_solr_schema_v01` | Solr schema/guard ต้องยังไม่ถอย |

## คำสั่ง

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py scripts\run_runtime_regression.py `
  --model-dir runtime\models\prototype `
  --out-dir reports\regression\runtime-current
```

## Output

```text
reports/regression/runtime-current/runtime-regression-summary.json
reports/regression/runtime-current/RUNTIME-REGRESSION-RESULT-TH.md
```

## เกณฑ์ผ่าน

ตอนนี้ตั้งเกณฑ์แบบ strict เพราะเป็นชุดที่ runtime ล่าสุดผ่านแล้ว:

```text
Gate FP = 0
Gate FN = 0
Known-positive Ranker Top-1 = 1.0
Unknown rejection = 1.0 ในชุดที่มี unknown
Safety flow = 1.0
Strict flow = 1.0
```

ถ้าแก้ runtime รอบหน้าแล้วชุดนี้ตก แปลว่าต้องดู failure ก่อน train/promote ต่อ

## ใช้คู่กับ batch ใหม่

ลำดับที่แนะนำหลังเครื่องสแกนส่ง batch มา:

```text
1. import_scan_batch.py
2. evaluate_runtime_predictions.py กับ batch ใหม่
3. run_runtime_regression.py กับ baseline เดิม
4. ถ้า baseline ไม่ถอย ค่อยพิจารณา train_candidate/validation_ready
```

