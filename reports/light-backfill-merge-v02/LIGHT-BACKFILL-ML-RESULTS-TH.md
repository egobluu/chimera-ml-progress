# ผลทดสอบ ML หลัง Light Backfill

รอบนี้นำข้อมูลจาก `dec-precheck-light-backfill-2026-08-31` มา merge เข้ากับ dataset v0.2 แล้วเทรน/evaluate ใหม่ เพื่อดูว่า feature จาก `whatweb`, `curl`, และ `ffuf` ช่วยให้ `strict_precheck` ลด false positive ได้หรือไม่

## Dataset หลัง merge

| รายการ | จำนวน |
| --- | ---: |
| base targets | 40 |
| targets ที่มี light backfill | 15 |
| targets ที่ยังไม่มี backfill | 25 |
| base features | 44 |
| backfill numeric features | 27 |
| merged features | 68 |

## ผล profile audit

| profile | features | threshold | accuracy | precision | recall | f1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full_v02` | 68 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |
| `strict_precheck` | 62 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `strict_no_negative_count` | 67 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `scanner_only` | 32 | 0.10 | 0.500 | 0.500 | 1.000 | 0.667 | 20 | 0 |
| `no_metasploit` | 64 | 0.20 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |
| `no_nuclei_confirm` | 67 | 0.15 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 |

## อ่านผล

Light backfill ทำให้ dataset มี feature ก่อนยิง exploit เพิ่มขึ้นจริง แต่ยังไม่ทำให้ `strict_precheck` ดีขึ้นในเกณฑ์ที่เราเลือก เพราะเกณฑ์ปัจจุบันให้ความสำคัญกับการไม่พลาด positive ก่อน จึงเลือก threshold 0.10 และทำให้โมเดลทาย `exploit` ทุกตัว

พูดง่าย ๆ:

```text
โมเดลยังกัน false negative ได้
แต่ยังกัน false positive ไม่ได้
```

## Threshold trade-off

ถ้าเพิ่ม threshold ของ `strict_precheck`:

| threshold | TP | FP | TN | FN | precision | recall | f1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 20 | 20 | 0 | 0 | 0.500 | 1.000 | 0.667 |
| 0.30 | 13 | 17 | 3 | 7 | 0.433 | 0.650 | 0.520 |
| 0.40 | 13 | 6 | 14 | 7 | 0.684 | 0.650 | 0.667 |
| 0.50 | 13 | 5 | 15 | 7 | 0.722 | 0.650 | 0.684 |
| 0.60 | 13 | 3 | 17 | 7 | 0.812 | 0.650 | 0.722 |

แปลว่า feature มีสัญญาณบางส่วน เพราะ threshold สูงลด FP ได้ แต่ยังต้องเสีย FN เยอะเกินไป จึงยังไม่พร้อมใช้เป็น gate หลัก

## ทำไม backfill ยังไม่ช่วยพอ

1. backfill มีแค่ 15/40 targets ทำให้ 25 targets ยังเป็น missing-heavy
2. `whatweb`, `curl`, `ffuf` ให้ข้อมูลทั่วไป แต่ยังไม่พอแยก exploitability เฉพาะ CVE
3. negative ที่ดีต้องมี evidence แบบ precondition fail เช่น endpoint exploit หาย, method ถูกปฏิเสธ, version patched, auth block
4. `scanner_only` ยังไม่เห็นความต่างเชิง exploit มากพอ เพราะ path discovery เจอ path แต่ไม่ได้บอกว่า exploit condition ผ่านหรือไม่

## สิ่งที่ต้องทำต่อ

รอบถัดไปควรทำ targeted precondition probes ไม่ใช่แค่ generic web discovery:

- Tomcat: เช็ค `PUT` allowed/rejected และ AJP 8009
- Spring: เช็ค Spring-specific header/error/actuator/classloader behavior
- Shiro: เช็ค `rememberMe` behavior
- Grafana: เช็ค vulnerable endpoint/path traversal behavior
- Redis: เช็ค auth/config/lua capability แบบ safe
- Solr: เช็ค Velocity config/API behavior
- ThinkPHP: เช็ค invokefunction endpoint reachable/not found
- CouchDB: เช็ค admin party/auth requirement

## ข้อสรุป

Light backfill รอบนี้สำเร็จในเชิง data hygiene และทำให้ schema พร้อมขึ้น แต่ยังไม่พอให้ ML ทำนายแบบใช้งานจริงได้ดีขึ้น จุดถัดไปที่ควรทำคือเก็บ feature แบบ `precondition_fail/pass` ให้ครบและสมดุลทั้ง positive/negative แทนการพึ่ง feature รวมก้อนอย่าง `negative_evidence_count`
