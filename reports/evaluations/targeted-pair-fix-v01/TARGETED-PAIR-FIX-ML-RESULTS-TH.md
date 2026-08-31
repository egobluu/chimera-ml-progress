# ผล ML หลังรวม Targeted Pair Fix v01

## สรุปสั้น

รอบนี้นำผล `dec-targeted-pair-fix-2026-08-31` มารวมกับ dataset เดิม โดยใช้เฉพาะ record ที่มี `label_consistency=consistent` เท่านั้น

ผลคือข้อมูลสะอาดขึ้น แต่ `strict_precheck` ยังไม่ดีพอสำหรับใช้งานจริง เพราะยังมี false positive สูงมาก

## ข้อมูลที่นำเข้า

| รายการ | จำนวน |
| --- | ---: |
| base targets | 40 |
| targets ที่มี pair-fix feature ใช้ได้ | 3 |
| records ที่ถูก skip เพราะ inconsistent | 11 |
| features หลัง merge | 79 |

targets ที่ใช้ได้จาก pair-fix:

- `shiro_CVE-2016-4437` - พบ `rememberme_deleteMe_seen`
- `solr_CVE-2019-17558` - พบ `solr_core_found` และ `velocity_enabled`
- `redis_non_vulnerable` - พบ `auth_required` และข้อมูล version/auth behavior

targets ที่ยังไม่ควรนำเข้า train:

- `thinkphp_5-rce`
- `couchdb_CVE-2017-12635`
- `nginx_CVE-2017-7529`
- `redis_auth_non_vulnerable`

เหตุผล: label กับ evidence ยังขัดกัน ถ้าเอาเข้า train จะทำให้โมเดลเรียนรู้ผิด

## ผลเทรน

| Profile | Features | Threshold | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_v02 | 79 | 0.20 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |
| strict_precheck | 73 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| strict_no_negative_count | 78 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| scanner_only | 32 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| no_metasploit | 75 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |
| no_nuclei_confirm | 78 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |

## อ่านผลยังไง

`full_v02`, `no_metasploit`, และ `no_nuclei_confirm` ยังให้คะแนนดีเกินไป เพราะยังมี feature ที่ใกล้กับคำเฉลยหรือเกิดหลังตรวจ exploit แล้ว จึงใช้เป็น smoke test ได้ แต่ยังไม่ควรใช้เป็นหลักฐานว่าโมเดลใช้งานจริงได้

profile ที่ควรดูสำหรับงานจริงตอนนี้คือ `strict_precheck`

ผลของ `strict_precheck`:

- จับ positive ได้ครบ 20 ตัว
- แต่ทำนาย negative ผิดครบ 20 ตัว
- แปลว่าโมเดลยังมีนิสัย "ยิงไว้ก่อน" เพราะข้อมูลฝั่ง precheck ยังแยก no-exploit ไม่ชัดพอ

## Threshold Sweep ของ strict_precheck

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 20 | 20 | 0 | 0 | 0.500 | 1.000 | 0.667 |
| 0.20 | 16 | 20 | 0 | 4 | 0.444 | 0.800 | 0.571 |
| 0.30 | 13 | 17 | 3 | 7 | 0.433 | 0.650 | 0.520 |
| 0.40 | 13 | 6 | 14 | 7 | 0.684 | 0.650 | 0.667 |
| 0.50 | 13 | 4 | 16 | 7 | 0.765 | 0.650 | 0.703 |
| 0.60 | 13 | 3 | 17 | 7 | 0.812 | 0.650 | 0.722 |
| 0.70 | 10 | 3 | 17 | 10 | 0.769 | 0.500 | 0.606 |
| 0.80 | 4 | 1 | 19 | 16 | 0.800 | 0.200 | 0.320 |
| 0.90 | 0 | 0 | 20 | 20 | 0.000 | 0.000 | 0.000 |

สรุป: ถ้าใช้ threshold ต่ำ จะไม่พลาด positive แต่ยิงผิดเยอะ ถ้าใช้ threshold สูง จะลดการยิงผิดได้ แต่เริ่มพลาดช่องโหว่จริง

## ข้อสรุป

Targeted Pair Fix รอบนี้ช่วยด้านคุณภาพข้อมูล แต่จำนวน target ที่ consistent ยังน้อยเกินไป จึงยังไม่พอให้ `strict_precheck` ดีขึ้นชัดเจน

งานต่อไปควรไม่ใช่การสแกนกว้างเพิ่มทันที แต่ควรแก้ label consistency ก่อน:

1. quarantine target ที่ label/evidence ขัดกัน
2. แก้หรือเปลี่ยน lab ที่ไม่ตรง CVE
3. เก็บ positive/negative pair ต่อ family ให้ครบ
4. train เฉพาะ dataset ที่ label consistency ผ่าน

