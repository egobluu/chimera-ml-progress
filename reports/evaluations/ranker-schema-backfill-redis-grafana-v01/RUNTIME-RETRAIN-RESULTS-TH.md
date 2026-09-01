# Runtime Retrain Results: Ranker Schema Backfill v01

## สรุปสั้น

นำ Redis/Grafana backfill records ที่ `safe_to_merge=true` เข้า dataset แล้ว retrain runtime prototype ใหม่

สิ่งที่เปลี่ยน:

- dataset จาก 65 targets เป็น 67 targets
- positive training targets ของ Ranker จาก 26 เป็น 28
- default runtime ที่ `runtime/models/prototype/` ถูก train ใหม่ด้วย dataset รุ่นนี้
- เก็บ runtime version แยกไว้ที่ `runtime/models/ranker-schema-backfill-v01/`

## Dataset ที่ใช้ train

```text
reports/evaluations/ranker-schema-backfill-redis-grafana-v01/target-exploitability-family-ranking-backfill-plus-redis-grafana.csv
```

records ที่เพิ่ม:

| Target | Label | Family |
| --- | ---: | --- |
| `unseen_redis_variant_01` | 1 | `redis` |
| `unseen_grafana_variant_01` | 1 | `grafana` |

ข้อควรจำ:

```text
หลังจากนำ target จาก unseen v02 เข้า train แล้ว ห้ามใช้ target เดิมเป็นหลักฐาน unseen อีก ต้องใช้ unseen v03 target ใหม่
```

## Gate หลัง retrain

| Metric | Result |
| --- | ---: |
| Train targets | 67 |
| Threshold | 0.15 |
| Accuracy | 0.9701 |
| Precision | 0.9333 |
| Recall | 1.0000 |
| F1 | 0.9655 |
| TP | 28 |
| FP | 2 |
| TN | 37 |
| FN | 0 |

การตีความ:

Gate ยังรักษาจุดสำคัญได้คือ `FN=0` ใน LOO evaluation หมายความว่าในชุดข้อมูลนี้ยังไม่พลาดหยุด target ที่ควรลอง exploit

## Family Ranker หลัง retrain

LOO evaluation:

| Metric | Result |
| --- | ---: |
| Positive targets | 28 |
| Candidate families | 16 |
| Top-1 | 0.8929 |
| Top-3 | 0.8929 |
| Top-5 | 0.8929 |
| MRR | 0.9035 |

การตีความ:

คะแนนไม่ได้กระโดดเป็น 1.000 ใน LOO รวม แปลว่าไม่ได้กลายเป็นโมเดลที่จำทุกอย่างแบบหลอกตาทันที แต่ดีขึ้นในจุด Redis/Grafana ที่เคยมี feature ไม่ครบ

## Runtime sanity check

รัน default runtime ใหม่กับชุด v02 ที่เติม backfill แล้ว:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 1.000 |
| Known-positive Ranker Top-1 | 1.000 |
| Unknown rejection rate | 1.000 |
| Safety flow accuracy | 1.000 |
| Strict flow accuracy | 1.000 |

การตีความ:

ตัวเลขนี้เป็น sanity check หลังแก้ feature ไม่ใช่ proof ว่า production-ready เพราะ target Redis/Grafana จาก v02 ถูกนำเข้า train แล้ว

## สถานะหลังรอบนี้

ใช้เป็น runtime prototype ล่าสุดได้:

```text
runtime/models/prototype/
scripts/predict_prototype.py
```

แต่การพิสูจน์จริงรอบต่อไปต้องเป็น:

```text
unseen validation v03 ด้วย target ใหม่ที่ไม่อยู่ใน training dataset
```

## งานถัดไป

1. ให้ OpenCode สร้าง unseen v03 target ใหม่
2. ห้ามใช้ `unseen_redis_variant_01` และ `unseen_grafana_variant_01` เป็น unseen อีก
3. ใช้ feature schema เดียวกับ runtime ปัจจุบัน
4. วัด metric ด้วย `scripts/evaluate_runtime_predictions.py`
5. ถ้า Ranker พลาด family ใหม่ ให้ backfill เฉพาะ family นั้นแล้วค่อย retrain รอบถัดไป
