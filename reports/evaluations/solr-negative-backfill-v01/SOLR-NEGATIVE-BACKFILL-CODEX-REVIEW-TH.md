# Codex Review: Solr Negative Backfill v01

## สรุปสั้น

รอบ `dec-solr-negative-backfill-2026-09-02` เติมสิ่งที่ขาดจาก Solr Velocity backfill รอบก่อนหน้าได้แล้ว คือ Solr negative control ที่สะอาด 2 ตัว

ผลที่ใช้ได้:

- `solr_negative_v04_1`
- `solr_negative_v04_2`

ทั้งสอง target เป็น `validated_negative` และ `safe_to_merge=true`

## ทำไม 2 ตัวนี้สำคัญ

ก่อนหน้านี้เรามี Solr positive ที่ clean แล้ว 2 ตัว แต่มี Solr negative ที่ clean แค่ 1 ตัว ทำให้ยังไม่ควร retrain เพราะ model อาจจำว่า “เจอ Solr แล้วมักน่ายิง”

รอบนี้เพิ่ม negative ที่บอกเงื่อนไขตรงกันข้าม:

```text
velocity_enabled = 0
velocity_disabled = 1
velocity_template_accessible = 0
velocity_rce_candidate = 0
```

แปลว่า target เป็น Solr จริง แต่ไม่ผ่าน precondition ของ Solr Velocity exploit

## Target ที่เพิ่ม

| Target | Source | Label | เหตุผลที่เป็น negative |
| --- | --- | --- | --- |
| `solr_negative_v04_1` | `solr:9.7.0` | validated_negative | Solr 9.x ไม่มี VelocityResponseWriter ใน default config |
| `solr_negative_v04_2` | `vulhub/solr:8.2.0` | validated_negative | ใช้ Solr 8.2.0 แต่ลบ VelocityResponseWriter ออกจาก config แล้ว |

## จุดที่ควรระวัง

`solr_negative_v04_2` เป็น hard negative ที่ดี เพราะ version ฝั่งหนึ่งดูเหมือนเสี่ยง แต่ exploit precondition ไม่ผ่านเพราะ Velocity ถูกปิด

ดังนั้น model ไม่ควรเรียนแค่ว่า:

```text
version_in_vulnerable_range = 1 แล้ว exploit ได้
```

แต่ควรเรียนว่า:

```text
ต้องมี velocity_enabled/config_api/precondition ที่จำเป็นด้วย
```

## Dataset ที่สร้าง

รอบนี้ merge ข้อมูลเป็น dataset รุ่นทดลอง:

```text
reports/evaluations/solr-negative-backfill-v01/target-exploitability-with-solr-backfill-v01.csv
```

ขั้นตอน merge:

```text
base 67 targets
  + Solr velocity backfill safe records 3 targets
  + Solr negative backfill safe records 2 targets
  = 72 targets
```

## ผล train runtime รุ่นทดลอง

train ไว้ที่:

```text
reports/evaluations/solr-negative-backfill-v01/runtime-models-solr-backfill-v01/
```

Gate LOO:

| Metric | Result |
| --- | ---: |
| targets | 72 |
| accuracy | 0.9444 |
| precision | 0.8824 |
| recall | 1.0000 |
| F1 | 0.9375 |
| FP | 4 |
| FN | 0 |

Ranker LOO:

| Metric | Result |
| --- | ---: |
| positive targets | 30 |
| candidate families | 16 |
| Top-1 | 0.9000 |
| Top-3 | 0.9000 |
| Top-5 | 0.9000 |
| MRR | 0.9095 |

## เทียบกับ runtime เดิม

runtime เดิมหลัง Redis/Grafana backfill:

```text
Gate LOO: accuracy 0.9701, FP 2, FN 0
Ranker LOO Top-1: 0.8929
```

runtime ทดลองหลัง Solr backfill:

```text
Gate LOO: accuracy 0.9444, FP 4, FN 0
Ranker LOO Top-1: 0.9000
```

ความหมาย:

- Ranker ดีขึ้นเล็กน้อย
- Gate แย่ลง เพราะ false positive เพิ่ม
- ยังไม่ควร promote เป็น default runtime

## Honest v04 หลังลอง model ใหม่นี้

rerun `dec-unseen-validation-v04-honest-2026-09-02` ด้วย model รุ่นทดลองแล้วผลยังเท่าเดิม:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 0.9167 |
| Gate FP | 0 |
| Gate FN | 1 |
| Known-positive Ranker Top-1 | 0.7500 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 0.9167 |
| Strict flow accuracy | 0.9167 |

สาเหตุหลักยังเป็น `solr_velocity_new_01` ที่ feature ฝั่ง v04 ส่งมาเหมือน Velocity ไม่พร้อม:

```text
velocity_endpoint_found = 0
velocity_template_accessible = 0
```

runtime จึงลดเป็น:

```text
low_confidence
needs_more_evidence
```

ดังนั้นปัญหานี้แก้ด้วยการ train อย่างเดียวไม่ได้ ต้องแก้ feature extractor/probe ให้สร้าง canonical Solr Velocity evidence ถูกตั้งแต่แรก

## สถานะที่ควรพูดตอนนี้

```text
Solr negative dataset พร้อม merge แล้ว แต่ runtime รุ่น Solr backfill ยังไม่ควร promote
```

งานถัดไปควรเป็น:

1. ปรับ Solr feature extractor ให้ใช้ logic เดียวกับ backfill นี้
2. rerun unseen Solr positive ใหม่ให้ได้ `velocity_enabled=1`
3. tune Gate threshold หรือ blocking policy เพื่อลด FP จาก 4
4. train ใหม่แล้วค่อยตัดสินใจ promote

