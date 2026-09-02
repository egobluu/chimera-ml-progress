# Codex Review: Solr Schema Fix v01

## สรุปสั้น

รอบ `dec-solr-schema-fix-2026-09-02` แก้ปัญหาสำคัญของ Solr ได้ถูกจุด คือทำให้ Solr positive/negative ใช้ feature schema เดียวกัน และมี label consistency ผ่าน 5/5 targets

สิ่งที่ดีขึ้น:

- Solr positive มี `velocity_enabled=1`
- Solr negative มี `velocity_disabled=1`
- ทุก target มี field หลักชุดเดียวกัน
- ไม่มี target ถูก quarantine
- ข้อมูลชุดนี้เหมาะสำหรับใช้เป็น canonical Solr backfill ต่อไป

แต่ผล train ยังไม่ควร promote เป็น default runtime เพราะ Gate false positive ยังสูงกว่า runtime เดิม

## Target ที่ safe to merge

| Target | Label | Evidence สำคัญ |
| --- | --- | --- |
| `solr_velocity_positive_v04_fix` | validated_positive | `solr_core_found=1`, `velocity_enabled=1`, `config_api_accessible=1` |
| `solr_velocity_positive_alt` | validated_positive | `velocity_enabled=1`, `velocity_template_accessible=1`, `config_api_accessible=1` |
| `solr_negative_v04_1` | validated_negative | `velocity_disabled=1`, `version_not_affected=1`, `version_patched=1` |
| `solr_negative_v04_2` | validated_negative | `velocity_disabled=1`, `version_in_vulnerable_range=1`, `version_not_affected=1` |
| `solr_velocity_negative_disabled` | validated_negative | `velocity_disabled=1`, `config_api_blocked=1`, `version_not_affected=1` |

## ทำไม schema fix รอบนี้สำคัญ

ปัญหาเดิมของ v04 คือ Solr positive ถูกส่ง feature เหมือนหลักฐานไม่พอ เช่น:

```text
velocity_endpoint_found = 0
velocity_template_accessible = 0
```

runtime จึงลดผลเป็น:

```text
low_confidence
needs_more_evidence
```

รอบนี้ OpenCode แก้ probe ให้เช็คตรงขึ้น:

1. `/solr/`
2. `/solr/admin/cores?action=STATUS&wt=json`
3. `/solr/{core}/config?wt=json`
4. ตรวจ VelocityResponseWriter
5. ทดสอบ `wt=velocity` ว่าทำงานจริงหรือ fallback เป็น JSON

นี่คือแนวทางที่ถูกต้อง เพราะ ML ต้องกิน feature ที่นิยามเหมือนกันทุก target ไม่ใช่บางรอบมี field หนึ่ง บางรอบใช้ alias อีกชื่อ

## Dataset รุ่นทดลอง

Codex merge schema-fixed records 5 ตัวเข้า base dataset 67 targets:

```text
67 base targets
+ 5 Solr schema-fixed targets
= 72 targets
```

ไฟล์ dataset:

```text
reports/evaluations/solr-schema-fix-v01/target-exploitability-with-solr-schema-fix-v01.csv
```

## ผล train runtime รุ่นทดลอง

model รุ่นทดลองอยู่ที่:

```text
reports/evaluations/solr-schema-fix-v01/runtime-models-solr-schema-fix-v01/
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

## เทียบกับ runtime default ปัจจุบัน

runtime default ปัจจุบันหลัง Redis/Grafana backfill:

```text
Gate accuracy 0.9701, FP 2, FN 0
Ranker Top-1 0.8929
```

runtime ทดลองหลัง Solr schema fix:

```text
Gate accuracy 0.9444, FP 4, FN 0
Ranker Top-1 0.9000
```

ความหมาย:

- Ranker ดีขึ้นเล็กน้อย
- Gate แย่ลงเพราะ FP เพิ่มจาก 2 เป็น 4
- ยังไม่ควร promote model รุ่นนี้เป็น default runtime

## Honest v04 หลังใช้ model รุ่นนี้

rerun `dec-unseen-validation-v04-honest-2026-09-02` ด้วย model รุ่นทดลองแล้วได้:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 0.9167 |
| Gate FP | 0 |
| Gate FN | 1 |
| Known-positive Ranker Top-1 | 0.7500 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 0.9167 |
| Strict flow accuracy | 0.9167 |

ผลยังเท่าเดิม เพราะ v04 ใช้ feature file เดิมที่ยังบอกว่า Solr positive มี Velocity evidence ไม่ครบ

ดังนั้น schema fix รอบนี้ช่วยสร้างข้อมูลที่ถูกสำหรับ train รอบถัดไป แต่ยังไม่ได้แก้ historical v04 feature ที่เก็บผิดไปแล้ว

## สถานะ

```text
Solr schema fix สำเร็จในเชิง dataset quality แต่ยังไม่สำเร็จพอสำหรับ promote runtime
```

## งานถัดไป

1. เอา Solr probe logic ชุดนี้ไปใช้ใน scanner/feature extractor หลัก
2. สแกน unseen Solr positive ใหม่ 1-2 ตัวด้วย extractor ใหม่
3. tune Gate threshold หรือ negative blocking policy เพื่อลด FP จาก 4
4. train runtime ใหม่อีกครั้ง
5. promote เฉพาะถ้า Gate ไม่แย่กว่า default และ honest unseen ดีขึ้นจริง

