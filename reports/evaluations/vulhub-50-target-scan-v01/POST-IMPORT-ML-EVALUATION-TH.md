# Post Import ML Evaluation: Vulhub 50 Target Scan v01

ชุดนี้นำเข้าจาก:

```text
C:\Users\rapii\Desktop\kali-share\dataset\vulhub-50-target-scan-v01
```

## Import Summary

| Item | Count |
| --- | ---: |
| targets.jsonl | 51 |
| features.jsonl | 51 |
| validation-results.jsonl | 51 |
| cve-enrichment.jsonl | 22 |
| safe_to_merge จาก scanner | 51 |
| quarantine จาก scanner | 0 |
| raw evidence folders ที่พบจริง | 14 |

หมายเหตุ: แผนเดิมคือ 50 targets แต่ผลที่กลับมามี 51 rows จึงเก็บไว้ทั้งหมดในรอบ import และใช้ audit แยกความพร้อมแทน

## Runtime Category หลัง Normalize

| Runtime category | Count |
| --- | ---: |
| known_positive | 15 |
| negative_control | 28 |
| unknown_family | 8 |

unknown-family 8 ตัวถูกต้องตาม runtime ปัจจุบัน เพราะ family เหล่านี้ยังไม่ได้อยู่ใน candidate list ของ Ranker:

- Drupal
- JBoss
- Jetty
- Laravel
- WordPress
- PHP-CGI
- Nacos
- Spring

## ML Evaluation หลัง Patch Runtime

| Metric | Result |
| --- | ---: |
| Total targets | 51 |
| Gate TP | 23 |
| Gate FP | 2 |
| Gate TN | 26 |
| Gate FN | 0 |
| Gate accuracy | 0.9608 |
| Gate precision | 0.9200 |
| Gate recall | 1.0000 |
| Gate F1 | 0.9583 |
| Known-positive Ranker Top-1 | 15/15 |
| Known-positive Ranker Top-3 | 15/15 |
| Unknown-family rejected | 8/8 |
| Safety flow accuracy | 51/51 |
| Strict flow accuracy | 51/51 |

## สิ่งที่ Patch แล้ว

เพิ่ม runtime normalization เพื่อแปลชื่อ feature จาก scanner ให้เข้ากับชื่อที่ runtime model ใช้ เช่น:

- `default_key_detected` -> `default_key_likely`
- `remember_me_cookie_found` -> `rememberme_deleteMe_seen`
- `script_console_accessible` -> `cli_endpoint_reachable`
- `default_credentials` -> `anonymous_access`
- `rce_endpoint_accessible` -> `upload_endpoint_reachable` เฉพาะ Struts2
- `ssti_endpoint_accessible` -> `rce_endpoint_candidate_found` เฉพาะ Flask
- `sql_injection_endpoint` -> `api_path_found` เฉพาะ Joomla
- `ssrf_endpoint_accessible` -> `endpoint_reachable_count` เฉพาะ Next.js

เพิ่ม product hint ใน Ranker เพื่อกันกรณี product ชัดแต่คะแนน generic ไปชน family อื่น เช่น `nexus_detected`, `nextjs_detected`, `shiro_detected`

เพิ่ม unknown guard ให้ unknown product ไม่หลุดไปเป็น known family เพียงเพราะมี feature กลางอย่าง `rce_endpoint_accessible`

## ใช้ Train ได้แค่ไหน

ยังไม่ควรเอา 51 rows เข้า train ทั้งหมดทันที

เหตุผล:

- raw evidence มีจริงแค่ 14 targets
- report ฝั่ง scanner แจ้งว่าบาง images missing แต่ validation ยัง safe_to_merge ทั้งหมด
- บาง positive มี feature แบบ label-level มากกว่า scanner-derived precondition เต็ม

แนะนำแบ่งแบบนี้:

| กองข้อมูล | จำนวนโดยประมาณ | การใช้ |
| --- | ---: | --- |
| train_ready_strict | 14 | target ที่มี raw evidence folder จริง ใช้ train/validation ได้หลังตรวจ raw |
| validation_only | 37 | ใช้เป็น regression/compatibility test ก่อน อย่า train ทันที |
| quarantine_recheck | 0+ | ยังไม่มีจาก scanner แต่ควร recheck image missing/manual label ก่อน promote |

## Decision

รอบนี้เหมาะจะ merge เข้า repo เป็น evaluation/regression ก่อน

ยังไม่ควร retrain โมเดลทันทีจากทั้ง 51 rows จนกว่าจะ:

1. ตรวจ raw evidence ของ 14 targets
2. rerun หรือเติม raw evidence ให้ rows ที่เหลือ
3. แยก row ที่เป็น synthetic/label-only ออกจาก scanner-derived feature
4. สร้าง CVE resolver validation จาก `cve-enrichment.jsonl`

## Curation Result

หลังเพิ่ม `scripts/curate_imported_scan_batch.py` และชี้ raw evidence ไปที่ shared folder:

| Split | Count | ความหมาย |
| --- | ---: | --- |
| train_ready_strict | 14 | มี raw evidence folder จริง และ runtime strict ผ่าน |
| validation_only | 37 | runtime ผ่าน แต่ raw evidence ยังไม่ครบ จึงใช้เป็น regression ได้ก่อน |
| needs_recheck | 0 | ไม่มีแถวที่ runtime fail หรือ feature/validation หาย |

ผล runtime check เฉพาะ `train_ready_strict`:

| Metric | Result |
| --- | ---: |
| Total | 14 |
| Gate TP/FP/TN/FN | 7/0/7/0 |
| Ranker Top-1 | 7/7 |
| Safety flow | 14/14 |
| Strict flow | 14/14 |

Decision ล่าสุด:

- ใช้ `train_ready_strict` เป็น candidate สำหรับ train รอบถัดไปได้ หลังคนตรวจ raw evidence แบบ spot check
- ใช้ `validation_only` เป็น regression/compatibility suite ต่อไปก่อน
- อย่าเอา 51 rows ทั้งหมดไป train ทันที
