# ผลทดสอบ XGBoost Family Ranking หลัง Backfill v01

## สรุปสั้น

รอบนี้เอาผล `dec-family-ranking-backfill-2026-09-01` จาก Kali/OpenCode มารวมกับ dataset หลัก แล้ว train/evaluate `XGBoost Family Ranker` ใหม่

ผลคือ **Family Ranking ผ่านระดับ prototype แล้ว**

| Metric | ก่อน backfill | หลัง backfill |
| --- | ---: | ---: |
| Top-1 | 0.500 | 0.885 |
| Top-3 | 0.539 | 0.885 |
| Top-5 | 0.539 | 0.885 |
| MRR | 0.551 | 0.897 |

ความหมาย: ถ้า Gate บอกว่า target ควรลอง exploit ต่อ ตัว Ranker สามารถเลือก exploit family อันดับ 1 ได้ถูกประมาณ 88.5% บนชุดทดสอบปัจจุบัน

## ข้อมูลที่นำเข้า

Input จาก Kali:

```text
C:\Users\rapii\Desktop\kali-share\dataset\dec-family-ranking-backfill-2026-09-01
```

ไฟล์สำคัญ:

- `targeted-family-ranking-features.jsonl` - feature สำหรับ family ranking 57 records
- `label-consistency-audit.jsonl` - ผลตรวจว่า target ไหนใช้ train ได้
- `ranking-safe-to-merge-targets.txt` - รายชื่อ target ที่ merge ได้/ต้อง quarantine
- `FAMILY-RANKING-BACKFILL-SUMMARY-TH.md` - สรุปจากฝั่งสแกน

Dataset ฐาน:

```text
reports/evaluations/negative-control-variations-v01/target-exploitability-negative-control-variations.csv
```

หลัง merge:

| รายการ | จำนวน |
| --- | ---: |
| base targets | 65 |
| targets ที่ได้ backfill | 10 |
| feature เดิม | 95 |
| feature ใหม่จาก backfill | 40 |
| feature หลัง merge | 119 |

## Target ที่ merge

ใช้เฉพาะ target ที่ `label_consistency=consistent` และ `ranking_safe_to_merge=true`

| Target | Family | Evidence สำคัญ |
| --- | --- | --- |
| `couchdb_CVE-2017-12635` | `couchdb_auth` | `admin_party_enabled`, `users_db_accessible`, `auth_required=0` |
| `elasticsearch_CVE-2015-1427` | `elasticsearch` | `script_engine_enabled`, `groovy_enabled`, `dynamic_scripting_enabled` |
| `flask_ssti` | `flask` | `jinja_detected`, `template_echo_observed`, `ssti_expression_evaluated` |
| `grafana_CVE-2021-43798` | `grafana` | `public_plugin_path_accessible`, `path_traversal_candidate_found` |
| `jenkins_CVE-2018-1000861` | `jenkins` | `cli_endpoint_reachable`, `stapler_endpoint_candidate_found` |
| `nginx_CVE-2017-7529` | `nginx` | `range_header_supported` |
| `redis_CVE-2022-0543` | `redis` | `redis_info_accessible`, `lua_available`, `auth_required=0` |
| `solr_CVE-2017-12629-RCE` | `solr_velocity` | `solr_core_found`, `velocity_enabled`, `config_api_accessible` |
| `struts2_s2-045` | `struts2` | `upload_endpoint_reachable` |
| `thinkphp_5-rce` | `thinkphp_rce` | `rce_endpoint_accessible`, `rce_endpoint_candidate_found` |

ไม่ได้ merge:

- `joomla_CVE-2023-23752` - container มีปัญหา
- `nextjs_CVE-2025-29927` - ไม่มี Vulhub lab
- `tomcat_CVE-2017-12615` - container มีปัญหา

## วิธีวัด

สคริปต์ที่ใช้:

```text
scripts/train_family_ranker.py
```

คำสั่ง:

```bash
python scripts/train_family_ranker.py \
  --dataset reports/evaluations/family-ranking-backfill-v01/target-exploitability-family-ranking-backfill.csv \
  --out-dir reports/evaluations/family-ranking-backfill-v01
```

วิธี test คือ `leave-one-target-out`

แปลแบบง่าย:

1. เลือก positive target ออกมา 1 ตัวเป็น test
2. train ด้วย positive targets ที่เหลือ
3. ให้ model rank candidate families ทั้งหมด
4. ดูว่า family ที่ถูกต้องอยู่ลำดับที่เท่าไหร่
5. ทำวนจนครบทุก positive target

metric:

- `Top-1` = family ที่ถูกต้องอยู่อันดับ 1 หรือไม่
- `Top-3` = family ที่ถูกต้องอยู่ใน 3 อันดับแรกหรือไม่
- `Top-5` = family ที่ถูกต้องอยู่ใน 5 อันดับแรกหรือไม่
- `MRR` = คะแนนเฉลี่ยตามอันดับ ยิ่ง target ถูกดันขึ้นบน คะแนนยิ่งสูง

## ผลแยกตามกลุ่ม

| Segment | Targets | Top-1 | Top-3 | Top-5 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: |
| clean_control_positive | 6 | 1.000 | 1.000 | 1.000 | 1.000 |
| original_positive | 20 | 0.850 | 0.850 | 0.850 | 0.866 |

ความหมาย:

- clean controls ยังทายถูกทั้งหมด
- original positives ดีขึ้นจาก Top-1 0.350 เป็น 0.850
- backfill family-specific evidence ช่วยแก้ปัญหา ranking ได้จริง

## เคสที่ยังพลาด

| Target | Family จริง | Rank | ทายอันดับ 1 |
| --- | --- | ---: | --- |
| `joomla_CVE-2023-23752` | `joomla` | 8 | `nextjs` |
| `nextjs_CVE-2025-29927` | `nextjs` | 8 | `joomla` |
| `tomcat_CVE-2017-12615` | `tomcat_put` | 16 | `nextjs` |

ทั้ง 3 ตัวคือกลุ่มที่รอบ backfill ถูก quarantine หรือยังไม่มี evidence ที่เชื่อถือได้ จึงไม่ควรใช้เป็นตัวตัดสินว่า Ranker พัง แต่ควรมองว่าเป็นรายการที่ต้องเก็บ evidence ใหม่เมื่อมี lab ที่เสถียร

## สถานะตอนนี้

ถ้าแบ่งระบบเป็น 2 ชั้น:

```text
1. Gate: exploit ได้ไหม
2. Ranker: ถ้า exploit ได้ ควรลอง family ไหนก่อน
```

สถานะล่าสุด:

| ส่วน | สถานะ | เหตุผล |
| --- | --- | --- |
| ML-only Gate | ผ่าน prototype | `precondition_only` F1 0.943, FP 2, FN 1 |
| Family Ranker | ผ่าน prototype | Top-1 0.885 หลัง backfill |

สรุป: **หยุดสแกนวนเพื่อแก้ ML core ได้ชั่วคราว** แล้วควรเริ่มทำส่วนใช้งานจริงระดับต้น เช่น inference command/API และรายงานผลที่อ่านง่าย

## งานถัดไปที่ควรทำ

1. Freeze baseline ชุดนี้เป็น `prototype-baseline-2026-09-01`
2. ทำ inference flow รวม: scanner evidence -> Gate -> Family Ranker -> recommendation
3. ทำ output ภาษาไทยสำหรับ user เช่น “ควรลอง Metasploit module กลุ่มไหนก่อน เพราะอะไร”
4. เก็บ evidence เพิ่มเฉพาะ 3 family ที่ยังพลาด: Joomla, NextJS, Tomcat PUT
5. ทดสอบกับ unseen target ใหม่ 5-10 ตัว โดยให้ model ทายก่อน แล้วค่อยใช้ Metasploit/manual PoC เป็นเฉลย
