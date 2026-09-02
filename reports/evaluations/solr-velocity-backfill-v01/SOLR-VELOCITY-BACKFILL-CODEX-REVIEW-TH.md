# Codex Review: Solr Velocity Backfill v01

## สรุปสั้น

รอบ `dec-solr-velocity-backfill-2026-09-02` ทำถูกทางแล้ว เพราะแก้เฉพาะ failure ที่เจอจาก honest unseen v04 คือ Solr Velocity ไม่ใช่สแกนกว้างเพิ่ม

ผลที่ใช้ได้:

- ได้ Solr positive ที่ clean 2 ตัว
- ได้ Solr negative ที่ clean 1 ตัว
- เจอ target ที่ตั้งใจเป็น negative แต่จริง ๆ Velocity เปิดอยู่ 1 ตัว จึง quarantine ถูกต้อง

## ผลรวม

| รายการ | จำนวน |
| --- | ---: |
| Targets tested | 4 |
| Safe to merge | 3 |
| Validated positive | 2 |
| Validated negative | 1 |
| Inconclusive/quarantined | 1 |

## Targets ที่ safe to merge

| Target | Label | Evidence สำคัญ |
| --- | --- | --- |
| `solr_velocity_positive_v04_fix` | validated_positive | `solr_detected=1`, `solr_core_found=1`, `velocity_enabled=1`, `config_api_accessible=1` |
| `solr_velocity_positive_alt` | validated_positive | `velocity_enabled=1`, `velocity_template_accessible=1`, `config_api_accessible=1` |
| `solr_velocity_negative_disabled` | validated_negative | `velocity_disabled=1`, `config_api_blocked=1`, `version_not_affected=1` |

## Target ที่ไม่ควร merge

| Target | เหตุผล |
| --- | --- |
| `solr_velocity_negative_patched_or_blocked` | ตั้งใจเป็น negative แต่ evidence พบว่า `velocity_enabled=1` และ config API accessible จึงไม่ใช่ negative control ที่สะอาด |

## ทำไมรอบนี้สำคัญ

ใน honest unseen v04 เคส `solr_velocity_new_01` ถูกลดเป็น:

```text
low_confidence
needs_more_evidence
```

เพราะ feature ที่ส่งมาไม่มีหลักฐาน Velocity ที่ runtime ต้องใช้ เช่น:

```text
velocity_enabled
velocity_template_accessible
config_api_accessible
```

รอบนี้จึงช่วยเติม feature ที่ตรงกับ schema จริง ทำให้รอบ retrain ถัดไปโมเดลควรแยก Solr positive/negative ได้ดีขึ้น

## ยังไม่ควร retrain ทันที

แม้จะมี 3 records ที่ safe to merge แล้ว แต่ยังไม่ควร retrain ทันที เพราะ Solr negative ที่ clean มีแค่ 1 ตัว

ถ้า retrain ตอนนี้ model อาจเรียนรู้ Solr negative จากตัวอย่างเดียว ซึ่งเสี่ยง overfit และทำให้ผลดูดีเกินจริง

เกณฑ์ที่แนะนำก่อน retrain:

```text
Solr positive clean >= 2
Solr negative clean >= 2
ทุก target ต้องมี canonical fields ครบ
```

ตอนนี้มี:

```text
Solr positive clean = 2
Solr negative clean = 1
```

ดังนั้นควรหา Solr negative เพิ่มอีกอย่างน้อย 1 ตัว

## งานถัดไป

ให้ OpenCode ทำ Solr negative backfill เพิ่มแบบแคบมาก:

- หา Solr patched/disabled/auth-blocked อีก 1-2 targets
- ต้องได้ `velocity_disabled=1` หรือ `config_api_blocked=1`
- ห้ามใช้ target ที่ Velocity เปิดอยู่เป็น negative
- ถ้าไม่เจอ ให้สร้าง custom clean negative lab จาก `solr:9.7.0` พร้อม core ที่ Velocity disabled

หลังได้ negative เพิ่มแล้ว Codex ค่อย:

1. merge Solr backfill เข้า dataset
2. retrain runtime
3. rerun v04 corrected evaluation
4. ทำ honest unseen v05 ด้วย target ใหม่

## สถานะ

```text
Solr backfill รอบนี้ดีและใช้ได้บางส่วน แต่ยังไม่พอสำหรับ retrain ที่น่าเชื่อถือ
```
