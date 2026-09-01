# ผล XGBoost Family Ranking v01

## สรุปสั้น

รอบนี้เริ่มทดสอบส่วน `Family Ranker` แล้ว

Gate ตอบว่า target ควรลอง exploit ไหม ส่วน Ranker ตอบต่อว่า ถ้าควร exploit ควรลอง exploit family ไหนก่อน

ผลรวมทั้ง dataset ยังไม่ผ่าน แต่ผลบน clean-control positives ผ่านดีมาก แปลว่า ranking direction ถูกทาง แต่ original positive targets ยังมี feature สำหรับจัดอันดับไม่พอ

## Dataset ที่ใช้

ใช้ dataset ล่าสุดจาก `negative-control-variations-v01`

| รายการ | จำนวน |
| --- | ---: |
| total targets | 65 |
| positive targets ที่ใช้ ranking | 26 |
| candidate families | 16 |

หมายเหตุ: ranking ใช้เฉพาะ positive targets เพราะ `no_exploit` เป็นงานของ Gate ไม่ควรเอามาแข่งใน candidate family ranking

## Candidate Families

Ranker ให้คะแนน family เหล่านี้:

- `couchdb_auth`
- `elasticsearch`
- `flask`
- `grafana`
- `jenkins`
- `joomla`
- `nextjs`
- `nexus`
- `nginx`
- `redis`
- `shiro_key`
- `solr_velocity`
- `spring`
- `struts2`
- `thinkphp_rce`
- `tomcat_ajp`
- `tomcat_put`

## วิธีวัด

ใช้ leave-one-target-out evaluation:

1. เลือก target positive 1 ตัวเป็น test
2. train ranker ด้วย positive targets ที่เหลือ
3. สร้าง candidate rows ทุก family ให้ target test
4. ให้ XGBoost rank คะแนนทุก family
5. วัดว่า family ที่ถูกอยู่ลำดับที่เท่าไหร่

metric ที่ใช้:

- `Top-1`: family อันดับ 1 ถูกไหม
- `Top-3`: family ที่ถูกอยู่ใน 3 อันดับแรกไหม
- `Top-5`: family ที่ถูกอยู่ใน 5 อันดับแรกไหม
- `MRR`: ยิ่ง family ที่ถูกอยู่ลำดับบน ค่าเฉลี่ยยิ่งสูง

## ผลรวม

| Metric | Result |
| --- | ---: |
| Top-1 | 0.500 |
| Top-3 | 0.538 |
| Top-5 | 0.538 |
| MRR | 0.551 |

แปลว่า ranking ยังไม่พร้อมใช้จริงทั้ง dataset

## ผลแยกตามชนิด target

| Segment | Targets | Top-1 | Top-3 | Top-5 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: |
| clean_control_positive | 6 | 1.000 | 1.000 | 1.000 | 1.000 |
| original_positive | 20 | 0.350 | 0.400 | 0.400 | 0.417 |

แปลผล:

- target ใหม่ที่เก็บแบบ clean precondition rank ถูกหมด
- target positive เก่าหลายตัวยัง rank ผิด เพราะ feature ไม่พอหรือ label/evidence เคยมีปัญหา

## ตัวอย่างที่ rank ถูก

- `shiro_default_key_positive` -> `shiro_key`
- `tomcat_ajp_positive` -> `tomcat_ajp`
- `tomcat_put_positive` -> `tomcat_put`
- `couchdb_admin_party_positive` -> `couchdb_auth`
- `solr_velocity_positive` -> `solr_velocity`
- `thinkphp_invokefunction_positive` -> `thinkphp_rce`

## ตัวอย่างที่ rank ผิด

| Target | True family | Rank | Top-1 ที่ model เลือก |
| --- | --- | ---: | --- |
| `couchdb_CVE-2017-12635` | `couchdb_auth` | 10 | `tomcat_put` |
| `grafana_CVE-2021-43798` | `grafana` | 14 | `flask` |
| `joomla_CVE-2023-23752` | `joomla` | 16 | `nextjs` |
| `thinkphp_5-rce` | `thinkphp_rce` | 9 | `grafana` |
| `tomcat_CVE-2017-12615` | `tomcat_put` | 11 | `couchdb_auth` |

หลายตัวในกลุ่มนี้เคยถูก flag ว่า label/evidence ยังไม่นิ่ง หรือยังไม่มี precondition feature ที่เจาะ family พอ

## ข้อสรุป

สถานะตอนนี้:

```text
Gate / precondition_only = ผ่าน prototype
Family Ranking รวมทุก target = ยังไม่ผ่าน
Family Ranking เฉพาะ clean controls = ผ่าน
```

ดังนั้นงานถัดไปของ ranking ไม่ใช่เพิ่ม model complexity แต่ต้องเพิ่ม candidate-family evidence ให้ original positive targets

## งานถัดไป

ให้ OpenCode เก็บ family-specific precondition features เพิ่มสำหรับ original positive targets ที่ rank ผิด โดยใช้ schema เดียวกับ clean controls

เป้าหมายรอบถัดไป:

| Metric | เป้าหมายขั้นต่ำ |
| --- | ---: |
| Ranking Top-1 รวม | >= 0.75 |
| Ranking Top-3 รวม | >= 0.90 |
| Clean-control Top-1 | คงไว้ที่ 1.00 |

