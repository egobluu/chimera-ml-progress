# Shared Validation Current Runtime v01

วันที่: 2026-09-03

งานนี้ประเมิน output จาก shared validation 3 ชุดด้วย runtime ปัจจุบันของ repo:

```text
scripts/predict_prototype.py
runtime/models/prototype/gate_precondition_only.json
runtime/models/prototype/family_ranker.json
runtime/models/prototype/prototype_manifest.json
```

## ที่มาของข้อมูล

baseline มาจาก:

```text
C:\Users\rapii\Desktop\kali-share\dataset\evaluations\shared-validation-runtime-v01
```

ใน repo เก็บไว้ที่:

```text
reports/evaluations/shared-validation-runtime-v01/baseline-opencode/
```

copy เฉพาะไฟล์ top-level เท่านั้น ไม่ copy raw folder:

```text
runtime-targets.jsonl
runtime-predictions.jsonl
runtime-metrics.json
family-ranker-errors.csv
unknown-family-guard-report.csv
weak-noisy-report.csv
REPORT-TH.md
```

## จำนวน target

ชุด current runtime มีทั้งหมด 56 targets:

| กลุ่ม | จำนวน | ความหมาย |
| --- | ---: | --- |
| known_positive | 19 | target ที่ exploit family อยู่ใน candidate families ของ runtime |
| unknown_family_positive | 9 | target ที่ exploit ได้ใน lab แต่ family ยังไม่อยู่ใน candidate families |
| negative_control | 28 | negative, weak, noisy หรือ no-exploit target |

## Baseline จาก OpenCode

baseline report เดิมสรุปว่า:

| Metric | Result |
| --- | ---: |
| Gate TP | 19 |
| Gate FP | 4 |
| Gate TN | 24 |
| Gate FN | 0 |
| Gate accuracy | 0.9149 |
| Gate precision | 0.8261 |
| Gate recall | 1.0000 |
| Gate F1 | 0.9048 |
| Family Ranker Top-1 | 19/19 |
| Family Ranker Top-3 | 19/19 |
| Unknown-family blocked | 9/9 |
| Weak/noisy blocked | 27/28 |
| Weak/noisy leaked | 1/28 |

leak สำคัญคือ:

```text
redis_weak_guard_01
```

สาเหตุคือ target มี Redis signal บางส่วน:

```text
redis_detected=1
redis_info_accessible=1
lua_available=0
known_family_signal_count=0
```

runtime เดิมยังปล่อยเป็น:

```text
ready_for_safe_verification
```

ซึ่งเสี่ยง เพราะ Redis family นี้ต้องใช้ Lua/sandbox condition เป็นหลักฐานสำคัญ

## Runtime ที่รันซ้ำใน repo นี้

หลังใช้ runtime ปัจจุบันและแก้ evaluator ให้เข้าใจ `unknown_family_positive` ถูกต้อง ผลเป็น:

| Metric | Result |
| --- | ---: |
| Total targets | 56 |
| Gate TP | 28 |
| Gate FP | 0 |
| Gate TN | 28 |
| Gate FN | 0 |
| Gate accuracy | 1.0000 |
| Gate precision | 1.0000 |
| Gate recall | 1.0000 |
| Gate F1 | 1.0000 |
| Known-positive Ranker Top-1 | 19/19 |
| Known-positive Ranker Top-3 | 19/19 |
| Unknown-family rejected | 9/9 |
| Safety flow | 56/56 |
| Strict flow | 56/56 |

ไฟล์ผลลัพธ์:

```text
reports/evaluations/shared-validation-runtime-v01/current-runtime/corrected-runtime-evaluation.json
reports/evaluations/shared-validation-runtime-v01/current-runtime/corrected-runtime-predictions.jsonl
reports/evaluations/shared-validation-runtime-v01/current-runtime/CORRECTED-RUNTIME-EVALUATION-TH.md
```

## สิ่งที่แก้ใน runtime/evaluator

### 1. Evaluation category bug

เดิม evaluator นับ unknown เฉพาะ:

```text
category == unknown_family
```

แต่ข้อมูลจริงใช้:

```text
unknown_family_positive
```

จึงแก้ให้ใช้:

```text
category.startswith("unknown_family")
```

ผลคือ Gate metric นับ unknown-family positive เป็น positive ถูกต้อง

### 2. Unknown guard แรงเกินกับ known family

พบ 2 target:

```text
jenkins_unknown_01
elasticsearch_unknown_01
```

สองตัวนี้เป็น known family จริงและ Ranker ทาย family ถูก แต่มี `unknown_product_detected=1` ติดมาจากต้นทาง จึงถูก guard บังคับเป็น `unknown_family_triage`

แก้ policy เป็น:

```text
ถ้า unknown_product_detected=1
แต่ Ranker มี family-specific positive signal ของ known family แล้ว
ไม่ต้อง force เป็น unknown_family ทันที
ให้ family_readiness ตัดสินต่อว่า ready หรือ manual triage
```

ผลหลังแก้คือสองตัวนี้ไม่ถูกโยนเป็น unknown ผิด ๆ แล้ว และยังไม่ทำให้ unknown-family จริงหลุดเป็น known-family

## วิธีอ่านผล

Gate ตอบคำถามแรก:

```text
target นี้มี precondition พอให้ตรวจ exploit ต่อไหม
```

Family Ranker ตอบคำถามถัดมา:

```text
ถ้าจะตรวจต่อ ควรเริ่มจาก exploit family ไหน
```

Unknown-family guard กันกรณี:

```text
Ranker เป็น closed-set จึงต้องเลือก family ที่รู้จักเสมอ
แต่ target จริงอาจเป็น family ที่ model ยังไม่รู้จัก
```

CVE/Module Resolver ยังควรเป็น mapping table หลัง Ranker:

```text
family -> CVE candidates -> Metasploit module/manual PoC
```

ไม่ควรให้ ML rank CVE ตรง ๆ ตอนนี้ เพราะ CVE เยอะกว่า target มาก และเสี่ยง overfit กับชื่อ/alias

## สรุปการตัดสินใจ

ผลนี้ถือว่า safe สำหรับ merge runtime/evaluation fix และใช้เป็น regression baseline ได้

แต่ยังไม่ควร claim production accuracy 100% เพราะนี่เป็น subset/sanity validation ที่มาจาก lab และชุด guard ที่เราคุม schema เอง

คำแนะนำ:

```text
1. merge 56 targets เข้า training/evaluation pipeline แบบมี split ชัดเจน
2. เก็บชุดนี้เป็น regression validation กัน runtime ถอย
3. retrain หลังเพิ่ม negative/weak family-specific precondition มากขึ้น
4. เพิ่ม resolver mapping table สำหรับ family ที่ coverage ยังไม่ครบ
5. รอข้อมูลสแกน overnight เป็น batch ถัดไป ไม่ต้อง block งานรอบนี้
```
