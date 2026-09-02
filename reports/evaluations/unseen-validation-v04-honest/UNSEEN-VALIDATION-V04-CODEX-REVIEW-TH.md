# Codex Review: Honest Unseen Validation v04

## สรุปสั้น

รอบ `dec-unseen-validation-v04-honest-2026-09-02` เป็นรอบที่น่าเชื่อกว่ารอบก่อน เพราะเป็น target ใหม่หลัง runtime ถูกแก้จาก v03 แล้ว และไม่ได้ใช้ target ที่ถูกนำเข้า train ไปแล้ว

ผลที่สำคัญที่สุด:

```text
ระบบไม่ได้ 100% แบบโลกจริง
แต่ Unknown Guard ดีขึ้นจริง
ปัญหาหลักที่เหลือคือ Solr feature extraction / Solr ranker evidence
```

## Source Metrics จาก OpenCode

| Metric | Source Result |
| --- | ---: |
| Gate Accuracy | 0.9167 |
| Gate FP | 1 |
| Gate FN | 0 |
| Ranker Top-1 | 0.7500 |
| Unknown Guard | 0.0000 |
| Safety Flow | 0.9167 |
| Strict Flow | 0.8333 |

source report มีประโยชน์ แต่ยังไม่ควรใช้ตรง ๆ ทั้งหมด เพราะไฟล์ feature จริงมี `unknown_product_detected=1` สำหรับ unknown targets แล้ว แต่ source evaluation ยังบอก unknown guard 0/4

## Corrected Metrics จาก Codex Runtime

Codex rerun ด้วย runtime/evaluator ล่าสุดจาก repo:

```bash
python scripts/evaluate_runtime_predictions.py \
  --features-jsonl reports/evaluations/unseen-validation-v04-honest/unseen-v04-precheck-features.jsonl \
  --targets-jsonl reports/evaluations/unseen-validation-v04-honest/unseen-v04-targets.jsonl \
  --out-dir reports/evaluations/unseen-validation-v04-honest/corrected-current-runtime
```

ผล corrected:

| Metric | Corrected Result |
| --- | ---: |
| Total targets | 12 |
| Gate accuracy | 0.9167 |
| Gate TP | 7 |
| Gate FP | 0 |
| Gate TN | 4 |
| Gate FN | 1 |
| Known-positive Ranker Top-1 | 0.7500 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 0.9167 |
| Strict flow accuracy | 0.9167 |

## ทำไม corrected metrics ไม่เหมือน source

### 1. Unknown Guard

source บอก `0/4` แต่ feature จริงของ unknown targets มี:

```text
unknown_product_detected=1
unknown_family_signal_count=1
known_family_signal_count=0
```

runtime ล่าสุดจึง force เป็น:

```text
unknown_family_triage
```

ดังนั้น corrected unknown rejection rate เป็น `1.0000`

### 2. Solr Negative

source บอก `solr_no_velocity_neg_v04` เป็น Gate FP แต่ runtime ล่าสุดอ่าน negative evidence แล้ว downgrade เป็น:

```text
low_confidence
needs_more_evidence
```

จึงไม่ใช่ FP แบบพาไป verify ทันที

### 3. Solr Positive

ปัญหาจริงที่เหลือคือ `solr_velocity_new_01`

feature ที่ส่งมา:

```text
solr_detected=1
velocity_endpoint_found=0
velocity_template_accessible=0
velocity_rce_candidate=0
version_in_vulnerable_range=1
```

runtime จึงมองว่าไม่มีหลักฐาน Velocity ที่ชัดพอ และ downgrade เป็น:

```text
low_confidence
needs_more_evidence
```

ในเชิง safety ถือว่าดีกว่ายิงมั่ว แต่ในเชิง ML recall นับเป็น FN เพราะ target นี้เป็น known-positive

## เคสที่ยังพลาด

| Target | Expected | Actual | Problem |
| --- | --- | --- | --- |
| `solr_velocity_new_01` | `solr_velocity` / likely exploitable | `needs_more_evidence` | feature extractor ไม่เจอ Velocity evidence ที่จำเป็น |

## สถานะหลัง v04

| ส่วน | สถานะ |
| --- | --- |
| Gate | ดีขึ้น แต่ยังมี FN จาก Solr positive |
| Unknown Guard | ผ่าน 4/4 ใน corrected runtime |
| Ranker | 3/4 known-positive Top-1 เพราะ Solr ไม่ได้เข้า ranking |
| Safety Flow | 11/12 |
| Strict Flow | 11/12 |

## การตีความที่ควรใช้

ควรพูดว่า:

```text
Honest v04 แสดงว่า runtime ใหม่กัน unknown-family ได้ดีขึ้นแล้ว แต่ยังมีปัญหา Solr feature extraction ทำให้ target positive ถูกส่งเป็น needs_more_evidence แทนที่จะ rank เป็น solr_velocity
```

ไม่ควรพูดว่า:

```text
โมเดลแม่น 100% แล้ว
```

## งานถัดไป

งานต่อไปควรแคบมาก:

1. ให้ OpenCode ทำ Solr Velocity feature backfill เท่านั้น
2. ต้องแยก positive/negative Solr ให้ชัด:
   - positive ต้องมี `velocity_enabled=1` หรือ evidence ว่า VelocityResponseWriter ใช้งานได้จริง
   - negative ต้องมี `velocity_disabled=1` หรือ `config_api_blocked=1`
3. ห้าม retrain ก่อน Codex ตรวจว่า Solr evidence consistent
4. หลังแก้ Solr แล้ว rerun corrected evaluation

สรุปคือรอบนี้ไม่ควรสแกนเพิ่มกว้าง ๆ แล้ว ควรแก้ Solr evidence ให้เป็น canonical schema ก่อน
