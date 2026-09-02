# อ่าน repo นี้ยังไง

ไฟล์นี้เป็นสารบัญหลักของ repo `chimera-ml-progress` เพื่อแยกให้ชัดว่าไฟล์ไหนคือเอกสารอธิบาย ไฟล์ไหนคือความคืบหน้า ไฟล์ไหนคือผลทดลอง และไฟล์ไหนยังไม่ควรนำไป train

## ถ้าเพิ่งเข้ามาอ่าน

อ่านตามลำดับนี้:

1. `README.md`
2. `reports/progress/current-status-th.md`
3. `runtime/README-TH.md`
4. `docs/09-llm-handoff-runtime-th.md`
5. `docs/10-ml-from-zero-th.md`
6. `docs/11-ml-runtime-integration-contract-th.md`
7. `docs/12-llm-decision-explainer-th.md`
8. `docs/08-workflow-responsibilities-th.md`
9. `docs/07-feature-catalog-th.md`

## หมวดเอกสาร

| path | หน้าที่ |
| --- | --- |
| `docs/01-project-scope-th.md` | อธิบายขอบเขตงาน ML ของโปรเจกต์ |
| `docs/02-timeline-th.md` | ลำดับว่าเราทำอะไรไปแล้ว |
| `docs/03-training-and-evaluation-th.md` | วิธี train/test และความหมายของ metric |
| `docs/04-feature-schema-th.md` | schema feature และเหตุผลที่ใช้ |
| `docs/05-lessons-learned-th.md` | สิ่งที่พลาดและบทเรียน |
| `docs/06-scanning-tools-th.md` | เครื่องมือที่ใช้เก็บ dataset และเครื่องมือที่จะใช้จริง |
| `docs/07-feature-catalog-th.md` | รายการ feature ทั้งหมด แยก precheck/postcheck/leak-risk |
| `docs/08-workflow-responsibilities-th.md` | หน้าที่ของ Codex, OpenCode, scanner, ML และ Metasploit |
| `docs/09-llm-handoff-runtime-th.md` | วิธีส่งต่อให้ฝั่ง LLM/agentic และไฟล์ไหนคือ runtime ใช้จริง |
| `docs/10-ml-from-zero-th.md` | คู่มือสอนจากศูนย์ว่า ML ในงานนี้คืออะไร train ยังไง metric แปลว่าอะไร และต่อ LLM ยังไง |
| `docs/11-ml-runtime-integration-contract-th.md` | contract ระหว่าง scanner, ML runtime และ LLM พร้อม input/output examples และ checklist ก่อน train/promote |
| `docs/12-llm-decision-explainer-th.md` | วิธีใช้สคริปต์แปลง prediction JSON เป็นคำอธิบาย/next action สำหรับ LLM/operator |

## หมวด runtime

| path | หน้าที่ |
| --- | --- |
| `runtime/README-TH.md` | คู่มือชุด runtime prototype อ่านก่อนเชื่อมกับ LLM |
| `runtime/models/prototype/gate_precondition_only.json` | XGBoost Gate model ที่ใช้จริงระดับ prototype |
| `runtime/models/prototype/family_ranker.json` | XGBoost Family Ranker model ที่ใช้จริงระดับ prototype |
| `runtime/models/prototype/prototype_manifest.json` | manifest บอก feature, threshold, candidate families และ entrypoint |
| `examples/input/` | ตัวอย่าง feature JSON ที่ส่งเข้า ML |
| `examples/output/` | ตัวอย่าง JSON ที่ ML คืนให้ LLM |

## หมวด reports

| folder | ความหมาย |
| --- | --- |
| `reports/progress/` | สถานะล่าสุดของงาน อ่านเพื่อรู้ว่าตอนนี้อยู่ตรงไหน |
| `reports/audits/` | ตรวจคุณภาพ feature/data leak ก่อนเชื่อผล ML |
| `reports/evaluations/` | ผล train/evaluate ของแต่ละรอบ |
| `reports/plans/` | แผน probe/scan ที่ออกแบบจากปัญหาของ ML |
| `reports/quarantine/` | ข้อมูลที่ยังไม่ควรนำไป train เพราะ label/evidence ขัดกัน |

## หมวด scripts

| script | หน้าที่ |
| --- | --- |
| `scripts/build_dataset.py` | รวม raw/evidence เป็น dataset |
| `scripts/generate_gate_features.py` | สร้าง gate feature จาก evidence |
| `scripts/audit_gate_features.py` | ตรวจ feature leak/postcheck risk |
| `scripts/merge_backfill_features.py` | รวม feature ที่สแกนเพิ่มเข้า dataset เดิม |
| `scripts/train_gate_model.py` | train ML-only Gate แบบหลัก |
| `scripts/train_gate_profiles.py` | train หลาย profile เพื่อเทียบว่าพึ่ง feature รั่วไหม |
| `scripts/plan_precondition_probes.py` | สร้างแผน probe จาก false positive/false negative |
| `scripts/rank_target_two_stage.py` | ใช้ model inference target ใหม่ |
| `scripts/train_runtime_models.py` | train model runtime prototype ที่ส่งต่อให้ LLM |
| `scripts/predict_prototype.py` | entrypoint ใช้จริง รับ feature JSON แล้วคืน Gate + Ranker + Unknown Guard |
| `scripts/evaluate_unknown_family.py` | ทดสอบ unknown-family behavior ของ Ranker |

## สถานะข้อมูลที่ควรจำ

ตอนนี้ยังไม่ควรพูดว่า ML แม่น 100% เพราะ dataset ยังเล็กและยังต้องทดสอบ unseen target เพิ่ม

ผลที่ควรใช้เป็น baseline คือ runtime prototype:

- Gate: `precondition_only`
- Ranker: `family_ranker`
- Unknown guard: logic ใน `scripts/predict_prototype.py`

ส่วน `reports/evaluations/*` คือประวัติการทดลองย้อนหลัง ไม่ใช่ entrypoint ที่ LLM ต้องเรียกทุกครั้ง

## ข้อมูลที่ห้ามใช้ train ก่อนแก้

ข้อมูลใน `reports/quarantine/` คือข้อมูลที่ตรวจพบว่า label กับ evidence อาจขัดกัน เช่น positive target แต่ probe ได้ negative evidence ห้ามเอาเข้า train ตรง ๆ จนกว่าจะ recheck lab/probe แล้ว