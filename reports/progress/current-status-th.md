# สถานะล่าสุดของงาน ML

## สรุปสถานะ

ตอนนี้งาน ML เดินมาถึง **ML-only Exploitability Gate v0.2 + Strict Precheck Improve v01**

ถือว่าผ่านเป้าหมาย prototype ระดับต้นในแง่ pipeline เพราะ:

- ไม่พึ่ง Rule Gate เป็นตัวตัดสินหลัก
- train/evaluate/infer ได้
- มี model artifact
- มี threshold tuning
- มี feature schema
- มี dataset target-level
- มี evidence ครบ 40/40 validated targets

## Dataset ล่าสุด

| รายการ | จำนวน |
| --- | ---: |
| validated_positive | 20 |
| validated_negative | 20 |
| inconclusive | 15 |
| train/evaluate targets | 40 |
| gate features | 44 |

## ผล v0.2

| Metric | Result |
| --- | ---: |
| Accuracy | 1.000 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| False Positive | 0 |
| False Negative | 0 |

## การตีความ

ผลนี้แปลว่า v0.2 ทำงานดีมากบน dataset ปัจจุบัน แต่ยังไม่ควรสรุปว่าใช้งานจริงได้กับ target ใหม่ทั้งหมด เพราะ dataset ยังเล็กและ feature บางตัวอาจมีความใกล้กับ label

คำพูดที่เหมาะสม:

```text
โมเดล ML-only Gate v0.2 สามารถทำงานได้คงที่บน controlled dataset และพร้อมเข้าสู่ขั้นตอน unseen target validation
```

ไม่ควรพูดว่า:

```text
โมเดลแม่น 100% แล้ว
```

## ผล Targeted Pair Fix v01

รอบนี้รวมเฉพาะ feature records ที่มี `label_consistency=consistent` จาก `dec-targeted-pair-fix-2026-08-31`

| รายการ | จำนวน |
| --- | ---: |
| targets ที่มี pair-fix feature ใช้ได้ | 3 |
| records ที่ skip เพราะ inconsistent | 11 |
| features หลัง merge | 79 |

ผล `strict_precheck` ยังไม่ดีขึ้น:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.500 |
| Precision | 0.500 |
| Recall | 1.000 |
| F1 | 0.667 |
| False Positive | 20 |
| False Negative | 0 |

ความหมาย: โมเดลยังมอง negative เป็น exploit ได้ง่ายเกินไป เพราะ evidence ฝั่ง precheck ที่ reliable ยังน้อย ต้องแก้ label consistency และเก็บ pair features เพิ่มก่อน

## งานถัดไป

1. quarantine target ที่ label/evidence ขัดกัน
2. แก้ target label เช่น target ที่ version หรือ precondition ไม่ตรง CVE
3. เก็บ positive/negative pair ต่อ family ให้ครบ
4. train `strict_precheck` ใหม่ด้วย dataset ที่ label consistency ผ่าน
5. ทำ unseen target test โดยให้ model infer ก่อน แล้วค่อยใช้ Metasploit/manual PoC เฉลย

## Audit ล่าสุด

เพิ่มสคริปต์ `scripts/audit_gate_features.py` เพื่อเช็คว่า feature ไหนอาจทำให้คะแนนสูงเกินจริง โดยเฉพาะ feature ที่รู้หลังยิง exploit หรือหลังเขียนผล validation แล้ว งานถัดไปควรวัด `strict_precheck` ที่ตัด feature กลุ่มนี้ออกก่อน

## Light Backfill ล่าสุด

นำผล `dec-precheck-light-backfill-2026-08-31` มา merge แล้วได้ dataset 40 targets / 68 features โดยมี target ที่ backfill จริง 15 ตัว ผลยังชี้ว่า `strict_precheck` และ `scanner_only` มี FP=20 เมื่อเลือก threshold แบบไม่ยอมให้ FN เกิด แปลว่า feature ใหม่ช่วยเรื่องความสะอาดของข้อมูล แต่ยังไม่พอให้โมเดลแยก `no_exploit` ได้ ต้องเพิ่ม targeted precondition probes ต่อ

## Targeted Probe Plan

เพิ่มแผน `reports/plans/targeted-precondition-v01/` จาก false positive ของ `strict_precheck` ได้ 60 probe tasks ครอบคลุม 20 false positive targets เป้าหมายคือเก็บ feature ที่ผูกกับ exploit condition จริง เช่น `method_put_rejected`, `ajp_port_closed`, `auth_required`, `endpoint_missing`, `version_patched` เพื่อให้โมเดลลด FP โดยไม่ต้องพึ่ง `negative_evidence_count`

ปรับเพิ่มเป็น `reports/plans/targeted-precondition-v02/` เพื่อให้อ่านง่ายและทำงานจริงง่ายขึ้น โดยตัด probe กว้าง ๆ ที่ไม่จำเป็นออก เช่น `generic_*`, default path discovery ทั่วไป, target ที่ไม่มี lab ตรง และเน้นเฉพาะ precondition ที่ตอบว่า exploit family นั้นผ่านหรือไม่ผ่านจริง

## Targeted Precondition Result

รวมผล `dec-targeted-precondition-v02-2026-08-31` แล้วได้ dataset 40 targets / 78 features แต่ `strict_precheck` ยัง FP=20 ที่ threshold 0.10 สาเหตุหลักคือ targeted features ยัง sparse เกินไปและส่วนใหญ่มีเฉพาะ negative side งานถัดไปต้องเก็บ targeted precondition ฝั่ง positive เป็นคู่เทียบ เช่น `method_put_allowed` เทียบกับ `method_put_rejected`, `ajp_port_open` เทียบกับ `ajp_port_closed`, `velocity_enabled` เทียบกับ `velocity_disabled`

## Targeted Pair Quality Audit

ผล `dec-targeted-precondition-pairs-2026-08-31` ยังไม่ควรนำเข้า train ตรง ๆ เพราะมี positive targets หลายตัวที่ได้ negative evidence เช่น `thinkphp_5-rce` ได้ `invokefunction_not_found`, `solr_CVE-2019-17558` ได้ `velocity_disabled`, `couchdb_CVE-2017-12635` ได้ `auth_required`, `shiro_CVE-2016-4437` ได้ `rememberme_not_seen` จึงต้อง quarantine แล้วแก้ lab/probe เฉพาะ family ก่อน

## Targeted Pair Fix Result

ผล `dec-targeted-pair-fix-2026-08-31` แก้ได้บางส่วน เช่น `solr_CVE-2019-17558`, `shiro_CVE-2016-4437`, และ `redis_non_vulnerable` แต่ยังมี target ที่ label/evidence inconsistent อยู่ เช่น `thinkphp_5-rce`, `couchdb_CVE-2017-12635`, `nginx_CVE-2017-7529`, `redis_auth_non_vulnerable`

ใช้ได้เฉพาะ records ที่ consistent เท่านั้น รายละเอียดอยู่ที่ `reports/evaluations/targeted-pair-fix-v01/`

## Strict Precheck Improve Result

ผล `dec-strict-precheck-improve-2026-08-31` มี 11 targets แต่ใช้ train ได้อย่างปลอดภัย 4 targets:

- `redis_auth_non_vulnerable`
- `tomcat_non_vulnerable`
- `solr_CVE-2019-17558`
- `shiro_CVE-2016-4437`

หลัง merge แล้วได้ 40 targets / 86 features แต่ผล `strict_precheck` ยังไม่ผ่าน:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.500 |
| Precision | 0.500 |
| Recall | 1.000 |
| F1 | 0.667 |
| False Positive | 20 |
| False Negative | 0 |

สรุป: ยังไม่ควรหยุดงาน ML core เพราะ profile ที่ใกล้ใช้งานจริงที่สุดยังแยก negative ไม่ได้ ต้องแก้ label consistency และเก็บคู่ positive/negative ที่สะอาดกว่านี้
