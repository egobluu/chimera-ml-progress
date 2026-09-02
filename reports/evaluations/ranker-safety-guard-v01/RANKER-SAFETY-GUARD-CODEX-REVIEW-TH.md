# Codex Review: Ranker Safety Guard v01

## สรุปสั้น

รอบนี้ไม่ได้ retrain model แต่แก้ runtime decision logic เพื่อให้ระบบระวังมากขึ้นตอน Ranker เลือก exploit family

พูดแบบภาษาคน:

```text
ถ้าโมเดลจัดอันดับ family ได้ แต่คะแนนอันดับหนึ่งไม่ชนะอันดับสองชัด หรือหลักฐานเฉพาะ family ยังบางเกินไป ระบบจะไม่บอกว่าพร้อมตรวจต่อทันที แต่จะส่งไป manual triage หรือให้เก็บ evidence เพิ่มก่อน
```

ชื่อในระบบ:

- พร้อมตรวจต่อหลังเลือก family ได้แล้ว (`known_family_ready`)
- family ดูมีโอกาส แต่ยังไม่ควรเชื่อเต็มที่ (`known_family_but_blocked_or_low_confidence`)
- target อาจไม่อยู่ใน family ที่โมเดลรู้จัก (`unknown_family`)

## สิ่งที่แก้

แก้ไฟล์:

```text
scripts/predict_prototype.py
scripts/evaluate_runtime_predictions.py
```

เพิ่ม logic หลัก 3 ส่วน:

1. ดูว่าคะแนนอันดับหนึ่งชนะอันดับสองชัดไหม (`ranker_confidence`)
2. ดูว่าหลักฐานเฉพาะ family พร้อมพอไหม (`family_readiness`)
3. ถ้าไม่ผ่านข้อ 1 หรือ 2 ให้ลดผลจากพร้อมตรวจต่อ (`known_family_ready`) เป็นต้องตรวจมือก่อน (`known_family_but_blocked_or_low_confidence`)

## Ranker Confidence

ระบบจะคำนวณคะแนนห่างระหว่าง family อันดับหนึ่งกับอันดับสอง

ตัวอย่างที่ดี:

```text
อันดับ 1 redis score = 2.917933
อันดับ 2 joomla score = 0.433710
margin = 2.484223
```

แบบนี้ถือว่าชนะชัด (`clear_margin`)

ถ้าคะแนนใกล้กันกว่า `0.25` จะถือว่าไม่มั่นใจ (`low_margin`) และไม่ปล่อยเป็นพร้อมตรวจต่อทันที

## Family Readiness

ระบบจะดูว่า family ที่ Ranker เลือกมีหลักฐานเฉพาะ family จริงหรือไม่

ตัวอย่าง Redis ที่พร้อม:

```text
redis_detected = 1
redis_info_accessible = 1
lua_available = 1
```

แบบนี้พร้อม เพราะมีหลักฐานเฉพาะ Redis

ตัวอย่างที่ยังบาง:

```text
version_in_vulnerable_range = 1
no_auth_required = 1
```

สองตัวนี้เป็นสัญญาณค่อนข้างทั่วไป ไม่พอให้บอกว่าเป็น Redis/Tomcat/Grafana family ใด family หนึ่งอย่างมั่นใจ

## Runtime Output ใหม่

ถ้า Ranker ทำงานแล้ว output จะมี field เพิ่ม:

```json
{
  "ranker": {
    "decision": "known_family_ready",
    "confidence": {
      "level": "clear_margin",
      "margin": 2.484223,
      "reason": "อันดับหนึ่งชนะอันดับสองชัดเจน"
    },
    "family_readiness": {
      "ready": true,
      "specific_positive_signals": [
        "lua_available",
        "redis_detected",
        "redis_info_accessible"
      ],
      "blocking_negative_signals": [],
      "reason": "มีหลักฐานเฉพาะ family เพียงพอ และไม่พบตัวบล็อกของ family นี้"
    }
  }
}
```

LLM/agent ควรอ่าน field นี้เพื่ออธิบายว่าระบบมั่นใจเพราะอะไร หรือทำไมต้องส่งให้คนตรวจมือก่อน

## Regression Result

Codex rerun runtime evaluation บน default runtime:

### Multi-family unseen validation v01

| Metric | Result |
| --- | ---: |
| Total targets | 10 |
| Gate FP/FN | 0 / 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Ranker low-margin count | 0 |
| Family not-ready count | 0 |
| Safety flow accuracy | 1.0000 |
| Strict flow accuracy | 1.0000 |

### Unseen Solr schema validation v01

| Metric | Result |
| --- | ---: |
| Total targets | 4 |
| Gate FP/FN | 0 / 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Ranker low-margin count | 0 |
| Family not-ready count | 0 |
| Safety flow accuracy | 1.0000 |
| Strict flow accuracy | 1.0000 |

## การตีความ

การแก้รอบนี้เป็น runtime safety improvement ไม่ใช่การเพิ่ม accuracy ด้วยการ train ใหม่

ผลที่ต้องการคือ:

- target ที่ feature สะอาดยังผ่านเหมือนเดิม
- target ที่ feature บางหรือคะแนน family สูสีจะถูกลดความเสี่ยง
- LLM มีข้อมูลเพิ่มสำหรับอธิบายและเลือก next action

## ข้อจำกัด

ยังต้องให้ OpenCode/Kali เก็บ validation เพิ่มเพื่อทดสอบกรณี:

- feature บางโดยตั้งใจ
- family score ใกล้กัน
- unknown-family target
- negative controls ที่มี generic positive signal แต่มี blocker เฉพาะ family

ยังไม่ควร promote เป็น production เพราะนี่เป็น guard runtime รอบแรก

## Validation ต่อจาก OpenCode

หลังจากได้ชุด `dec-ranker-guard-unknown-validation-2026-09-02` แล้ว Codex นำมาวิ่ง runtime evaluation จริงอีกครั้ง

ชุดนี้มี 24 targets:

| กลุ่ม | จำนวน |
| --- | ---: |
| Known family positive/negative | 12 |
| Unknown family positive | 6 |
| Weak/noisy no-exploit | 6 |

รอบแรกพบว่า `redis_weak_guard_01` ยังเสี่ยง เพราะมี Redis signal บางส่วนแต่ไม่มี Lua evidence และ `known_family_signal_count=0` ระบบกลับยังปล่อยเป็น `ready_for_safe_verification`

จึงเพิ่ม guard เฉพาะ weak evidence:

- Redis ไม่มี `lua_available` และไม่มี known-family signal จะถูก downgrade
- Grafana ที่ `path_traversal_blocked=1` และเข้า public plugin path ไม่ได้จะถูก downgrade
- `known_family_signal_count=0` ทำให้ `family_readiness.ready=false`

ผลหลังแก้:

| Metric | Result |
| --- | ---: |
| Gate FP/FN | 0 / 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Unknown-family rejected | 1.0000 |
| Safety flow | 1.0000 |
| Strict flow | 1.0000 |

รายงานละเอียด:

```text
reports/evaluations/ranker-guard-unknown-validation-v01/RANKER-GUARD-UNKNOWN-CODEX-REVIEW-TH.md
```
