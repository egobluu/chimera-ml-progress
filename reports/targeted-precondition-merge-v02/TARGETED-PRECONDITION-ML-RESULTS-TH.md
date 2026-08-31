# ผล ML หลังรวม Targeted Precondition v0.2

รอบนี้นำ `dec-targeted-precondition-v02-2026-08-31` มารวมกับ dataset ที่มี light backfill แล้ว train/evaluate ใหม่ จุดประสงค์คือดูว่า feature แบบเจาะเงื่อนไข exploit ช่วยลด false positive ของ `strict_precheck` ได้หรือไม่

## Dataset หลัง merge

| รายการ | จำนวน |
| --- | ---: |
| base targets | 40 |
| targets ที่มี targeted feature | 11 |
| targets ที่ยังไม่มี targeted feature | 29 |
| features ก่อน merge targeted | 68 |
| targeted numeric features | 19 |
| features หลัง merge | 78 |

## ผล profile audit

| profile | features | threshold | accuracy | precision | recall | f1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full_v02` | 78 | 0.20 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |
| `strict_precheck` | 72 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `strict_no_negative_count` | 77 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `scanner_only` | 32 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `no_metasploit` | 74 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |
| `no_nuclei_confirm` | 77 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |

## อ่านผลแบบตรงไปตรงมา

targeted precondition รอบนี้ยังไม่ลด FP ในค่า threshold ที่เราเลือก เพราะ threshold 0.10 ถูกเลือกเพื่อกัน false negative ให้เป็น 0 ทำให้โมเดลยังทาย `exploit` ทุก negative target

แต่ถ้าดู threshold สูงขึ้นจะเห็นว่าโมเดลเริ่มแยก negative ได้บางส่วน:

| threshold | TP | FP | TN | FN | precision | recall | f1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 20 | 20 | 0 | 0 | 0.500 | 1.000 | 0.667 |
| 0.40 | 13 | 6 | 14 | 7 | 0.684 | 0.650 | 0.667 |
| 0.50 | 13 | 4 | 16 | 7 | 0.765 | 0.650 | 0.703 |
| 0.60 | 13 | 3 | 17 | 7 | 0.812 | 0.650 | 0.722 |

แปลว่า feature เริ่มมีสัญญาณ แต่ยังไม่สมดุลพอ เพราะพอเพิ่ม threshold เพื่อลด FP จะเสีย positive ไป 7 ตัว

## ทำไม targeted feature ยังช่วยไม่พอ

1. **feature กระจายบางเกินไป**

   หลาย feature มีแค่ target เดียว เช่น `method_put_rejected`, `ajp_port_closed`, `rememberme_not_seen`, `velocity_disabled` พอใช้ leave-one-out ถ้า target นั้นถูกกันไว้เป็น test โมเดลจะไม่เคยเห็น feature นั้นใน train fold

2. **ยังเก็บ negative มากกว่า positive precondition**

   เราเก็บ feature ที่บอกว่า negative ไม่ควร exploit ได้ดีขึ้น แต่ยังไม่มีคู่ positive ที่ใช้ feature ชุดเดียวกันมากพอ เช่น Tomcat positive ควรมี `method_put_allowed` เพื่อเทียบกับ Tomcat negative ที่มี `method_put_rejected`

3. **บาง feature ขัดกับ label หรือยังตีความผิด**

   ตัวอย่างที่ต้องตรวจซ้ำ:

   - `tomcat_non_vulnerable` มี `version_in_vulnerable_range_true=1` แต่ label เป็น negative อาจถูกได้ถ้า method/AJP block แต่ต้องเขียนเหตุผลให้ชัด
   - `redis_non_vulnerable` และ `redis_auth_non_vulnerable` มี `no_auth_required=1` และ `lua_available=1` ซึ่งเป็น positive-like signal ต้องตรวจว่าทำไม label ยังเป็น negative
   - `nginx_non_vulnerable` มี `version_patched=1` จาก nginx 1.13.2 แต่ CVE-2017-7529 เคยใช้ nginx 1.13.2 เป็น vulnerable target จึงควรตรวจซ้ำว่า mapping หรือ rule ผิดหรือไม่

4. **targeted feature มีแค่ 11/40 targets**

   ยังไม่พอให้โมเดลเรียน pattern ทั่วไป โดยเฉพาะ family ที่มีแค่ negative หรือมีแค่ positive

## ข้อสรุป

targeted precondition v0.2 เป็นทิศทางที่ถูก แต่ยังไม่ใช่จุดที่ ML ใช้งานได้จริงทันที งานถัดไปต้องทำ targeted probe เป็น “คู่ positive/negative” ใน family เดียวกัน เพื่อให้โมเดลเห็นว่าค่าไหนคือผ่านและค่าไหนคือไม่ผ่าน

## งานถัดไปที่ควรทำ

1. เก็บ Tomcat positive:
   - `tomcat_CVE-2017-12615`: ต้องได้ `method_put_allowed`
   - `tomcat_CVE-2020-1938`: ต้องได้ `ajp_port_open`

2. เก็บ ThinkPHP positive:
   - `thinkphp_5-rce` หรือ `thinkphp_5023_rce`: ต้องได้ `invokefunction_reachable`

3. เก็บ Solr positive:
   - `solr_CVE-2019-17558`: ต้องได้ `velocity_enabled`

4. เก็บ CouchDB positive:
   - `couchdb_CVE-2017-12635` หรือ `couchdb_CVE-2017-12636`: ต้องได้ `admin_party_enabled` หรือ `config_accessible`

5. ตรวจซ้ำ feature ที่ขัดกับ label:
   - Redis negative ที่ยัง `lua_available`
   - Nginx negative ที่ version 1.13.2 ถูก mark เป็น patched
   - Tomcat negative ที่ version อยู่ใน vulnerable range แต่ precondition ถูก block

เป้าหมายรอบถัดไปคือไม่ใช่เพิ่ม target เยอะ แต่เพิ่ม feature ที่มีคู่เทียบให้โมเดลเรียนจริง
