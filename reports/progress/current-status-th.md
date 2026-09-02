# สถานะล่าสุดของงาน ML

## สรุปสถานะ

ตอนนี้งาน ML เดินมาถึง **ML-only Exploitability Gate + XGBoost Family Ranker prototype**

ถือว่าผ่านเป้าหมาย prototype ระดับต้นในแง่ pipeline เพราะ:

- ไม่พึ่ง Rule Gate เป็นตัวตัดสินหลัก
- train/evaluate/infer ได้
- มี model artifact
- มี threshold tuning
- มี feature schema
- มี dataset target-level
- Gate ผ่านเกณฑ์ `precondition_only`
- Family Ranker หลัง backfill ทาย family ได้ดีขึ้นชัดเจน

## Dataset ล่าสุด

| รายการ | จำนวน |
| --- | ---: |
| validated_positive | 20 |
| validated_negative | 20 |
| inconclusive | 15 |
| train/evaluate targets | 65 |
| gate/ranking features ล่าสุด | 119 |

## ผล v0.2

| Metric | Result |
| --- | ---: |
| Accuracy | 1.000 |
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| False Positive | 0 |
| False Negative | 0 |

## การตีความ

ผลนี้แปลว่า v0.2 ทำงานดีมากบน dataset ปัจจุบัน แต่ยังไม่ควรสรุปว่าใช้งานจริงได้กับ target ใหม่ทั้งหมด เพราะ dataset ยังเล็กและ feature บางตัวอาจมีความใกล้กับ label

คำพูดที่เหมาะสม:

```text
โมเดล ML-only Gate v0.2 สามารถทำงานได้คงที่บน controlled dataset และพร้อมเข้าสู่ขั้นตอน unseen target validation
```

ไม่ควรพูดว่า:

```text
โมเดลแม่น 100% แล้ว
```

## ผล Targeted Pair Fix v01

รอบนี้รวมเฉพาะ feature records ที่มี `label_consistency=consistent` จาก `dec-targeted-pair-fix-2026-08-31`

| รายการ | จำนวน |
| --- | ---: |
| targets ที่มี pair-fix feature ใช้ได้ | 3 |
| records ที่ skip เพราะ inconsistent | 11 |
| features หลัง merge | 79 |

ผล `strict_precheck` ยังไม่ดีขึ้น:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.500 |
| Precision | 0.500 |
| Recall | 1.000 |
| F1 | 0.667 |
| False Positive | 20 |
| False Negative | 0 |

ความหมาย: โมเดลยังมอง negative เป็น exploit ได้ง่ายเกินไป เพราะ evidence ฝั่ง precheck ที่ reliable ยังน้อย ต้องแก้ label consistency และเก็บ pair features เพิ่มก่อน

## งานถัดไป

1. freeze baseline ชุดนี้เป็น prototype
2. ทำ inference flow รวม Gate -> Family Ranker
3. ทำ output ภาษาไทยว่าแนะนำ exploit family ไหน เพราะ evidence อะไร
4. ทดสอบ unseen target ใหม่ 5-10 ตัว โดยให้ model ทายก่อน แล้วค่อยใช้ Metasploit/manual PoC เฉลย
5. เก็บ evidence เพิ่มเฉพาะ family ที่ยังพลาด เช่น Joomla, NextJS, Tomcat PUT

## Audit ล่าสุด

เพิ่มสคริปต์ `scripts/audit_gate_features.py` เพื่อเช็คว่า feature ไหนอาจทำให้คะแนนสูงเกินจริง โดยเฉพาะ feature ที่รู้หลังยิง exploit หรือหลังเขียนผล validation แล้ว งานถัดไปควรวัด `strict_precheck` ที่ตัด feature กลุ่มนี้ออกก่อน

## Light Backfill ล่าสุด

นำผล `dec-precheck-light-backfill-2026-08-31` มา merge แล้วได้ dataset 40 targets / 68 features โดยมี target ที่ backfill จริง 15 ตัว ผลยังชี้ว่า `strict_precheck` และ `scanner_only` มี FP=20 เมื่อเลือก threshold แบบไม่ยอมให้ FN เกิด แปลว่า feature ใหม่ช่วยเรื่องความสะอาดของข้อมูล แต่ยังไม่พอให้โมเดลแยก `no_exploit` ได้ ต้องเพิ่ม targeted precondition probes ต่อ

## Targeted Probe Plan

เพิ่มแผน `reports/plans/targeted-precondition-v01/` จาก false positive ของ `strict_precheck` ได้ 60 probe tasks ครอบคลุม 20 false positive targets เป้าหมายคือเก็บ feature ที่ผูกกับ exploit condition จริง เช่น `method_put_rejected`, `ajp_port_closed`, `auth_required`, `endpoint_missing`, `version_patched` เพื่อให้โมเดลลด FP โดยไม่ต้องพึ่ง `negative_evidence_count`

ปรับเพิ่มเป็น `reports/plans/targeted-precondition-v02/` เพื่อให้อ่านง่ายและทำงานจริงง่ายขึ้น โดยตัด probe กว้าง ๆ ที่ไม่จำเป็นออก เช่น `generic_*`, default path discovery ทั่วไป, target ที่ไม่มี lab ตรง และเน้นเฉพาะ precondition ที่ตอบว่า exploit family นั้นผ่านหรือไม่ผ่านจริง

## Targeted Precondition Result

รวมผล `dec-targeted-precondition-v02-2026-08-31` แล้วได้ dataset 40 targets / 78 features แต่ `strict_precheck` ยัง FP=20 ที่ threshold 0.10 สาเหตุหลักคือ targeted features ยัง sparse เกินไปและส่วนใหญ่มีเฉพาะ negative side งานถัดไปต้องเก็บ targeted precondition ฝั่ง positive เป็นคู่เทียบ เช่น `method_put_allowed` เทียบกับ `method_put_rejected`, `ajp_port_open` เทียบกับ `ajp_port_closed`, `velocity_enabled` เทียบกับ `velocity_disabled`

## Targeted Pair Quality Audit

ผล `dec-targeted-precondition-pairs-2026-08-31` ยังไม่ควรนำเข้า train ตรง ๆ เพราะมี positive targets หลายตัวที่ได้ negative evidence เช่น `thinkphp_5-rce` ได้ `invokefunction_not_found`, `solr_CVE-2019-17558` ได้ `velocity_disabled`, `couchdb_CVE-2017-12635` ได้ `auth_required`, `shiro_CVE-2016-4437` ได้ `rememberme_not_seen` จึงต้อง quarantine แล้วแก้ lab/probe เฉพาะ family ก่อน

## Targeted Pair Fix Result

ผล `dec-targeted-pair-fix-2026-08-31` แก้ได้บางส่วน เช่น `solr_CVE-2019-17558`, `shiro_CVE-2016-4437`, และ `redis_non_vulnerable` แต่ยังมี target ที่ label/evidence inconsistent อยู่ เช่น `thinkphp_5-rce`, `couchdb_CVE-2017-12635`, `nginx_CVE-2017-7529`, `redis_auth_non_vulnerable`

ใช้ได้เฉพาะ records ที่ consistent เท่านั้น รายละเอียดอยู่ที่ `reports/evaluations/targeted-pair-fix-v01/`

## Strict Precheck Improve Result

ผล `dec-strict-precheck-improve-2026-08-31` มี 11 targets แต่ใช้ train ได้อย่างปลอดภัย 4 targets:

- `redis_auth_non_vulnerable`
- `tomcat_non_vulnerable`
- `solr_CVE-2019-17558`
- `shiro_CVE-2016-4437`

หลัง merge แล้วได้ 40 targets / 86 features แต่ผล `strict_precheck` ยังไม่ผ่าน:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.500 |
| Precision | 0.500 |
| Recall | 1.000 |
| F1 | 0.667 |
| False Positive | 20 |
| False Negative | 0 |

สรุป: ยังไม่ควรหยุดงาน ML core เพราะ profile ที่ใกล้ใช้งานจริงที่สุดยังแยก negative ไม่ได้ ต้องแก้ label consistency และเก็บคู่ positive/negative ที่สะอาดกว่านี้

## Label Consistency Fix Result

ผล `dec-label-consistency-fix-2026-08-31` ตรวจ 6 targets และเหลือ safe to merge เพียง 1 target คือ `tomcat_CVE-2020-1938`

quarantine 5 targets:

- `tomcat_CVE-2017-12615`
- `solr_non_vulnerable`
- `shiro_non_vulnerable`
- `thinkphp_5-rce`
- `couchdb_CVE-2017-12635`

หลัง merge แล้วได้ 40 targets / 87 features แต่ผล `strict_precheck` ยังเหมือนเดิม:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.500 |
| Precision | 0.500 |
| Recall | 1.000 |
| F1 | 0.667 |
| False Positive | 20 |
| False Negative | 0 |

ความหมาย: รอบนี้ไม่ได้ทำให้คะแนนดีขึ้น แต่ทำให้รู้ว่า dataset เดิมมี label/control target ที่ต้องแก้จริง ก่อนจะคาดหวังให้ ML แยก exploit/no-exploit ได้

## Clean Control Labs Result

ผล `dec-clean-control-labs-2026-09-01` ได้ clean CouchDB pair และเพิ่มเป็น target ใหม่ใน dataset:

- `couchdb_admin_party_clean` เป็น positive
- `couchdb_auth_required_clean` เป็น negative

หลัง merge แล้ว dataset เพิ่มเป็น 42 targets / 90 features แต่ `strict_precheck` ยังไม่ผ่าน:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.500 |
| Precision | 0.500 |
| Recall | 1.000 |
| F1 | 0.667 |
| False Positive | 21 |
| False Negative | 0 |

`couchdb_auth_required_clean` ยังถูกทำนายผิดเป็น exploit แปลว่าโมเดลยังต้องการ clean positive/negative pair จากหลาย family กว่านี้ ไม่ใช่แค่ CouchDB คู่เดียว

## Clean Control Labs v02 Result

ผล `dec-clean-control-labs-2026-09-01` รุ่น Precondition Focus เพิ่ม target ใหม่ได้ 9 ตัว ทำให้ dataset เป็น 49 targets / 90 features

clean pairs ที่เพิ่ม:

- Tomcat PUT
- Tomcat AJP
- Shiro default key

ผลล่าสุด:

| Profile | F1 | FP | FN |
| --- | ---: | ---: | ---: |
| full_v02 | 0.885 | 6 | 0 |
| strict_precheck | 0.648 | 25 | 0 |

สรุป: test เริ่มสมจริงขึ้นเพราะ full profile ไม่ได้ 1.000 แล้ว แต่ `strict_precheck` ยังไม่ผ่าน ต้องเพิ่ม clean positive สำหรับ Solr/ThinkPHP/CouchDB และปรับ profile ให้เน้น precondition มากขึ้น

## Missing Positive Controls Result

ผล `dec-missing-positive-controls-2026-09-01` เพิ่ม positive controls ที่ขาดได้ 3 targets:

- `solr_velocity_positive`
- `thinkphp_invokefunction_positive`
- `couchdb_admin_party_positive`

หลัง merge แล้ว dataset เป็น 52 targets / 92 features และเพิ่ม profile ใหม่ `precondition_only`

| Profile | F1 | FP | FN |
| --- | ---: | ---: | ---: |
| strict_precheck | 0.675 | 25 | 0 |
| precondition_only | 0.788 | 14 | 0 |

สรุป: `precondition_only` ดีขึ้นชัดเจนและควรใช้เป็น candidate profile หลักรอบถัดไป แต่ยังไม่ถึงเกณฑ์หยุด เพราะ FP ยังมากกว่า 5

## Negative Control Variations Result

ผล `dec-negative-control-variations-2026-09-01` เพิ่ม negative controls 13 targets ทำให้ dataset เป็น 65 targets / 95 features

หลังเพิ่ม derived precondition features แล้ว `precondition_only` ผ่านเกณฑ์ prototype:

| Profile | F1 | FP | FN |
| --- | ---: | ---: | ---: |
| precondition_only | 0.943 | 2 | 1 |
| strict_precheck | 0.943 | 2 | 1 |
| scanner_only | 0.571 | 39 | 0 |

เกณฑ์หยุดที่ตั้งไว้คือ FP <= 5, FN <= 2, F1 >= 0.80 ซึ่งรอบนี้ผ่านแล้ว

สรุป: หยุดสแกนวนเพื่อแก้ ML core ได้แล้วในระดับ prototype งานถัดไปควร freeze baseline, ทำ clean dataset ตัด target quarantined ออก, แล้วเริ่มทำ inference/API สำหรับใช้งานจริง

## Family Ranking v01 Result

เริ่มทดสอบ XGBoost Family Ranker แล้ว โดยให้ Gate แยก exploit/no-exploit ก่อน แล้ว Ranker จัดอันดับเฉพาะ exploit family

ผลรวมยังไม่ผ่าน:

| Metric | Result |
| --- | ---: |
| Top-1 | 0.500 |
| Top-3 | 0.538 |
| Top-5 | 0.538 |
| MRR | 0.551 |

แต่ถ้าแยกเฉพาะ clean-control positive targets ที่เพิ่งเก็บมา ผลดีมาก:

| Segment | Targets | Top-1 | Top-3 | MRR |
| --- | ---: | ---: | ---: | ---: |
| clean_control_positive | 6 | 1.000 | 1.000 | 1.000 |
| original_positive | 20 | 0.350 | 0.400 | 0.417 |

สรุป: Ranker ทำงานได้บน target ที่มี precondition feature สะอาด แต่ original positives ยังต้อง backfill family-specific evidence เพิ่มก่อน

## Family Ranking Backfill v01 Result

ผล `dec-family-ranking-backfill-2026-09-01` จาก Kali/OpenCode เพิ่ม family-specific evidence ให้ original positive targets 10 ตัว และ merge เฉพาะ records ที่ safe to merge

ผลหลัง train/evaluate ใหม่:

| Metric | ก่อน backfill | หลัง backfill |
| --- | ---: | ---: |
| Top-1 | 0.500 | 0.885 |
| Top-3 | 0.539 | 0.885 |
| Top-5 | 0.539 | 0.885 |
| MRR | 0.551 | 0.897 |

ผลแยกกลุ่ม:

| Segment | Targets | Top-1 | MRR |
| --- | ---: | ---: | ---: |
| clean_control_positive | 6 | 1.000 | 1.000 |
| original_positive | 20 | 0.850 | 0.866 |

เคสที่ยังพลาดคือ `joomla_CVE-2023-23752`, `nextjs_CVE-2025-29927`, และ `tomcat_CVE-2017-12615` ซึ่งเป็น target ที่ backfill รอบนี้ quarantine หรือยังไม่มี evidence ที่เชื่อถือได้

สรุป: **ML core อยู่ระดับใช้งาน prototype ได้แล้ว** ควรหยุดสแกนวนเพื่อไล่คะแนนชั่วคราว แล้วทำ inference/API สำหรับใช้งานจริงก่อน

## Unknown Family v01 Result

ทดสอบแล้วว่า Family Ranker เป็น closed-set model ถ้าไม่มี guard จะฝืนตอบหนึ่งใน known families เสมอ แม้ target จะเป็น unknown หรือ no-exploit

เพิ่มสคริปต์ `scripts/evaluate_unknown_family.py` เพื่อวัด open-set behavior ด้วย rule จากจำนวน family-specific positive signals

ผลหลัก:

| กลุ่ม | Rule | Reject เป็น unknown |
| --- | --- | ---: |
| synthetic unknown 4 targets | ทุก rule | 4/4 |
| negative/no_exploit 39 targets | `top1_signal_decision` | 38/39 |
| negative/no_exploit 39 targets | `clean_top1_decision` | 39/39 |

ข้อแลกเปลี่ยนคือ rule ที่เข้มขึ้นจะ reject known-positive บางตัวที่ evidence ยังน้อย เช่น Nexus, Joomla, NextJS, Tomcat PUT

สรุป: ระบบจริงต้องมี output `unknown_family` หรือ `known_family_but_low_confidence` ก่อนเชื่อคำตอบจาก Ranker

## Runtime Prototype Handoff

เพิ่มชุด runtime สำหรับส่งต่อให้ฝั่ง LLM/agentic แล้ว:

```text
runtime/models/prototype/
├── gate_precondition_only.json
├── family_ranker.json
└── prototype_manifest.json
```

entrypoint ที่ควรเรียก:

```bash
python scripts/predict_prototype.py --features examples/input/redis_likely_exploitable_features.json
```

ตัวอย่าง output อยู่ใน:

```text
examples/output/
```

สรุปว่าไฟล์ไหนใช้ทำอะไร:

| กลุ่ม | ใช้ทำอะไร |
| --- | --- |
| `runtime/models/prototype/*` | model ที่ใช้จริงระดับ prototype |
| `scripts/predict_prototype.py` | ให้ LLM/agentic เรียกเพื่อ predict |
| `examples/input` / `examples/output` | ตัวอย่าง format input/output |
| `scripts/train_*.py` | ใช้ train/retrain ไม่ใช่ตัวที่ LLM ต้องเรียกทุกครั้ง |
| `reports/evaluations/*` | หลักฐานผลทดลองย้อนหลัง |

## Unseen Validation v01 Result

ผล `dec-unseen-validation-v01-2026-09-01` เป็นการทดสอบแบบโลกจริงรอบแรก เพราะ model ต้อง predict ก่อน แล้วจึง verify ทีหลัง

ผลรวม:

| Metric | Result |
| --- | ---: |
| Total targets | 10 |
| Gate accuracy | 0.600 |
| Gate TP | 4 |
| Gate FP | 4 |
| Gate TN | 2 |
| Gate FN | 0 |
| Ranker Top-1 | 1.000 |
| Unknown rejection | 1.000 |

สรุป:

- Ranker ทาย known-family variants ถูก 4/4
- Unknown guard reject unknown-family ถูก 3/3
- Gate ยัง FP กับ unknown-family และ patched nginx รวม 4 targets

ดังนั้น bottleneck รอบถัดไปคือ **Gate improvement** ไม่ใช่ Ranker

ปรับ runtime เพิ่มให้มี `final_decision` เพื่อให้ LLM อ่านผลรวมของ Gate + Ranker + Unknown Guard ได้ง่ายขึ้น

## Unseen Validation v02 Result

ผล `dec-unseen-validation-v02-2026-09-01` ทดสอบ 12 targets:

| Metric | Reported Result |
| --- | ---: |
| Completed/Total | 12/12 |
| Gate accuracy | 1.000 |
| Gate FP | 0 |
| Gate FN | 0 |
| Ranker Top-1 | 0.333 |

Codex ตรวจเพิ่มแล้วพบว่าไฟล์สรุป v02 มีข้อมูลขัดกัน: evaluation รายงาน `unknown guard 100%` แต่ prediction จริงของ unknown-family targets หลายตัวเป็น `known_family_ready` และ `ready_for_safe_verification`

แก้ runtime แล้วใน `scripts/predict_prototype.py`:

- normalize alias `is_non_http_target` เป็น `is_non_http_service`
- ถ้า `unknown_product_detected=1` และ unknown signal ไม่แพ้ known signal ให้บังคับเป็น `unknown_family_triage`

หลัง patch ทดสอบกับ `unseen_drupal_01` แล้วได้:

```text
gate.decision = likely_exploitable
ranker.decision = unknown_family
final_decision = unknown_family_triage
```

สรุป: Gate เริ่มใช้ได้ดีขึ้น แต่ Ranker ยังต้องทำ feature schema alignment โดยเฉพาะ Redis/Grafana variants ก่อน retrain รอบต่อไป

หลังเพิ่ม `scripts/evaluate_runtime_predictions.py` และ rerun จาก runtime ที่ patch แล้ว ได้ corrected metrics:

| Metric | Corrected Result |
| --- | ---: |
| Gate accuracy | 1.000 |
| Known-positive Ranker Top-1 | 0.333 |
| Unknown rejection rate | 1.000 |
| Safety flow accuracy | 1.000 |
| Strict flow accuracy | 0.833 |

ความหมาย: flow ตอนใช้งานไม่ปล่อย unknown ไปยิงมั่วแล้ว แต่ Ranker ยังผิดกับ Redis/Grafana เพราะ feature เฉพาะ family ไม่ครบ

## Ranker Schema Backfill Redis/Grafana Result

ผล `dec-ranker-schema-backfill-redis-grafana-2026-09-02` เติม feature เฉพาะ family ให้ 2 target ที่ Ranker พลาด:

- `unseen_redis_variant_01`
- `unseen_grafana_variant_01`

หลัง merge feature แล้ว rerun corrected runtime evaluation:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 1.000 |
| Known-positive Ranker Top-1 | 1.000 |
| Unknown rejection rate | 1.000 |
| Safety flow accuracy | 1.000 |
| Strict flow accuracy | 1.000 |

คำอธิบายสำคัญ: ผลนี้ไม่ได้แปลว่า production-ready หรือแม่น 100% กับ target ทั้งหมด แต่แปลว่า Ranker พลาดเพราะ Redis/Grafana feature ไม่ครบ เมื่อเติม canonical family-specific features แล้วชุด v02 ถูกทั้งหมด

งานถัดไปคือ retrain ด้วย backfill records ที่ safe to merge แล้วทดสอบ v03 ด้วย target ใหม่

## Runtime Retrain After Redis/Grafana Backfill

retrain runtime prototype แล้วด้วย dataset 67 targets:

```text
reports/evaluations/ranker-schema-backfill-redis-grafana-v01/target-exploitability-family-ranking-backfill-plus-redis-grafana.csv
```

ผล Gate LOO:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.9701 |
| Precision | 0.9333 |
| Recall | 1.0000 |
| F1 | 0.9655 |
| FP | 2 |
| FN | 0 |

ผล Ranker LOO:

| Metric | Result |
| --- | ---: |
| Top-1 | 0.8929 |
| Top-3 | 0.8929 |
| Top-5 | 0.8929 |
| MRR | 0.9035 |

default runtime ใน `runtime/models/prototype/` ถูก promote เป็นรุ่นนี้แล้ว

ข้อควรระวัง: `unseen_redis_variant_01` และ `unseen_grafana_variant_01` ไม่ใช่ unseen อีกต่อไป เพราะถูกนำเข้า training dataset แล้ว ต้องใช้ v03 targets ใหม่เท่านั้นในการพิสูจน์รอบต่อไป

## Unseen Validation v03 Result

ผล `dec-unseen-validation-v03-2026-09-02` เป็น unseen ใหม่หลัง retrain runtime:

source report ระบุ 11/12 targets completed แต่ตัวเลขบางส่วนขัดกัน จึง reconstruct JSONL จาก per-target files แล้ว rerun corrected evaluation

ก่อนแก้ runtime guard เพิ่ม:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 0.9091 |
| Gate FP | 1 |
| Gate FN | 0 |
| Known-positive Ranker Top-1 | 0.6000 |
| Unknown rejection rate | 0.0000 |
| Safety flow accuracy | 0.7273 |
| Strict flow accuracy | 0.5455 |

failure หลัก:

- unknown target ตั้ง `unknown_product_detected=0`
- Solr negative ไม่มี canonical `velocity_disabled`
- CouchDB ใช้ alias ไม่ตรง schema
- Tomcat AJP แพ้ Nexus เพราะ generic signal bias

หลังแก้ runtime guard/normalization/rerank:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 1.0000 |
| Gate FP | 0 |
| Gate FN | 0 |
| Known-positive Ranker Top-1 | 1.0000 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 1.0000 |
| Strict flow accuracy | 1.0000 |

การตีความ: นี่คือ post-hoc fix จาก v03 failure ไม่ใช่ proof ว่า production-ready ต้องทดสอบ v04 ด้วย target ใหม่หลัง feature extractor ส่ง canonical fields ให้ถูกตั้งแต่แรก

## Honest Unseen Validation v04 Result

ผล `dec-unseen-validation-v04-honest-2026-09-02` ใช้ target ใหม่ 12/12 และเป็น honest unseen หลัง runtime v03 fix

หลัง Codex rerun corrected evaluation:

| Metric | Corrected Result |
| --- | ---: |
| Gate accuracy | 0.9167 |
| Gate FP | 0 |
| Gate FN | 1 |
| Known-positive Ranker Top-1 | 0.7500 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 0.9167 |
| Strict flow accuracy | 0.9167 |

จุดดี:

- unknown-family guard ผ่าน 4/4 หลังใช้ runtime ล่าสุด
- Redis, Tomcat PUT, Grafana rank ถูก
- negative controls ไม่ถูกส่งไปยิงทันที

จุดที่ยังพลาด:

- `solr_velocity_new_01` เป็น known-positive แต่ feature ที่ส่งมาไม่มี Velocity evidence ชัด (`velocity_endpoint_found=0`, `velocity_template_accessible=0`) จึงถูกลดเป็น `needs_more_evidence`

งานถัดไปควรทำ Solr Velocity backfill แบบเจาะจงเท่านั้น ก่อน retrain หรือ claim คะแนนใหม่

## Solr Velocity Backfill v01 Result

ผล `dec-solr-velocity-backfill-2026-09-02`:

| รายการ | จำนวน |
| --- | ---: |
| tested | 4 |
| safe_to_merge | 3 |
| validated_positive | 2 |
| validated_negative | 1 |
| inconclusive | 1 |

safe to merge:

- `solr_velocity_positive_v04_fix`
- `solr_velocity_positive_alt`
- `solr_velocity_negative_disabled`

quarantine:

- `solr_velocity_negative_patched_or_blocked` เพราะ Velocity เปิดอยู่จริง ไม่ใช่ negative control

ยังไม่ควร retrain ทันที เพราะ Solr negative clean มีแค่ 1 ตัว ควรหา Solr negative เพิ่มอีก 1-2 ตัวก่อน

## Solr Negative Backfill v01 Result

ผล `dec-solr-negative-backfill-2026-09-02` เติม Solr negative control ได้ 2 targets:

| Target | Source | Status | Safe |
| --- | --- | --- | --- |
| `solr_negative_v04_1` | `solr:9.7.0` | validated_negative | true |
| `solr_negative_v04_2` | `vulhub/solr:8.2.0` | validated_negative | true |

ทั้งสองตัวมี core จริง แต่ Velocity ใช้งานไม่ได้ จึงเหมาะเป็น negative control สำหรับ Solr Velocity

Codex merge Solr backfill แล้วเป็น dataset รุ่นทดลอง 72 targets:

```text
reports/evaluations/solr-negative-backfill-v01/target-exploitability-with-solr-backfill-v01.csv
```

ผล train runtime รุ่นทดลอง:

| Metric | Result |
| --- | ---: |
| Gate LOO accuracy | 0.9444 |
| Gate FP | 4 |
| Gate FN | 0 |
| Ranker LOO Top-1 | 0.9000 |

เทียบกับ runtime เดิม Gate แย่ลงเพราะ FP เพิ่ม แม้ Ranker ดีขึ้นเล็กน้อย จึงยังไม่ promote เป็น default runtime

rerun honest v04 ด้วย model รุ่นทดลองแล้วยังได้:

| Metric | Result |
| --- | ---: |
| Gate accuracy | 0.9167 |
| Gate FP | 0 |
| Gate FN | 1 |
| Known-positive Ranker Top-1 | 0.7500 |
| Unknown rejection rate | 1.0000 |
| Safety flow accuracy | 0.9167 |
| Strict flow accuracy | 0.9167 |

สรุป: Solr negative data พร้อมใช้แล้ว แต่ failure หลักยังอยู่ที่ feature extractor ของ Solr positive ต้องส่ง `velocity_enabled/config_api_accessible` ให้ถูกตั้งแต่แรก และต้อง tune Gate เพื่อลด FP ก่อน promote
