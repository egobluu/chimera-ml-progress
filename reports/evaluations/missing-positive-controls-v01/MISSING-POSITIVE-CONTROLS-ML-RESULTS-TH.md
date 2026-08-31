# ผล ML หลังรวม Missing Positive Controls v01

## สรุปสั้น

รอบนี้นำผล `dec-missing-positive-controls-2026-09-01` มา merge ต่อจาก Clean Control Labs v02 โดยเพิ่ม positive controls ที่ขาดอยู่ 3 targets

ผลสำคัญ: profile ใหม่ `precondition_only` ทำงานดีกว่า `strict_precheck` ชัดเจน แต่ยังไม่ถึงเกณฑ์หยุดงาน ML core

## ข้อมูลที่นำเข้า

| รายการ | จำนวน |
| --- | ---: |
| base targets | 49 |
| appended new targets | 3 |
| total targets หลัง merge | 52 |
| features หลัง merge | 92 |
| skipped inconsistent records | 0 |
| skipped disallowed target records | 0 |

targets ใหม่ที่เพิ่ม:

- `solr_velocity_positive`
- `thinkphp_invokefunction_positive`
- `couchdb_admin_party_positive`

หมายเหตุ: ไฟล์ top-level `merged-missing-positive-features.jsonl` มีข้อมูล ThinkPHP เก่าที่ขัดกับไฟล์ราย target จึงใช้ไฟล์ราย target `raw-curated/*/targeted-missing-positive-features.jsonl` เป็น source หลักแทน

## ผลเทรน

| Profile | Features | Threshold | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_v02 | 92 | 0.20 | 0.885 | 0.813 | 1.000 | 0.897 | 26 | 6 | 20 | 0 |
| strict_precheck | 86 | 0.15 | 0.519 | 0.510 | 1.000 | 0.675 | 26 | 25 | 1 | 0 |
| strict_no_negative_count | 91 | 0.15 | 0.519 | 0.510 | 1.000 | 0.675 | 26 | 25 | 1 | 0 |
| precondition_only | 38 | 0.30 | 0.731 | 0.650 | 1.000 | 0.788 | 26 | 14 | 12 | 0 |
| scanner_only | 32 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 26 | 26 | 0 | 0 |
| no_metasploit | 88 | 0.20 | 0.885 | 0.813 | 1.000 | 0.897 | 26 | 6 | 20 | 0 |
| no_nuclei_confirm | 91 | 0.20 | 0.885 | 0.813 | 1.000 | 0.897 | 26 | 6 | 20 | 0 |

## Threshold Sweep ของ precondition_only

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 26 | 26 | 0 | 0 | 0.500 | 1.000 | 0.667 |
| 0.15 | 26 | 26 | 0 | 0 | 0.500 | 1.000 | 0.667 |
| 0.20 | 26 | 25 | 1 | 0 | 0.510 | 1.000 | 0.675 |
| 0.25 | 26 | 16 | 10 | 0 | 0.619 | 1.000 | 0.765 |
| 0.30 | 26 | 14 | 12 | 0 | 0.650 | 1.000 | 0.788 |
| 0.35 | 25 | 14 | 12 | 1 | 0.641 | 0.962 | 0.769 |
| 0.45 | 25 | 13 | 13 | 1 | 0.658 | 0.962 | 0.781 |
| 0.60 | 20 | 12 | 14 | 6 | 0.625 | 0.769 | 0.690 |
| 0.70 | 2 | 1 | 25 | 24 | 0.667 | 0.077 | 0.138 |

## แปลผล

การเพิ่ม positive controls ทำให้เห็นทิศทางที่ถูกต้อง:

- `strict_precheck` ยังปน feature กว้าง/fingerprint มากเกินไป
- `precondition_only` ที่ใช้เฉพาะเงื่อนไข exploit จริง ทำงานดีกว่า
- FP ลดจาก 25 เหลือ 14 โดย FN ยังเป็น 0

นี่เป็นสัญญาณว่า ML เริ่มเรียนจาก feature ที่มีความหมายจริงแล้ว แต่ยังไม่พอหยุด เพราะ FP ยังเกินเป้าหมาย

## สถานะความพร้อม

ยังไม่ควรหยุดงาน ML core

ใกล้ขึ้น แต่ยังไม่ถึงเกณฑ์:

| Metric | ตอนนี้ | เป้าหมายหยุด |
| --- | ---: | ---: |
| FP | 14 | <= 5 |
| FN | 0 | <= 2 |
| F1 | 0.788 | >= 0.80 |

## งานต่อไป

ควรทำต่อ 2 ทางพร้อมกัน:

1. เพิ่ม clean negative controls ให้คู่กับ positive controls ที่เพิ่งเพิ่ม โดยเฉพาะ Solr/ThinkPHP/CouchDB ซ้ำอีกหลาย variation
2. ใช้ `precondition_only` เป็น candidate profile หลักแทน `strict_precheck` สำหรับการวัด readiness รอบถัดไป

ตอนนี้เป้าหมายไม่ใช่เพิ่ม scanner เยอะขึ้น แต่คือเพิ่ม target pairs ที่มี precondition signal ชัดเจนกว่าเดิม

