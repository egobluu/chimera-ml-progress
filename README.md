# Chimera Scanner ML Progress

repo นี้ใช้เก็บสรุปความคืบหน้าฝั่ง Machine Learning ของโครงงาน `chimera-scanner-dataset` ตั้งแต่ช่วงที่เริ่มเปลี่ยนแนวทางมาใช้ **XGBoost Ranking / XGBoost Gate** เพื่อช่วยจัดลำดับการทดสอบช่องโหว่จากผล vulnerability scanner

เนื้อหาเน้นตอบคำถามหลัก:

- เราทำอะไรไปแล้ว
- ใช้ข้อมูลอะไร train
- ทดสอบอย่างไร
- คะแนนมาจากไหน
- เจอปัญหาอะไร
- แก้อย่างไร
- ตอนนี้โมเดลอยู่ระดับไหน
- ต้องทำอะไรต่อเพื่อให้ใช้งานจริงได้มากขึ้น

## แนวคิดระบบล่าสุด

ระบบถูกออกแบบเป็น 2-stage ML workflow:

```text
Scanner Evidence
      ↓
ML-only Exploitability Gate
      ↓
XGBoost Family Ranker
      ↓
Metasploit / Manual Verification
      ↓
Feedback กลับเข้า Dataset
```

ความหมาย:

- `Exploitability Gate`: โมเดลตัดสินว่า target นี้ควรถูกทดสอบ exploit ต่อหรือควรเป็น `no_exploit`
- `Family Ranker`: ถ้า Gate บอกว่าควร exploit จึงจัดอันดับ exploit family เช่น `tomcat`, `redis`, `spring`, `nexus`
- `Verification`: ใช้ Metasploit/manual PoC ตรวจว่าผลที่เลือกใช้ได้จริงหรือไม่
- `Feedback Loop`: เอาผลยิงได้/ยิงไม่ได้กลับมาเพิ่ม dataset และ feature

## สถานะล่าสุด

สถานะล่าสุดคือ **ML-only Exploitability Gate v0.2 รันได้ครบ pipeline แล้ว** แต่ผลที่เหมาะกับการใช้งานจริงต้องดู profile `strict_precheck` เป็นหลัก

ผลจาก full profile:

| Metric | v0.1 | v0.2 |
| --- | ---: | ---: |
| Recall | 1.000 | 1.000 |
| False Negative | 0 | 0 |
| False Positive | 12 | 0 |
| F1 | 0.769 | 1.000 |
| gate-feature-evidence | 14/40 | 40/40 |
| Features | 33 | 44 |

ข้อควรระวัง: คะแนน full profile ยังดีเกินจริง เพราะมี feature ที่ใกล้คำเฉลยหรือเกิดหลังตรวจ exploit แล้ว ส่วน `strict_precheck` หลังรวม targeted pair fix ยังมี FP=20 ที่ threshold 0.10 จึงยังไม่ควรพูดว่าโมเดลแม่นแล้ว

## เอกสารสำคัญ

- [docs/00-navigation-th.md](docs/00-navigation-th.md) - สารบัญหลักว่าอ่าน repo นี้ยังไง
- [docs/01-project-scope-th.md](docs/01-project-scope-th.md) - ขอบเขตงาน ML หลังเริ่มใช้ XGBoost Ranking
- [docs/02-timeline-th.md](docs/02-timeline-th.md) - timeline ว่าทำอะไรไปแล้วตามลำดับ
- [docs/03-training-and-evaluation-th.md](docs/03-training-and-evaluation-th.md) - วิธี train/test และ metric ที่ใช้
- [docs/04-feature-schema-th.md](docs/04-feature-schema-th.md) - feature ที่ใช้และเหตุผล
- [docs/05-lessons-learned-th.md](docs/05-lessons-learned-th.md) - ปัญหาและสิ่งที่แก้
- [docs/06-scanning-tools-th.md](docs/06-scanning-tools-th.md) - เครื่องมือที่ใช้ในงานจริงและงานเก็บ dataset
- [docs/07-feature-catalog-th.md](docs/07-feature-catalog-th.md) - รายการ feature ทั้งหมดและ phase ที่ใช้ได้/ห้ามใช้
- [docs/08-workflow-responsibilities-th.md](docs/08-workflow-responsibilities-th.md) - หน้าที่ของ Codex, OpenCode, ML, scanner และ Metasploit
- [docs/09-llm-handoff-runtime-th.md](docs/09-llm-handoff-runtime-th.md) - สิ่งที่ต้องส่งต่อให้ฝั่ง LLM/agentic และไฟล์ไหนคือของใช้จริง
- [runtime/README-TH.md](runtime/README-TH.md) - คู่มือ runtime prototype ที่ควรเรียกใช้จริง
- [scripts/README.md](scripts/README.md) - script ที่ใช้ build dataset, train model และ inference
- [reports/README.md](reports/README.md) - สารบัญ reports แยก progress/audit/evaluation/plan/quarantine
- [reports/progress/current-status-th.md](reports/progress/current-status-th.md) - สรุปสถานะล่าสุด
- [reports/plans/targeted-precondition-v02/TARGETED-PRECONDITION-PROBE-PLAN-TH.md](reports/plans/targeted-precondition-v02/TARGETED-PRECONDITION-PROBE-PLAN-TH.md) - แผน probe เจาะจงที่เกลาใหม่สำหรับลด false positive
- [reports/evaluations/targeted-precondition-v02/TARGETED-PRECONDITION-ML-RESULTS-TH.md](reports/evaluations/targeted-precondition-v02/TARGETED-PRECONDITION-ML-RESULTS-TH.md) - ผล ML หลังรวม targeted precondition และข้อผิดพลาดที่ยังเหลือ
- [reports/quarantine/targeted-pair-quality-v01/TARGETED-PAIR-QUALITY-AUDIT-TH.md](reports/quarantine/targeted-pair-quality-v01/TARGETED-PAIR-QUALITY-AUDIT-TH.md) - ตรวจคุณภาพ targeted pair ก่อนนำเข้า train
- [reports/evaluations/targeted-pair-fix-v01/TARGETED-PAIR-FIX-ML-RESULTS-TH.md](reports/evaluations/targeted-pair-fix-v01/TARGETED-PAIR-FIX-ML-RESULTS-TH.md) - ผลหลังรวมเฉพาะ targeted pair records ที่ consistent
- [reports/evaluations/strict-precheck-improve-v01/STRICT-PRECHECK-IMPROVE-ML-RESULTS-TH.md](reports/evaluations/strict-precheck-improve-v01/STRICT-PRECHECK-IMPROVE-ML-RESULTS-TH.md) - ผลหลังรวม strict precheck safe targets รอบล่าสุด
- [reports/evaluations/label-consistency-fix-v01/LABEL-CONSISTENCY-FIX-ML-RESULTS-TH.md](reports/evaluations/label-consistency-fix-v01/LABEL-CONSISTENCY-FIX-ML-RESULTS-TH.md) - ผลหลังคัด label consistency fix รอบล่าสุด
- [reports/evaluations/clean-control-labs-v01/CLEAN-CONTROL-LABS-ML-RESULTS-TH.md](reports/evaluations/clean-control-labs-v01/CLEAN-CONTROL-LABS-ML-RESULTS-TH.md) - ผลหลังเพิ่ม CouchDB clean control pair เป็น target ใหม่
- [reports/evaluations/clean-control-labs-v02/CLEAN-CONTROL-LABS-V02-ML-RESULTS-TH.md](reports/evaluations/clean-control-labs-v02/CLEAN-CONTROL-LABS-V02-ML-RESULTS-TH.md) - ผลหลังเพิ่ม clean control targets 9 ตัวแบบ precondition focus
- [reports/evaluations/missing-positive-controls-v01/MISSING-POSITIVE-CONTROLS-ML-RESULTS-TH.md](reports/evaluations/missing-positive-controls-v01/MISSING-POSITIVE-CONTROLS-ML-RESULTS-TH.md) - ผลหลังเพิ่ม positive controls ที่ขาด และทดสอบ `precondition_only`
- [reports/evaluations/negative-control-variations-v01/NEGATIVE-CONTROL-VARIATIONS-ML-RESULTS-TH.md](reports/evaluations/negative-control-variations-v01/NEGATIVE-CONTROL-VARIATIONS-ML-RESULTS-TH.md) - ผลหลังเพิ่ม negative controls จน `precondition_only` ผ่านเกณฑ์ prototype
- [reports/evaluations/family-ranking-v01/FAMILY-RANKING-V01-RESULTS-TH.md](reports/evaluations/family-ranking-v01/FAMILY-RANKING-V01-RESULTS-TH.md) - ผลทดสอบ XGBoost Family Ranker รอบแรก
- [reports/evaluations/family-ranking-backfill-v01/FAMILY-RANKING-BACKFILL-V01-RESULTS-TH.md](reports/evaluations/family-ranking-backfill-v01/FAMILY-RANKING-BACKFILL-V01-RESULTS-TH.md) - ผล Family Ranker หลังเพิ่ม family-specific backfill features
- [reports/evaluations/unknown-family-v01/UNKNOWN-FAMILY-V01-RESULTS-TH.md](reports/evaluations/unknown-family-v01/UNKNOWN-FAMILY-V01-RESULTS-TH.md) - ผลทดสอบ unknown-family/open-set guard
- [reports/evaluations/unseen-validation-v01/UNSEEN-VALIDATION-CODEX-REVIEW-TH.md](reports/evaluations/unseen-validation-v01/UNSEEN-VALIDATION-CODEX-REVIEW-TH.md) - รีวิว unseen validation รอบแรกแบบ predict ก่อน verify
- [reports/evaluations/unseen-validation-v02/UNSEEN-VALIDATION-V02-CODEX-REVIEW-TH.md](reports/evaluations/unseen-validation-v02/UNSEEN-VALIDATION-V02-CODEX-REVIEW-TH.md) - รีวิว unseen validation รอบสอง พร้อม audit จุดที่ผลสรุปขัดกับ prediction จริง
- [reports/plans/feature-schema-alignment-v01/FEATURE-SCHEMA-ALIGNMENT-PLAN-TH.md](reports/plans/feature-schema-alignment-v01/FEATURE-SCHEMA-ALIGNMENT-PLAN-TH.md) - แผนปรับ feature schema ให้ OpenCode/feature extractor ตรงกับ runtime ML

## ระดับความพร้อม

ถ้าให้คะแนนภาพรวมเป้าหมายสุดท้ายเป็น 10/10:

```text
ตอนนี้อยู่ประมาณ 4/10 สำหรับ pipeline รวม เพราะ Gate และ Family Ranker ผ่านระดับ prototype แล้ว
```

เพราะ:

- มี ML-only Gate ที่ train/evaluate/infer ได้แล้ว
- มี dataset 20 positive / 20 negative ที่ balance
- มี feature evidence ครบทุก target ที่ใช้ train
- มี Family Ranker ที่ Top-1 0.885 หลังเพิ่ม backfill features
- แต่ยังต้องพิสูจน์กับ unseen target ใหม่ และทำ inference/API ให้ใช้งานจริง

## Unseen Validation v02

ผลล่าสุดจาก `dec-unseen-validation-v02-2026-09-01` ทำให้เห็นภาพจริงขึ้น:

- Gate แยก vulnerable/negative controls ได้ดีในชุดทดสอบนี้
- Ranker ยังพลาด Redis/Grafana variants เพราะ family-specific features ไม่ครบ
- unknown-family guard ในไฟล์สรุปเดิมมีข้อมูลขัดกับ prediction จริง
- runtime ถูก patch แล้วให้ `unknown_product_detected` บังคับไป `unknown_family_triage`

สรุปสถานะที่ควรใช้พูดตอนนี้:

```text
ML prototype ใช้เป็น decision-support ได้แล้ว แต่ยังต้องทำ feature schema alignment ก่อน retrain/ranker รอบถัดไป
```

หลัง rerun corrected evaluation ด้วย runtime ที่ patch แล้ว:

| Metric | Corrected Result |
| --- | ---: |
| Gate accuracy | 1.000 |
| Known-positive Ranker Top-1 | 0.333 |
| Unknown rejection rate | 1.000 |
| Safety flow accuracy | 1.000 |
| Strict flow accuracy | 0.833 |

ตัวเลขนี้คือคำตอบที่ควรใช้แทน “100%” เดิม เพราะแยกชัดว่า flow ปลอดภัยขึ้น แต่ Ranker ยังพลาด Redis/Grafana
