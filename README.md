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
- [docs/10-ml-from-zero-th.md](docs/10-ml-from-zero-th.md) - คู่มือสอน ML ของโปรเจกต์นี้จากศูนย์ ตั้งแต่ data/features/train/metrics/runtime ไปจนถึง LLM handoff
- [docs/11-ml-runtime-integration-contract-th.md](docs/11-ml-runtime-integration-contract-th.md) - สัญญา input/output ระหว่าง scanner, ML runtime และ LLM พร้อม policy/checklist
- [docs/12-llm-decision-explainer-th.md](docs/12-llm-decision-explainer-th.md) - วิธีแปลง runtime prediction JSON เป็นคำอธิบาย/next action สำหรับ LLM/operator
- [docs/13-machine2-runtime-workflow-th.md](docs/13-machine2-runtime-workflow-th.md) - workflow เครื่อง 2: Host Codex + Kali VM OpenCode สำหรับ runtime/evaluation/priority report
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
- [reports/evaluations/ranker-schema-backfill-redis-grafana-v01/RANKER-SCHEMA-BACKFILL-CODEX-REVIEW-TH.md](reports/evaluations/ranker-schema-backfill-redis-grafana-v01/RANKER-SCHEMA-BACKFILL-CODEX-REVIEW-TH.md) - ผลหลังเติม Redis/Grafana family-specific features แล้ว rerun Ranker
- [reports/evaluations/unseen-validation-v03/UNSEEN-VALIDATION-V03-CODEX-REVIEW-TH.md](reports/evaluations/unseen-validation-v03/UNSEEN-VALIDATION-V03-CODEX-REVIEW-TH.md) - ผล unseen v03 หลังตรวจ metric ใหม่และแก้ runtime guard จาก failure จริง
- [reports/plans/feature-schema-alignment-v01/FEATURE-SCHEMA-ALIGNMENT-PLAN-TH.md](reports/plans/feature-schema-alignment-v01/FEATURE-SCHEMA-ALIGNMENT-PLAN-TH.md) - แผนปรับ feature schema ให้ OpenCode/feature extractor ตรงกับ runtime ML
- [reports/plans/scanner-batch-ingestion-v01/SCANNER-BATCH-INGESTION-PLAN-TH.md](reports/plans/scanner-batch-ingestion-v01/SCANNER-BATCH-INGESTION-PLAN-TH.md) - แผนรับ batch จากเครื่องสแกน ผ่าน import/audit/evaluate ก่อนเข้า train
- [reports/plans/runtime-regression-v01/RUNTIME-REGRESSION-PLAN-TH.md](reports/plans/runtime-regression-v01/RUNTIME-REGRESSION-PLAN-TH.md) - วิธีรัน regression suites กันไม่ให้ runtime ถอย

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

หลังทำ targeted schema backfill เฉพาะ Redis/Grafana แล้ว rerun runtime บนชุด v02 เดิม:

| Metric | After Backfill |
| --- | ---: |
| Known-positive Ranker Top-1 | 1.000 |
| Unknown rejection rate | 1.000 |
| Safety flow accuracy | 1.000 |
| Strict flow accuracy | 1.000 |

ต้องตีความว่า “feature schema คือสาเหตุหลักของ Ranker failure” ไม่ใช่สรุปว่าโมเดลแม่น 100% กับโลกจริง

runtime prototype ล่าสุดถูก retrain แล้วจาก dataset 67 targets:

- `runtime/models/prototype/`
- `runtime/models/ranker-schema-backfill-v01/`
- [reports/evaluations/ranker-schema-backfill-redis-grafana-v01/RUNTIME-RETRAIN-RESULTS-TH.md](reports/evaluations/ranker-schema-backfill-redis-grafana-v01/RUNTIME-RETRAIN-RESULTS-TH.md)

งานพิสูจน์ถัดไปต้องเป็น unseen validation v03 ด้วย target ใหม่ เพราะ Redis/Grafana จาก v02 ถูกนำเข้า train แล้ว

## Unseen Validation v03

v03 เป็นรอบที่มีประโยชน์เพราะเจอ failure จริง:

- unknown target ส่ง `unknown_product_detected=0`
- Solr negative ขาด canonical `velocity_disabled`
- CouchDB ใช้ alias ไม่ตรง schema
- Tomcat AJP แพ้ Nexus เพราะ generic signal bias

หลังแก้ runtime guard แล้ว corrected evaluation บน v03 ผ่านครบ 11/11 แต่ต้องตีความว่าเป็น post-hoc fix ไม่ใช่ production accuracy

งานถัดไปคือ v04 target ใหม่ เพื่อพิสูจน์ว่า guard/schema ใหม่ generalize ได้จริง

## Honest Unseen Validation v04

v04 ใช้ target ใหม่ 12 ตัวและ corrected evaluation ล่าสุดได้:

| Metric | Corrected Result |
| --- | ---: |
| Gate accuracy | 0.9167 |
| Gate FP | 0 |
| Gate FN | 1 |
| Known-positive Ranker Top-1 | 0.7500 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 0.9167 |
| Strict flow accuracy | 0.9167 |

สรุป: unknown guard ดีขึ้นจริง แต่ยังไม่ 100% เพราะ Solr positive ขาด Velocity evidence ที่ runtime ต้องใช้ จึงต้องทำ Solr feature backfill ต่อ

## Solr Velocity Backfill

รอบ `dec-solr-velocity-backfill-2026-09-02` ได้ Solr evidence เพิ่ม:

| Result | Count |
| --- | ---: |
| clean positive | 2 |
| clean negative | 1 |
| inconclusive/quarantined | 1 |

ยังไม่ retrain ทันที เพราะ Solr negative ที่สะอาดมีแค่ 1 ตัว ต้องหา negative เพิ่มอีกอย่างน้อย 1 ตัวก่อน

## Solr Negative Backfill

รอบ `dec-solr-negative-backfill-2026-09-02` เติม Solr negative control เพิ่ม 2 targets และ safe-to-merge ทั้งคู่:

- `solr_negative_v04_1`
- `solr_negative_v04_2`

หลังรวมกับ Solr positive backfill เดิม ได้ dataset รุ่นทดลอง 72 targets:

- [reports/evaluations/solr-negative-backfill-v01/target-exploitability-with-solr-backfill-v01.csv](reports/evaluations/solr-negative-backfill-v01/target-exploitability-with-solr-backfill-v01.csv)
- [reports/evaluations/solr-negative-backfill-v01/SOLR-NEGATIVE-BACKFILL-CODEX-REVIEW-TH.md](reports/evaluations/solr-negative-backfill-v01/SOLR-NEGATIVE-BACKFILL-CODEX-REVIEW-TH.md)

ผล train รุ่นทดลอง:

| Metric | Result |
| --- | ---: |
| Gate LOO accuracy | 0.9444 |
| Gate FP/FN | 4 / 0 |
| Ranker LOO Top-1 | 0.9000 |

ยังไม่ promote เป็น default runtime เพราะ Gate FP เพิ่มจาก runtime เดิม จุดที่ต้องแก้ต่อคือ Solr feature extractor/probe ให้ส่ง `velocity_enabled`, `velocity_disabled`, `config_api_accessible` ให้ถูกตั้งแต่แรก

## Solr Schema Fix

รอบ `dec-solr-schema-fix-2026-09-02` แก้ Solr feature schema แล้ว rerun Solr-only validation ได้ 5/5 safe-to-merge:

- positive 2 targets
- negative 3 targets
- quarantine 0 targets

รายงานหลัก:

- [reports/evaluations/solr-schema-fix-v01/SOLR-SCHEMA-FIX-CODEX-REVIEW-TH.md](reports/evaluations/solr-schema-fix-v01/SOLR-SCHEMA-FIX-CODEX-REVIEW-TH.md)
- [reports/evaluations/solr-schema-fix-v01/target-exploitability-with-solr-schema-fix-v01.csv](reports/evaluations/solr-schema-fix-v01/target-exploitability-with-solr-schema-fix-v01.csv)

ผล train รุ่นทดลอง:

| Metric | Result |
| --- | ---: |
| Gate LOO accuracy | 0.9444 |
| Gate FP/FN | 4 / 0 |
| Ranker LOO Top-1 | 0.9000 |
| Honest v04 safety | 0.9167 |

ยังไม่ promote เป็น default runtime เพราะ Gate FP เพิ่มจาก runtime เดิม แม้ Ranker ดีขึ้นเล็กน้อย

หลังทำ FP investigation พบว่า FP 4 ตัวเป็น Solr negative ที่มี `velocity_disabled=1` แต่ยังมี generic Solr/core/access signal สูง จึงเพิ่ม runtime guard ให้ Solr ที่ `velocity_disabled=1` และ `velocity_enabled=0` ถูกลดเป็น `low_confidence` ก่อนส่งไป exploit verification

ผลทดสอบเฉพาะ Solr schema-fixed 5 targets หลัง guard:

| Metric | Result |
| --- | ---: |
| Gate FP/FN | 0 / 0 |
| Ranker Top-1 | 1.0000 |
| Safety flow | 1.0000 |

ตัวเลขนี้เป็น Solr-only sanity check ไม่ใช่ production accuracy

## Unseen Solr Schema Validation

รอบ `dec-unseen-solr-schema-validation-2026-09-02` ทดสอบ Solr target ใหม่ 4 ตัวหลังแก้ extractor แล้ว โดยยังไม่เอาเข้า train ก่อน:

- positive 2/2
- negative 2/2
- quarantine 0

ผล runtime evaluation ทั้ง default runtime และ Solr schema-fix model:

| Metric | Result |
| --- | ---: |
| Gate FP/FN | 0 / 0 |
| Ranker Top-1 | 1.0000 |
| Safety flow | 1.0000 |

รายงานหลัก:

- [reports/evaluations/unseen-solr-schema-validation-v01/UNSEEN-SOLR-SCHEMA-CODEX-REVIEW-TH.md](reports/evaluations/unseen-solr-schema-validation-v01/UNSEEN-SOLR-SCHEMA-CODEX-REVIEW-TH.md)

ข้อควรระวัง: นี่เป็น Solr-only unseen validation 4 targets ไม่ใช่คะแนน production ของทั้งระบบ

## Multi-family Unseen Validation

รอบ `dec-multifamily-unseen-validation-2026-09-02` ทดสอบ unseen targets ใหม่ 10 ตัว ครอบคลุม Redis, Grafana, Tomcat PUT, Tomcat AJP และ CouchDB โดยยังไม่เอาเข้า train ก่อน:

| Family | Positive | Negative | Result |
| --- | ---: | ---: | --- |
| Redis | 1 | 1 | 2/2 safe_to_merge |
| Grafana | 1 | 1 | 2/2 safe_to_merge |
| Tomcat PUT | 1 | 1 | 2/2 safe_to_merge |
| Tomcat AJP | 1 | 1 | 2/2 safe_to_merge |
| CouchDB | 1 | 1 | 2/2 safe_to_merge |

ผล runtime evaluation ด้วย default runtime:

| Metric | Result |
| --- | ---: |
| Gate FP/FN | 0 / 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Safety flow | 1.0000 |
| Strict flow | 1.0000 |

รายงานหลัก:

- [reports/evaluations/multifamily-unseen-validation-v01/UNSEEN-MULTIFAMILY-CODEX-REVIEW-TH.md](reports/evaluations/multifamily-unseen-validation-v01/UNSEEN-MULTIFAMILY-CODEX-REVIEW-TH.md)

ข้อควรระวัง: ผลนี้เป็น multi-family unseen validation ชุดเล็ก 10 targets และไม่มี unknown-family target จึงบอกได้ว่า prototype ดีขึ้นชัดใน scope นี้ แต่ยังไม่ใช่ production accuracy

## Ranker Safety Guard

หลัง multi-family unseen validation เพิ่ม runtime guard เพื่อให้ Ranker ไม่มั่นใจเกินไปเมื่อหลักฐานบางหรือคะแนน family สูสีกัน:

- เพิ่ม `ranker.confidence` เพื่อดูว่าอันดับหนึ่งชนะอันดับสองชัดไหม
- เพิ่ม `ranker.family_readiness` เพื่อดูว่ามีหลักฐานเฉพาะ family พอไหม
- ถ้าคะแนนสูสีหรือหลักฐานเฉพาะ family ไม่พอ จะลดจากพร้อมตรวจต่อเป็น manual triage

Regression ด้วย default runtime ยังไม่ถอยบนชุดที่มี feature สะอาด:

| Validation set | Gate FP/FN | Ranker Top-1 | Safety flow | Strict flow |
| --- | ---: | ---: | ---: | ---: |
| Multi-family unseen v01 | 0 / 0 | 1.0000 | 1.0000 | 1.0000 |
| Unseen Solr schema v01 | 0 / 0 | 1.0000 | 1.0000 | 1.0000 |

รายงานหลัก:

- [reports/evaluations/ranker-safety-guard-v01/RANKER-SAFETY-GUARD-CODEX-REVIEW-TH.md](reports/evaluations/ranker-safety-guard-v01/RANKER-SAFETY-GUARD-CODEX-REVIEW-TH.md)
- [reports/plans/opencode-unknown-family-validation-v01/OPENCODE-PROMPT-TH.md](reports/plans/opencode-unknown-family-validation-v01/OPENCODE-PROMPT-TH.md)

## Ranker Guard Unknown Validation

รอบ `dec-ranker-guard-unknown-validation-2026-09-02` ทดสอบ guard จริงกับ 24 targets:

| กลุ่ม | จำนวน | ผล |
| --- | ---: | --- |
| Known family | 12 | 12/12 safe |
| Unknown family | 6 | 6/6 ถูกส่งไป unknown triage |
| Weak/noisy | 6 | 6/6 ไม่ถูกปล่อยเป็น exploit |

ตอน runtime แรกเจอ failure สำคัญ 1 จุด: `redis_weak_guard_01` มี Redis signal บางส่วนแต่ `lua_available=0` และ `known_family_signal_count=0` ยังถูกปล่อยเป็น `ready_for_safe_verification`

จึงเพิ่ม guard ให้ Redis/Grafana weak evidence ถูกลดเป็น `low_confidence` และให้ `known_family_signal_count=0` ทำให้ `family_readiness.ready=false`

ผลหลังแก้:

| Metric | Result |
| --- | ---: |
| Gate FP/FN | 0 / 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Unknown-family rejected | 1.0000 |
| Safety flow | 1.0000 |
| Strict flow | 1.0000 |

รายงานหลัก:

- [reports/evaluations/ranker-guard-unknown-validation-v01/RANKER-GUARD-UNKNOWN-CODEX-REVIEW-TH.md](reports/evaluations/ranker-guard-unknown-validation-v01/RANKER-GUARD-UNKNOWN-CODEX-REVIEW-TH.md)

ข้อควรระวัง: ชุดนี้ควรเก็บเป็น validation/regression set ก่อน ยังไม่ควรเอาไป train ทับทันที และยังไม่ควร claim production-ready 100%

## Runtime Regression

เพิ่ม runner สำหรับตรวจ baseline ซ้ำก่อน merge/train:

```text
scripts/run_runtime_regression.py
```

ผลรันล่าสุดด้วย `runtime/models/prototype`:

| Suite | Status |
| --- | --- |
| `ranker_guard_unknown_v01` | pass |
| `multifamily_unseen_v01` | pass |
| `unseen_solr_schema_v01` | pass |

สรุป: 3/3 suites ผ่าน, Gate FP/FN ยัง 0, Safety/Strict ยัง 1.0000

รายงานผล:

- [reports/regression/runtime-current/RUNTIME-REGRESSION-RESULT-TH.md](reports/regression/runtime-current/RUNTIME-REGRESSION-RESULT-TH.md)

## LLM Decision Explainer

เพิ่มสคริปต์แปลง runtime prediction JSON เป็นคำอธิบายสำหรับ LLM/operator:

```text
scripts/explain_runtime_decision.py
```

ตัวอย่าง output:

```text
examples/output/redis_likely_exploitable_explanation.md
examples/output/redis_weak_explanation.md
examples/output/grafana_blocked_explanation.md
examples/output/unknown_wordpress_explanation.md
examples/output/negative_control_explanation.md
```

หน้าที่คือบังคับ flow ให้อ่าน `final_decision` + `runtime/llm-action-policy.json` ก่อน ไม่ใช่ให้ LLM ตัดสินจาก score เดี่ยว ๆ

## Shared Validation Runtime v01

นำผล shared validation จาก `C:\Users\rapii\Desktop\kali-share\dataset\evaluations\shared-validation-runtime-v01` เข้า repo แล้วรันซ้ำด้วย runtime ปัจจุบัน

ผล current runtime:

| Metric | Result |
| --- | ---: |
| Total targets | 56 |
| Gate TP/FP/TN/FN | 28 / 0 / 28 / 0 |
| Gate precision/recall/F1 | 1.0000 / 1.0000 / 1.0000 |
| Known-positive Ranker Top-1 | 19/19 |
| Known-positive Ranker Top-3 | 19/19 |
| Unknown-family rejected | 9/9 |
| Safety flow | 56/56 |
| Strict flow | 56/56 |

แก้เพิ่ม 2 จุด:

- evaluator นับ `unknown_family_positive` เป็น unknown-family positive ได้ถูกต้อง
- unknown guard ไม่ force known family เป็น unknown ถ้ามี family-specific positive signal แล้ว

รายงานหลัก:

- [reports/evaluations/shared-validation-runtime-v01/SHARED-VALIDATION-CURRENT-RUNTIME-TH.md](reports/evaluations/shared-validation-runtime-v01/SHARED-VALIDATION-CURRENT-RUNTIME-TH.md)

ข้อควรระวัง: ผล 1.0000 นี้เป็น subset/sanity validation ไม่ใช่ production accuracy

เพิ่ม CVE/Module Resolver mapping และ priority report สำหรับเครื่อง 2:

| Queue | Count |
| --- | ---: |
| ready_for_safe_verification | 17 |
| manual_triage_before_exploit | 2 |
| unknown_family_triage | 9 |
| needs_more_evidence | 6 |
| do_not_exploit_now | 22 |

ไฟล์หลัก:

- [runtime/resolver/family-cve-module-map.json](runtime/resolver/family-cve-module-map.json)
- [scripts/generate_priority_report.py](scripts/generate_priority_report.py)
- [reports/evaluations/shared-validation-runtime-v01/priority-current/PRIORITY-REPORT-TH.md](reports/evaluations/shared-validation-runtime-v01/priority-current/PRIORITY-REPORT-TH.md)

เพิ่ม safe verification plan top 5 สำหรับส่งต่อให้ Kali VM OpenCode:

- [scripts/build_safe_verification_plan.py](scripts/build_safe_verification_plan.py)
- [reports/evaluations/shared-validation-runtime-v01/verification-plan-v01/SAFE-VERIFICATION-PLAN-TH.md](reports/evaluations/shared-validation-runtime-v01/verification-plan-v01/SAFE-VERIFICATION-PLAN-TH.md)
- [reports/evaluations/shared-validation-runtime-v01/verification-plan-v01/verification-plan.jsonl](reports/evaluations/shared-validation-runtime-v01/verification-plan-v01/verification-plan.jsonl)

## CVE Resolver Runtime v01

เพิ่มชั้นที่ 3 ของ runtime แล้ว:

```text
Gate -> Family Ranker -> CVE/Module Resolver
```

Resolver ใช้ rule-scoring เพื่อจัดอันดับ CVE/module ภายใน family ที่ Ranker เลือก ไม่ให้ ML ทาย CVE ตรง ๆ ตั้งแต่แรก

ไฟล์หลัก:

- [runtime/resolver/cve-ranking-rules.json](runtime/resolver/cve-ranking-rules.json)
- [scripts/rank_cve_candidates.py](scripts/rank_cve_candidates.py)
- [reports/evaluations/vulhub-50-target-scan-v01/CVE-RESOLVER-RUNTIME-RESULT-TH.md](reports/evaluations/vulhub-50-target-scan-v01/CVE-RESOLVER-RUNTIME-RESULT-TH.md)

ผลบน Vulhub 50 batch:

| Metric | Result |
| --- | ---: |
| Known-positive CVE Resolver coverage | 14/14 |
| Known-positive CVE Resolver Top-1 | 14/14 |
| Regression suites | 5/5 pass |

ข้อควรระวัง: CVE Resolver Top-1 1.0000 เป็นผลจาก lab mapping ที่มีเฉลยชัด ไม่ใช่ production accuracy โลกจริง
