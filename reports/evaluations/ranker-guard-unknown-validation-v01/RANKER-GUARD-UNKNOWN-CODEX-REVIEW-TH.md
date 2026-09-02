# Codex Review: Ranker Guard Unknown Validation v01

## สรุปสั้น

รอบนี้เอาผลจาก OpenCode/Kali ชุด `dec-ranker-guard-unknown-validation-2026-09-02` เข้ามาตรวจซ้ำด้วย runtime ML จริงของ repo

พูดแบบภาษาคน:

```text
เราไม่ได้แค่เชื่อรายงานว่า 24/24 safe แต่เอา feature ทั้งหมดมาวิ่งผ่าน Gate + Ranker + Guard อีกครั้ง เพื่อดูว่า runtime จะตัดสินใจปลอดภัยจริงไหมเมื่อเจอ known family, unknown family และ weak/noisy target
```

ผลหลังปรับ guard:

| Metric | Result |
| --- | ---: |
| Total targets | 24 |
| Gate TP / FP / TN / FN | 12 / 0 / 12 / 0 |
| Gate accuracy | 1.0000 |
| Known-positive Ranker Top-1 | 6/6 |
| Unknown-family rejected | 6/6 |
| Safety flow accuracy | 1.0000 |
| Strict flow accuracy | 1.0000 |

## ไฟล์ที่เอาเข้า

คัดเฉพาะไฟล์ผลลัพธ์ระดับบนเข้ามา ไม่ copy raw evidence folders:

```text
reports/evaluations/ranker-guard-unknown-validation-v01/features.jsonl
reports/evaluations/ranker-guard-unknown-validation-v01/targets.jsonl
reports/evaluations/ranker-guard-unknown-validation-v01/validation-results.jsonl
reports/evaluations/ranker-guard-unknown-validation-v01/safe-to-merge-targets.txt
reports/evaluations/ranker-guard-unknown-validation-v01/quarantined-targets.txt
reports/evaluations/ranker-guard-unknown-validation-v01/runtime-targets.jsonl
```

ตัวที่ใช้ให้ runtime อ่านจริงคือ `runtime-targets.jsonl` เพราะ OpenCode ใช้ชื่อ family บางตัวไม่ตรงกับชื่อ canonical ของ model

## การ map label

ชื่อที่มนุษย์ใช้ใน report บางอันเป็นชื่อ exploit scenario แต่ model ใช้ชื่อ family กลาง

ตัวอย่าง:

| Source label | Runtime family |
| --- | --- |
| `redis_lua` | `redis` |
| `grafana_path_traversal` | `grafana` |
| `solr_velocity_rce` | `solr_velocity` |
| `couchdb_rce` | `couchdb_auth` |

ส่วน target ที่เป็น Drupal, Laravel, Jetty, WordPress, PHP-CGI, JBoss ถูกตั้งเป็นกลุ่ม `unknown_family` เพราะยังไม่ใช่ family ที่ Ranker รุ่นนี้ train ให้เลือก

## ความหมายของกลุ่มทดสอบ

Known family คือ target ที่อยู่ใน family ที่ model รู้จักแล้ว เช่น Redis, Grafana, Solr, Tomcat, CouchDB

Unknown family คือ target ที่มี exploit จริง แต่ไม่อยู่ใน family ที่ Ranker รู้จัก เช่น Drupal หรือ Laravel เป้าหมายไม่ใช่ให้ Ranker ทายถูก แต่ให้ระบบไม่ฝืนเลือก family ผิดแล้วส่งไปยิง

Weak/noisy คือ target ที่มีสัญญาณบางส่วนเหมือนช่องโหว่ แต่หลักฐานยังไม่พอหรือมีตัวบล็อก เป้าหมายคือระบบต้องไม่ปล่อยเป็น `ready_for_safe_verification`

## สิ่งที่เจอตอน runtime แรก

ก่อนปรับ guard เพิ่ม Runtime เจอปัญหาจริง 1 จุด:

```text
redis_weak_guard_01 ถูก Gate มองว่า likely_exploitable และ final_decision เป็น ready_for_safe_verification
```

พูดง่าย ๆ คือ Redis weak target มี Redis service และ info endpoint พอให้ดูคล้าย Redis แต่ไม่มีหลักฐานสำคัญของ exploit path:

```text
lua_available = 0
known_family_signal_count = 0
```

ดังนั้นการปล่อยเป็นพร้อมตรวจ exploit ต่อถือว่าเสี่ยงเกินไป

Grafana weak ก็มี Gate positive ในรอบแรก แต่ final flow ยังไม่ปล่อยไปยิง เพราะ guard เดิมลดเป็น manual triage ได้แล้ว

## สิ่งที่แก้

แก้ใน runtime ไม่ได้ retrain model:

```text
scripts/predict_prototype.py
scripts/evaluate_runtime_predictions.py
```

เพิ่มกฎอ่านง่าย ๆ:

ถ้าเป็น Redis แต่ไม่มี Lua และ scanner บอกว่าสัญญาณ known-family ไม่พอ ให้ลดความมั่นใจทันที

ชื่อในระบบ:

```text
redis_detected > 0
lua_available <= 0
known_family_signal_count <= 0
```

ถ้าเป็น Grafana แต่ path traversal ถูก block และเข้า public plugin path ไม่ได้ ให้ลดความมั่นใจทันที

ชื่อในระบบ:

```text
grafana_detected > 0
path_traversal_blocked > 0
public_plugin_path_accessible <= 0
```

และถ้า feature บอกชัดว่า known-family signal ยังเป็น 0 ระบบจะถือว่า family ที่ Ranker เลือกยังไม่พร้อม

ชื่อในระบบ:

```text
family_readiness.ready = false
```

## ผลหลังแก้

ผล runtime evaluation หลัง guard ใหม่:

| ส่วน | ผล |
| --- | ---: |
| Known family positives | 6/6 ready ถูกต้อง |
| Known family negatives | 6/6 ไม่ถูกปล่อยเป็น exploit |
| Unknown-family positives | 6/6 ถูกส่งไป unknown triage |
| Weak/noisy targets | 6/6 ไม่ถูกปล่อยเป็น exploit |

ตัวเลข confusion matrix ของ Gate:

| Metric | Count |
| --- | ---: |
| TP | 12 |
| FP | 0 |
| TN | 12 |
| FN | 0 |

แปลภาษาคน:

- เจอของที่ควรเป็น exploit ได้ครบ (`TP = 12`)
- ไม่มี negative/weak ตัวไหนถูกมองเป็น exploit หลังแก้ (`FP = 0`)
- กัน target ที่ไม่ควร exploit ได้ครบ (`TN = 12`)
- ไม่มี positive ตัวไหนหลุดเป็น negative (`FN = 0`)

## การตีความ

รอบนี้สำคัญกว่ารอบ multi-family ก่อน เพราะมีทั้ง unknown-family และ weak/noisy target

สิ่งที่พูดได้:

```text
Ranker guard รุ่นล่าสุดกัน unknown-family และ weak/noisy cases ใน validation ชุดนี้ได้ครบ
```

สิ่งที่ยังไม่ควรพูด:

```text
production-ready 100%
```

เหตุผลคือยังเป็น validation set ที่ควบคุมเอง จำนวน 24 targets และยังไม่ได้ทดสอบกับ traffic/targets จริงแบบหลากหลายมากพอ

## คำแนะนำต่อ

ยังไม่ควรเอา 24 targets นี้ไป train ทับทันที เพราะรอบนี้มีหน้าที่เป็น validation/regression set

ควรทำต่อแบบนี้:

1. เก็บชุดนี้เป็น regression guard set
2. sync runtime script ที่แก้แล้วไป repo scanner/dataset
3. เพิ่ม integration doc ให้ LLM/agent อ่าน output ใหม่ เช่น `ranker.confidence`, `family_readiness`, `final_decision`
4. รอบถัดไปค่อยทำ scanner-to-ML integration test จาก feature extractor จริง ไม่ใช่ JSONL ที่ curated แล้วเท่านั้น

