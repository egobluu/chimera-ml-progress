# Codex Review: Unseen Solr Schema Validation v01

## สรุปสั้น

รอบ `dec-unseen-solr-schema-validation-2026-09-02` เป็นการทดสอบ Solr ใหม่หลังแก้ feature extractor/probe schema แล้ว โดยยังไม่เอา 4 targets นี้เข้า train ก่อน

ผลคือผ่านตามที่ต้องการ:

- Solr positive ใหม่ 2/2 ผ่าน
- Solr negative ใหม่ 2/2 ผ่าน
- quarantine 0
- runtime prediction แยก positive/negative ได้ถูกใน scope Solr

## ทำไมรอบนี้สำคัญ

ก่อนหน้านี้ `solr_velocity_new_01` ใน honest v04 พลาด เพราะ feature ที่ส่งเข้า runtime เหมือน Velocity ไม่พร้อม:

```text
velocity_endpoint_found = 0
velocity_template_accessible = 0
```

รอบนี้จึงไม่ได้เริ่มจาก train เพิ่ม แต่เริ่มจากพิสูจน์ว่า extractor ใหม่ส่ง field สำคัญถูกหรือไม่

## Targets

| Target | Category | Expected family | Result |
| --- | --- | --- | --- |
| `solr_positive_unseen_01` | positive | `solr_velocity` | safe_to_merge |
| `solr_positive_unseen_02` | positive | `solr_velocity` | safe_to_merge |
| `solr_negative_unseen_01` | negative | none | safe_to_merge |
| `solr_negative_unseen_02` | negative | none | safe_to_merge |

## Runtime Evaluation

Codex รัน evaluation 2 แบบ:

1. default runtime ปัจจุบัน พร้อม Solr blocker guard
2. runtime รุ่นทดลองจาก Solr schema fix

ผลทั้งสองแบบเท่ากัน:

| Metric | Result |
| --- | ---: |
| Total targets | 4 |
| Gate accuracy | 1.0000 |
| Gate FP | 0 |
| Gate FN | 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Safety flow accuracy | 1.0000 |
| Strict flow accuracy | 1.0000 |

## วิธีอ่านผล

สำหรับ positive:

```text
gate_decision = likely_exploitable
predicted_top_family = solr_velocity
final_decision = ready_for_safe_verification
```

สำหรับ negative:

```text
gate_decision = low_confidence
final_decision = needs_more_evidence
```

แปลว่า runtime ไม่ปล่อย Solr negative ที่ `velocity_disabled=1` ไปถึง exploit verification อัตโนมัติ

## ข้อจำกัด

ตัวเลข 1.0000 รอบนี้ไม่ใช่ proof ว่า model แม่น 100% ทั้งระบบ เพราะเป็น Solr-only unseen validation 4 targets

ความหมายที่พูดได้อย่างซื่อ ๆ คือ:

```text
Solr feature extractor/probe schema ใหม่ใช้งานได้ในระดับ prototype และแก้ปัญหา Solr positive/negative ที่เคยปนกันได้
```

## Merge Decision

ข้อมูล 4 targets นี้ควรเก็บไว้เป็น unseen validation result ก่อน ยังไม่ควรเอาเข้า train ทันที เพราะถ้าเอาเข้า train แล้วจะเสียสถานะ unseen

ถ้าต้องการ retrain รอบหน้า ให้ทำหลังจากมี unseen validation ครอบคลุม family อื่นด้วย เช่น Tomcat, Redis, Grafana, CouchDB

## งานถัดไป

1. เก็บ unseen validation แบบเดียวกันกับ family อื่น 2-3 family
2. แยกชุด `validation-only` กับ `train-safe` ให้ชัด
3. ค่อย retrain หลังมี unseen evidence หลาย family ไม่ใช่เฉพาะ Solr
4. ถ้าจะ promote runtime ให้ใช้เกณฑ์ทั้งระบบ ไม่ใช้ Solr-only score

