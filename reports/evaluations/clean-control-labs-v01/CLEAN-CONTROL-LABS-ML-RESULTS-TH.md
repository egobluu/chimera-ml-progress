# ผล ML หลังรวม Clean Control Labs v01

## สรุปสั้น

รอบนี้นำผล `dec-clean-control-labs-2026-09-01` มา merge และ train ใหม่ โดยเพิ่ม target ใหม่เข้า dataset จริง ไม่ใช่แค่เพิ่ม feature ให้ target เดิม

ผลคือ dataset เพิ่มจาก 40 เป็น 42 targets แต่ `strict_precheck` ยังไม่ผ่านเกณฑ์ใช้งานจริง

## ข้อมูลที่นำเข้า

| รายการ | จำนวน |
| --- | ---: |
| base targets | 40 |
| appended new targets | 2 |
| total targets หลัง merge | 42 |
| features หลัง merge | 90 |
| skipped inconsistent records | 1 |
| skipped disallowed target records | 63 |

targets ที่เพิ่มเข้า train:

- `couchdb_admin_party_clean` - positive/control สำหรับ CouchDB admin party
- `couchdb_auth_required_clean` - negative/control สำหรับ CouchDB auth-required

หมายเหตุ: ไฟล์ summary จาก Kali ระบุว่า CouchDB มี clean pair 2 targets แต่ `safe-to-merge-targets.txt` มีแค่ `couchdb_auth_required_clean` และ audit mark `couchdb_admin_party_clean` เป็น inconclusive เพราะ version feature ไม่ชัดเจน รอบนี้จึง merge เฉพาะ records ราย feature ที่ `label_consistency=consistent` และข้าม record ที่ inconclusive

## ผลเทรน

| Profile | Features | Threshold | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_v02 | 90 | 0.20 | 0.976 | 0.955 | 1.000 | 0.977 | 21 | 1 | 20 | 0 |
| strict_precheck | 84 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 21 | 21 | 0 | 0 |
| strict_no_negative_count | 89 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 21 | 21 | 0 | 0 |
| scanner_only | 32 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 21 | 21 | 0 | 0 |
| no_metasploit | 86 | 0.20 | 0.976 | 0.955 | 1.000 | 0.977 | 21 | 1 | 20 | 0 |
| no_nuclei_confirm | 89 | 0.15 | 0.976 | 0.955 | 1.000 | 0.977 | 21 | 1 | 20 | 0 |

## Threshold Sweep ของ strict_precheck

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 21 | 21 | 0 | 0 | 0.500 | 1.000 | 0.667 |
| 0.20 | 16 | 21 | 0 | 5 | 0.432 | 0.762 | 0.552 |
| 0.30 | 13 | 19 | 2 | 8 | 0.406 | 0.619 | 0.491 |
| 0.40 | 13 | 10 | 11 | 8 | 0.565 | 0.619 | 0.591 |
| 0.50 | 13 | 5 | 16 | 8 | 0.722 | 0.619 | 0.667 |
| 0.60 | 13 | 3 | 18 | 8 | 0.812 | 0.619 | 0.703 |
| 0.70 | 10 | 3 | 18 | 11 | 0.769 | 0.476 | 0.588 |
| 0.80 | 4 | 1 | 20 | 17 | 0.800 | 0.190 | 0.308 |
| 0.90 | 0 | 1 | 20 | 21 | 0.000 | 0.000 | 0.000 |

## จุดที่ยังพลาด

target ใหม่ `couchdb_auth_required_clean` เป็น negative แต่ถูกทำนายเป็น exploit:

| Profile | Probability | Result |
| --- | ---: | --- |
| full_v02 | 0.8776 | false positive |
| strict_precheck | 0.5727 | false positive |

แปลว่าโมเดลยังไม่เข้าใจ pattern ว่า `auth_required=1` และ `config_blocked=1` ควรลดโอกาส exploit สำหรับ CouchDB เพราะตัวอย่าง clean control ยังน้อยเกินไป

## แปลผล

รอบนี้ถือว่าสำเร็จด้าน dataset pipeline เพราะ:

- เพิ่ม target ใหม่เข้า CSV ได้จริง
- มี clean CouchDB pair ชุดแรก
- ตรวจพบว่าโมเดลยังพลาดกับ negative control ใหม่

แต่ยังไม่สำเร็จด้าน ML readiness เพราะ:

- `strict_precheck` ยัง FP=21 จาก 21 negative
- threshold สูงช่วยลด FP ได้ แต่เพิ่ม FN มากเกินไป
- ยังมี clean pair แค่ family เดียว

## ควรทำต่ออะไร

รอบถัดไปควรเลิกพึ่ง fingerprint จาก `whatweb` เป็นตัวตัดสิน consistency แล้วแยก `fingerprint_consistency` ออกจาก `precondition_consistency`

ควรให้ OpenCode ทำ custom/lightweight control labs เพิ่มสำหรับ family เหล่านี้:

- Tomcat PUT positive/negative
- Tomcat AJP positive/negative
- Solr Velocity positive/negative
- Shiro default-key positive/negative
- ThinkPHP invokefunction positive/negative

เป้าหมายก่อนหยุด ML core:

| Metric | เป้าหมาย |
| --- | ---: |
| clean families | >= 4 |
| clean targets | >= 50 |
| strict_precheck FP | <= 5 |
| strict_precheck FN | <= 2 |
| strict_precheck F1 | >= 0.80 |

