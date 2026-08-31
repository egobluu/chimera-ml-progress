# Timeline ความคืบหน้า

## จุดเริ่มต้น: XGBoost Ranking

เริ่มจากแนวคิดว่าให้ ML ช่วยจัดอันดับ exploit candidate จาก scanner-derived features และเทียบกับ logic baseline

รูปแบบแรก:

```text
target + candidate_family → score
```

candidate family เช่น:

- `tomcat`
- `spring`
- `redis`
- `joomla`
- `nexus`
- `no_exploit`

## รอบแรก: Prototype Ranking

ข้อมูลเริ่มต้นมี target น้อย ทำให้ metric ออกมาดูดีเกินไป เช่น Top-1 = 1.000 ทั้ง logic และ XGBoost

ข้อสรุป:

- คะแนน 1.000 ยังเชื่อไม่ได้
- dataset เล็กเกินไป
- feature alias ชัดเกินไป เช่น product/service ตรงกับ expected family
- ยังแยก `no_exploit` ไม่ดี

## แก้ metric และ leak audit

พบว่า metric `no_exploit_top1` เดิมนิยามผิด เพราะนับเหมือน Top-1 ปกติ ไม่ได้เช็คจริงว่า top candidate คือ `no_exploit`

หลังแก้ metric:

```text
negative_no_exploit_top1 = 0.000
```

แปลว่า model ยังไม่สามารถทำนาย negative target เป็น `no_exploit` ได้ดี

## เพิ่ม dataset เป็น 20 positive / 20 negative

opencode สแกนเพิ่มจนได้:

- validated_positive: 20
- validated_negative: 20
- inconclusive: 15
- total validation files: 55

หลัง train:

```text
logic_baseline Top-1 = 0.450
precheck_xgb Top-1 = 0.650
negative_no_exploit_top1 = 0.300
```

XGBoost เริ่มชนะ logic แต่ยังไม่เก่งเรื่อง `no_exploit`

## เปลี่ยนเป็น 2-stage ML

ทดลองแยก Gate และ Ranker:

```text
Gate: exploit / no_exploit
Ranker: ถ้า exploit ให้ rank family
```

ผลช่วงแรก:

```text
Gate F1 = 0.650
Family Ranker Top-1 = 1.000
```

แปลว่า Ranker ไม่ใช่คอขวด คอขวดคือ Gate

## Gate Feature Improve

opencode เก็บ `gate-feature-evidence.jsonl` สำหรับ target ที่ Gate พลาด 14 ตัว

feature สำคัญ:

- `version_in_vulnerable_range`
- `no_auth_required`
- `ajp_port_open`
- `anonymous_access`
- `velocity_enabled`
- `invokefunction_reachable`
- `negative_evidence_count`
- `version_not_affected`
- `put_upload_rejected`
- `ajp_port_closed`

## ML-only Gate v0.1

เป้าหมายคือเลิกพึ่ง Rule Gate เป็นตัวตัดสินหลัก ให้ XGBoost Gate ตัดสินเอง

ผล:

```text
Recall = 1.000
False Negative = 0
False Positive = 12
F1 = 0.769
Threshold = 0.25
```

ถือว่าผ่าน v0.1 เพราะไม่ skip ช่องโหว่จริง แต่ยังยิงเกินเยอะ

## ML-only Gate v0.2

เติม `gate-feature-evidence.jsonl` ให้ครบ 40/40 validated targets และเพิ่ม feature เป็น 44 ตัว

ผล:

```text
Recall = 1.000
False Negative = 0
False Positive = 0
F1 = 1.000
Threshold = 0.20
```

ข้อสรุป:

- v0.2 สำเร็จตามเกณฑ์ prototype
- แต่ยังต้องทำ leak audit และ unseen target test

