# Codex Review: Unseen Validation v01

## สรุปสั้น

ผล `dec-unseen-validation-v01-2026-09-01` เป็นการทดสอบแบบโลกจริงรอบแรกของ ML runtime prototype เพราะโมเดลต้อง predict ก่อน แล้วค่อยใช้ Metasploit/manual/scanner evidence เป็นเฉลยทีหลัง

ผลรวม:

| ส่วน | ผล |
| --- | ---: |
| total targets | 10 |
| Gate accuracy | 60% |
| Gate TP | 4 |
| Gate FP | 4 |
| Gate TN | 2 |
| Gate FN | 0 |
| Ranker Top-1 | 100% (4/4) |
| Unknown rejection | 100% (3/3) |
| safe to merge later | 10/10 |

## แปลผลแบบไม่หลอกตัวเอง

### สิ่งที่ดี

Ranker ทำงานดีมากกับ known-family variants:

- `unseen_redis_variant_01` -> `redis`
- `unseen_tomcat_put_variant_01` -> `tomcat_put`
- `unseen_solr_variant_01` -> `solr_velocity`
- `unseen_grafana_variant_01` -> `grafana`

Unknown guard ก็ทำงานดี:

- Jetty/Drupal/Laravel ถูกส่งเป็น `unknown_family`
- ไม่ถูกฟันธงเป็น known family แบบมั่ว

### สิ่งที่ยังต้องแก้

Gate ยังเปิดกว้างเกินไป:

- unknown-family ทั้ง 3 ตัวถูก Gate มองเป็น `likely_exploitable`
- patched nginx 1 ตัวถูก Gate มองเป็น `likely_exploitable`

สาเหตุหลักคือ Gate ยังให้น้ำหนักกับ generic HTTP/precondition signal มากไป เช่น `is_http_target` และ `endpoint_reachable_count` โดยยังไม่มี unknown-product negative signal มาช่วยกดคะแนน

## ข้อสรุปด้านสถาปัตยกรรม

ผลนี้ยืนยันว่าระบบไม่ควรใช้ Gate อย่างเดียว

ควรใช้ flow รวม:

```text
Gate
-> Ranker
-> Unknown Guard
-> Final Decision Router
```

เพราะถึง Gate จะ FP กับ unknown target แต่ Ranker/Unknown Guard ยังช่วยดึงกลับมาเป็น `unknown_family_triage` ได้

## การปรับ runtime ที่ทำเพิ่ม

ปรับ `scripts/predict_prototype.py` ให้มี `final_decision`

ค่า output ใหม่:

| final_decision | ความหมาย |
| --- | --- |
| `do_not_exploit_now` | Gate บอก `no_exploit` |
| `needs_more_evidence` | Gate หรือระบบยังไม่มั่นใจ |
| `ready_for_safe_verification` | Gate ผ่าน และ Ranker เห็น known family ชัด |
| `manual_triage_before_exploit` | มี family candidate แต่มี negative/blocked signal |
| `unknown_family_triage` | น่าสงสัย แต่ไม่อยู่ใน family ที่รู้จักหรือ evidence ไม่พอ |

ค่านี้สำคัญสำหรับฝั่ง LLM/agentic เพราะไม่ต้องเดาเองจากหลาย field

## งาน ML ถัดไป

ควรทำ Gate Improvement v02:

1. เพิ่ม feature กลุ่ม unknown/out-of-scope product เช่น `unknown_product_detected`, `known_family_signal_count`
2. ลดน้ำหนัก generic HTTP signal ที่ทำให้ unknown target กลายเป็น `likely_exploitable`
3. เพิ่ม negative examples ที่เป็น HTTP vulnerable แต่ไม่อยู่ใน candidate family
4. เทียบผลกับ unseen v01 โดยห้ามลบผล baseline เดิม
5. ถ้า candidate model ลด FP โดยไม่เพิ่ม FN ค่อย promote

## สถานะความพร้อมหลัง unseen v01

| ส่วน | สถานะ |
| --- | --- |
| Gate | ยังต้องปรับ FP |
| Ranker | ผ่าน unseen known-family prototype |
| Unknown Guard | ผ่าน unseen unknown-family prototype |
| Runtime handoff | ใช้ต่อกับ LLM ได้ดีขึ้นหลังเพิ่ม `final_decision` |

สรุป:

```text
Ranker และ Unknown Guard พร้อมใช้ระดับ prototype
Gate ยังเป็น bottleneck หลักของ ML รอบถัดไป
```
