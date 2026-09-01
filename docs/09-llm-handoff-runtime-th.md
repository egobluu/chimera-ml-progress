# ส่งไม้ต่อให้ฝั่ง LLM/Agentic

## คำตอบสั้น

เวลาส่งต่อ ไม่ใช่ส่งแค่ feature และโค้ด train/test

ต้องส่งชุด runtime ที่เรียกใช้งานได้จริง:

```text
feature JSON
-> scripts/predict_prototype.py
-> runtime/models/prototype/*
-> JSON result ให้ LLM เอาไปอธิบาย/ตัดสินใจต่อ
```

## อะไรคือของใช้จริง

| ส่วน | ใช้จริงไหม | เหตุผล |
| --- | --- | --- |
| `runtime/models/prototype/gate_precondition_only.json` | ใช้จริง | Gate model สำหรับบอกว่าน่าลอง exploit ไหม |
| `runtime/models/prototype/family_ranker.json` | ใช้จริง | Ranker model สำหรับจัดอันดับ exploit family |
| `runtime/models/prototype/prototype_manifest.json` | ใช้จริง | บอก feature, threshold, candidate families |
| `scripts/predict_prototype.py` | ใช้จริง | entrypoint ที่ LLM/agentic เรียก |
| `examples/input/*.json` | ใช้จริงเป็นตัวอย่าง | บอก format input |
| `examples/output/*.json` | ใช้จริงเป็นตัวอย่าง | บอก format output |

## อะไรคือของ train/test

| ส่วน | ใช้ทำอะไร |
| --- | --- |
| `scripts/train_runtime_models.py` | train model runtime ใหม่จาก baseline dataset |
| `scripts/train_gate_profiles.py` | test feature profiles และ audit ว่า profile ไหนใช้จริงได้ |
| `scripts/train_family_ranker.py` | train/evaluate family ranking |
| `scripts/evaluate_unknown_family.py` | test unknown-family guard |
| `reports/evaluations/*` | เก็บผลทดลองย้อนหลังเพื่ออธิบายว่าทำไมเลือก model นี้ |

## อะไรคือของอธิบาย

| ส่วน | ใช้ทำอะไร |
| --- | --- |
| `docs/04-feature-schema-th.md` | อธิบาย schema และ feature |
| `docs/07-feature-catalog-th.md` | catalog feature ทั้งหมด |
| `docs/08-workflow-responsibilities-th.md` | แบ่งหน้าที่ Codex/OpenCode/LLM/ML |
| `runtime/README-TH.md` | คู่มือใช้งาน runtime prototype |
| `reports/progress/current-status-th.md` | สถานะล่าสุดของ ML |

## ลำดับที่ฝั่ง LLM ควรทำ

1. รับ target และผล scan จาก scanner
2. เรียก feature extractor ให้ได้ JSON feature
3. เรียก `scripts/predict_prototype.py`
4. อ่าน `gate.decision`
5. ถ้า `no_exploit` ให้บอกผู้ใช้ว่าไม่ควรยิงตอนนี้ และเสนอ scan เพิ่มถ้าหลักฐานน้อย
6. ถ้า `low_confidence` ให้ส่งเข้า agentic/manual triage
7. ถ้า `likely_exploitable` ให้อ่าน `ranker.top_families`
8. ถ้า `ranker.decision=known_family_ready` ให้แนะนำ safe Metasploit check/manual probe
9. ห้ามยิง exploit จริงอัตโนมัติ ต้องให้ user ยืนยันก่อน
10. เก็บผล postcheck กลับ dataset เป็น feedback

## ทำไมไม่ให้ LLM อ่าน raw แล้วตัดสินเอง

เพราะ raw scanner output มี noise เยอะและแต่ละ tool เขียนไม่เหมือนกัน

ML ต้องการตัวเลขที่เทียบกันได้ เช่น:

```text
lua_available = 1
auth_required = 0
velocity_enabled = 1
method_put_allowed = 0
```

ดังนั้นทุก target ต้องผ่าน feature extractor ก่อน เพื่อให้ model เปรียบเทียบกับ pattern ที่เรียนมาได้

LLM มีหน้าที่:

```text
อธิบายผล
วางแผน scan เพิ่ม
จัดการ unknown/low confidence
เลือก safe verification
เขียน report
คุม session/co-op
```

ML มีหน้าที่:

```text
ตัดสิน exploitability
จัดอันดับ family
ให้คะแนน/ความมั่นใจจาก feature
```
