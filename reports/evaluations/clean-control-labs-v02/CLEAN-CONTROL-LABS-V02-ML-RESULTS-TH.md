# ผล ML หลังรวม Clean Control Labs v02

## สรุปสั้น

รอบนี้นำผล `dec-clean-control-labs-2026-09-01` รุ่น Precondition Focus มา merge ใหม่ โดยเพิ่ม target ใหม่เข้า dataset จริง 9 targets

ผลสำคัญคือ dataset เริ่มยากและสมจริงขึ้น คะแนน `full_v02` ลดลงจาก 1.000 เหลือ 0.8846 ส่วน `strict_precheck` ยังไม่ผ่าน

## ข้อมูลที่นำเข้า

| รายการ | จำนวน |
| --- | ---: |
| base targets | 40 |
| appended new targets | 9 |
| total targets หลัง merge | 49 |
| features หลัง merge | 90 |
| skipped inconsistent records | 0 |
| skipped disallowed target records | 74 |

targets ใหม่ที่เพิ่ม:

- `tomcat_put_positive`
- `tomcat_put_negative`
- `tomcat_ajp_positive`
- `tomcat_ajp_negative`
- `shiro_default_key_positive`
- `shiro_default_key_negative`
- `solr_velocity_negative`
- `thinkphp_rce_negative`
- `couchdb_auth_required_clean`

clean pairs ที่ได้ครบ:

- Tomcat PUT: PUT allowed เทียบกับ PUT rejected
- Tomcat AJP: AJP open เทียบกับ AJP closed
- Shiro Key: default key likely เทียบกับ unlikely

ยังขาดคู่ positive/negative ที่สะอาด:

- Solr Velocity positive
- ThinkPHP RCE positive
- CouchDB admin-party positive

## ผลเทรน

| Profile | Features | Threshold | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_v02 | 90 | 0.20 | 0.878 | 0.793 | 1.000 | 0.885 | 23 | 6 | 20 | 0 |
| strict_precheck | 84 | 0.15 | 0.490 | 0.479 | 1.000 | 0.648 | 23 | 25 | 1 | 0 |
| strict_no_negative_count | 89 | 0.15 | 0.490 | 0.479 | 1.000 | 0.648 | 23 | 25 | 1 | 0 |
| scanner_only | 32 | 0.10 | 0.469 | 0.469 | 1.000 | 0.639 | 23 | 26 | 0 | 0 |
| no_metasploit | 86 | 0.20 | 0.878 | 0.793 | 1.000 | 0.885 | 23 | 6 | 20 | 0 |
| no_nuclei_confirm | 89 | 0.20 | 0.878 | 0.793 | 1.000 | 0.885 | 23 | 6 | 20 | 0 |

## Threshold Sweep ของ strict_precheck

| Threshold | TP | FP | TN | FN | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 23 | 26 | 0 | 0 | 0.469 | 1.000 | 0.639 |
| 0.15 | 23 | 25 | 1 | 0 | 0.479 | 1.000 | 0.648 |
| 0.20 | 20 | 24 | 2 | 3 | 0.455 | 0.870 | 0.597 |
| 0.30 | 17 | 17 | 9 | 6 | 0.500 | 0.739 | 0.596 |
| 0.40 | 13 | 15 | 11 | 10 | 0.464 | 0.565 | 0.510 |
| 0.50 | 13 | 5 | 21 | 10 | 0.722 | 0.565 | 0.634 |
| 0.60 | 13 | 1 | 25 | 10 | 0.929 | 0.565 | 0.703 |
| 0.70 | 13 | 0 | 26 | 10 | 1.000 | 0.565 | 0.722 |
| 0.80 | 9 | 0 | 26 | 14 | 1.000 | 0.391 | 0.562 |
| 0.90 | 0 | 0 | 26 | 23 | 0.000 | 0.000 | 0.000 |

## แปลผล

`strict_precheck` ยังไม่พร้อมใช้งานจริง เพราะถ้าเลือก threshold ต่ำเพื่อไม่ให้พลาด positive โมเดลจะ false positive เยอะมาก

ถ้าดัน threshold ไป `0.60-0.70` จะลด false positive ได้ดี แต่ false negative สูงถึง 10 targets แปลว่าพลาดช่องโหว่จริงมากเกินไป

อย่างไรก็ตาม รอบนี้มีสัญญาณที่ดี:

- คะแนน full profile ไม่ 1.000 แล้ว แปลว่า test เริ่มไม่ง่ายหลอกตัวเอง
- มี clean pairs เพิ่มหลาย family
- ML เริ่มถูกทดสอบกับ target ใหม่ที่ยากขึ้น

## จุดที่พลาดใน target ใหม่

ที่ threshold 0.15 target negative ใหม่ยังถูกมองเป็น exploit หลายตัว เช่น:

- `couchdb_auth_required_clean`
- `shiro_default_key_negative`
- `solr_velocity_negative`
- `thinkphp_rce_negative`
- `tomcat_ajp_negative`
- `tomcat_put_negative`

แปลว่าโมเดลยังไม่ให้ค่าน้ำหนักกับ precondition-negative features มากพอ

## ข้อสรุป

ยังไม่ควรหยุดงาน ML core

รอบถัดไปควรทำ 2 อย่าง:

1. เพิ่ม clean positive ให้สมดุลกับ negative control ที่เพิ่มมา โดยเฉพาะ `solr_velocity_positive`, `thinkphp_rce_positive`, `couchdb_admin_party_positive`
2. ปรับ training profile ให้เน้น `precondition_*` มากขึ้น และแยก fingerprint features ออกจาก strict profile ให้ชัด

เกณฑ์หยุดยังเหมือนเดิม:

| Metric | เป้าหมาย |
| --- | ---: |
| strict_precheck FP | <= 5 |
| strict_precheck FN | <= 2 |
| strict_precheck F1 | >= 0.80 |

