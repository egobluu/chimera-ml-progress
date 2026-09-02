# Machine 2 Runtime Workflow

เอกสารนี้อธิบายบทบาทเครื่อง 2 ตาม setup ปัจจุบัน:

```text
เครื่อง 2
├── Host Windows: Codex
└── Kali VM: OpenCode + Linux/security tools
```

งานรอบนี้ไม่ต้องรอเครื่องสแกนอีกเครื่อง และไม่ต้องรอ overnight scan

## Host Codex ทำอะไร

Codex บน host เป็นตัวคุม repo และ ML runtime:

```text
1. รับไฟล์จาก shared folder
2. normalize targets/features
3. run scripts/predict_prototype.py
4. evaluate Gate/Ranker/Unknown guard
5. ใช้ resolver mapping table
6. สร้าง priority report
7. update docs/report
```

ไฟล์หลัก:

```text
scripts/prepare_shared_runtime_evaluation.py
scripts/evaluate_runtime_predictions.py
scripts/generate_priority_report.py
runtime/resolver/family-cve-module-map.json
```

## Kali VM OpenCode ทำอะไร

OpenCode ใน Kali VM ใช้เมื่อจำเป็นต้องใช้ Linux/security tooling:

```text
1. รัน tool ที่ host Windows ไม่มีหรือรันไม่สะดวก
2. ทำ lab check ที่ได้รับอนุญาต
3. สร้าง evidence/features ลง shared folder
4. ห้าม retrain เองถ้ายังไม่ได้สั่ง
5. ห้ามแก้ runtime policy เองถ้ายังไม่ได้สั่ง
```

Kali VM ไม่ใช่ blocker ของงานนี้ เพราะ Codex host สามารถ evaluate/runtime/report จากข้อมูลที่มีอยู่แล้วได้

## Runtime Flow บนเครื่อง 2

```text
runtime-targets/features
  -> Gate
  -> Family Ranker
  -> Unknown-family guard
  -> final_decision
  -> CVE/Module Resolver
  -> priority report
```

## CVE/Module Resolver

Resolver ไม่ใช่ ML model

หน้าที่คือ mapping หลัง Ranker:

```text
family -> CVE candidates -> Metasploit module/manual safe probe
```

ข้อห้าม:

```text
ML ไม่ควร rank CVE ตรง ๆ ตอนนี้
Resolver ห้ามถูกใช้ถ้า final_decision ยังไม่ใช่ ready_for_safe_verification
Metasploit/manual PoC result เป็น postcheck ไม่ใช่ precheck feature
```

## คำสั่งที่ใช้บน Host Codex

เตรียม shared validation:

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py scripts\prepare_shared_runtime_evaluation.py `
  --source C:\Users\rapii\Desktop\kali-share\dataset\evaluations\shared-validation-runtime-v01 `
  --out-dir reports\evaluations\shared-validation-runtime-v01
```

สร้าง priority report:

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py scripts\generate_priority_report.py `
  --predictions reports\evaluations\shared-validation-runtime-v01\current-runtime\corrected-runtime-predictions.jsonl `
  --targets reports\evaluations\shared-validation-runtime-v01\current-runtime-inputs\targets.jsonl `
  --resolver runtime\resolver\family-cve-module-map.json `
  --out-dir reports\evaluations\shared-validation-runtime-v01\priority-current
```

## ผลล่าสุด

จาก shared validation 56 targets:

| Queue | Count |
| --- | ---: |
| ready_for_safe_verification | 17 |
| manual_triage_before_exploit | 2 |
| unknown_family_triage | 9 |
| needs_more_evidence | 6 |
| do_not_exploit_now | 22 |

ไฟล์ report:

```text
reports/evaluations/shared-validation-runtime-v01/priority-current/PRIORITY-REPORT-TH.md
reports/evaluations/shared-validation-runtime-v01/priority-current/priority-review.csv
```
