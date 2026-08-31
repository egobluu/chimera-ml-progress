# ผล ML หลังรวม Label Consistency Fix v01

## สรุปสั้น

รอบนี้นำผล `dec-label-consistency-fix-2026-08-31` มาใช้ต่อ โดย merge เฉพาะ target ที่ safe to merge คือ `tomcat_CVE-2020-1938`

ผลคะแนน `strict_precheck` ยังไม่ดีขึ้น แต่รอบนี้สำคัญมากเพราะช่วยยืนยันว่า target หลายตัวใน dataset เดิมยังไม่ควรใช้ train

## ข้อมูลจาก Kali/OpenCode

| รายการ | จำนวน |
| --- | ---: |
| targets ที่ตรวจ | 6 |
| safe to merge | 1 |
| quarantined | 5 |
| feature records จาก scan | 36 |

safe to merge:

- `tomcat_CVE-2020-1938`

quarantined:

- `tomcat_CVE-2017-12615` - PUT exploit condition ไม่ reproducible
- `solr_non_vulnerable` - Velocity enabled เหมือน positive
- `shiro_non_vulnerable` - lab เป็น Shiro 1.5.1 ที่น่าจะ vulnerable
- `thinkphp_5-rce` - invokefunction endpoint ไม่เจอ
- `couchdb_CVE-2017-12635` - ต้อง auth ไม่ใช่ admin party

## Merge Summary

| รายการ | จำนวน |
| --- | ---: |
| base targets | 40 |
| targets ที่ merge จริง | 1 |
| targets ที่ไม่มี feature เพิ่ม | 39 |
| records ที่ skip เพราะ target ไม่อยู่ใน safe list | 30 |
| features หลัง merge | 87 |

## ผลเทรน

| Profile | Features | Threshold | Accuracy | Precision | Recall | F1 | TP | FP | TN | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_v02 | 87 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |
| strict_precheck | 81 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| strict_no_negative_count | 86 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| scanner_only | 32 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 20 | 0 | 0 |
| no_metasploit | 83 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |
| no_nuclei_confirm | 86 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 20 | 0 | 20 | 0 |

## แปลผล

`strict_precheck` ยังไม่ผ่าน เพราะ false positive ยัง 20 ตัวจาก 20 negative

สาเหตุหลักไม่ใช่ว่า XGBoost ใช้ไม่ได้ แต่ข้อมูลฝั่ง negative/control ยังไม่น่าเชื่อถือพอ ตัวอย่างเช่น target ที่ตั้งชื่อว่า non-vulnerable บางตัวกลับมี evidence เหมือน vulnerable target

รอบนี้จึงให้ผลเชิงคุณภาพมากกว่าคะแนน:

- ยืนยันว่า `tomcat_CVE-2020-1938` ใช้ train ต่อได้
- ยืนยันว่า 5 targets ต้อง quarantine หรือหา lab ใหม่
- ลดความเสี่ยงที่โมเดลจะเรียนรู้จาก label ผิด

## ข้อสรุป

ยังไม่ควรหยุดงาน ML core ถ้าต้องการให้ `strict_precheck` ใช้งานจริงได้

งานถัดไปที่สำคัญที่สุดคือหา replacement/control labs ที่สะอาด โดยเฉพาะ negative targets ของแต่ละ family:

- Tomcat ที่ PUT ปิดจริง และ AJP ปิดจริง
- Solr ที่ Velocity disabled จริง
- Shiro ที่ไม่ใช่ default-key vulnerable
- CouchDB ที่ admin party แยกชัดจาก auth-required
- ThinkPHP positive lab ที่ endpoint ใช้ได้จริง

