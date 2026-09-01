# Codex Review: Ranker Schema Backfill Redis/Grafana v01

## สรุปสั้น

OpenCode เก็บ feature backfill เฉพาะ 2 target ที่ Ranker พลาดใน Unseen v02:

- `unseen_redis_variant_01`
- `unseen_grafana_variant_01`

Codex ตรวจแล้วพบว่า feature รอบนี้ตรงกับ runtime schema และช่วยแก้ปัญหา Ranker ได้จริงในชุดทดสอบ v02

## ก่อน backfill

ผล corrected evaluation หลัง patch unknown guard แต่ก่อน merge backfill:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 1.000 |
| Known-positive Ranker Top-1 | 0.3333 |
| Unknown rejection rate | 1.000 |
| Safety flow accuracy | 1.000 |
| Strict flow accuracy | 0.8333 |

เคสที่พลาด:

| Target | Expected | Predicted ก่อน backfill |
| --- | --- | --- |
| `unseen_redis_variant_01` | `redis` | `couchdb_auth` |
| `unseen_grafana_variant_01` | `grafana` | `redis` |

## Feature ที่เพิ่ม

### Redis

```text
redis_detected=1
redis_info_accessible=1
lua_available=1
no_auth_required=1
version_in_vulnerable_range=1
is_non_http_service=1
```

### Grafana

```text
grafana_detected=1
plugin_path_candidate_found=1
public_plugin_path_accessible=1
path_traversal_candidate_found=1
version_in_vulnerable_range=1
is_http_target=1
```

## หลัง merge backfill แล้ว rerun runtime

ใช้ไฟล์:

```text
unseen-v02-features-with-redis-grafana-backfill.jsonl
```

แล้วรัน:

```bash
python scripts/evaluate_runtime_predictions.py \
  --features-jsonl reports/evaluations/ranker-schema-backfill-redis-grafana-v01/unseen-v02-features-with-redis-grafana-backfill.jsonl \
  --targets-jsonl reports/evaluations/unseen-validation-v02/unseen-v02-targets.jsonl \
  --out-dir reports/evaluations/ranker-schema-backfill-redis-grafana-v01
```

ผล corrected หลัง backfill:

| Metric | Result |
| --- | ---: |
| Total targets | 12 |
| Gate accuracy | 1.000 |
| Gate TP | 8 |
| Gate FP | 0 |
| Gate TN | 4 |
| Gate FN | 0 |
| Known-positive Ranker Top-1 | 1.000 |
| Unknown rejection rate | 1.000 |
| Safety flow accuracy | 1.000 |
| Strict flow accuracy | 1.000 |

## การตีความที่ถูกต้อง

ผลนี้ไม่ได้แปลว่าโมเดลแม่น 100% กับโลกจริง

ผลนี้แปลว่า:

```text
Ranker พลาดเพราะ feature ของ Redis/Grafana ไม่ครบ เมื่อเติม family-specific features ที่ถูกต้อง Ranker จัด family ในชุด v02 ได้ถูก
```

ดังนั้นสิ่งที่เราเรียนรู้คือ:

- คุณภาพ feature สำคัญกว่าการ train ซ้ำแบบไม่แก้ schema
- family-specific evidence จำเป็นต่อ Ranker
- generic HTTP signal อย่าง `no_auth_required` หรือ `endpoint_reachable_count` อย่างเดียวทำให้ Rankerสับสน

## สถานะหลังรอบนี้

| ส่วน | สถานะ |
| --- | --- |
| Gate | ผ่านในชุด v02 แต่ยังต้องทดสอบชุดใหญ่ขึ้น |
| Unknown Guard | ทำงานถูกหลัง patch |
| Ranker | ทำงานดีขึ้นเมื่อ feature schema ตรง |
| Dataset | ควรนำ 2 records นี้เข้า training dataset รอบถัดไป |

## งานถัดไป

1. merge Redis/Grafana backfill records เข้า clean training dataset
2. retrain runtime model/ranker ใหม่
3. ทำ unseen validation v03 ด้วย target ใหม่ ไม่ใช่ target เดิม
4. เพิ่ม backfill แบบเดียวกันให้ family อื่นที่ยัง evidence บาง เช่น Joomla, NextJS, Tomcat PUT

คำเตือน:

```text
อย่าใช้ v02 หลัง backfill เป็นหลักฐานว่า production-ready เพราะเราซ่อม feature ของ target ที่รู้ว่าพลาดแล้ว ต้องทดสอบ v03 ด้วย target ใหม่เสมอ
```
