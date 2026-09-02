# ML Runtime Integration Contract

เอกสารนี้คือสัญญากลางระหว่าง scanner, ML runtime และ LLM/agent

เป้าหมายคือทำให้แต่ละฝั่งคุยกันด้วย format เดียวกัน เวลาข้อมูลจากเครื่องสแกนเข้ามาเยอะ ๆ จะได้ไม่ต้องปรับมือทุก batch

## ภาพรวม

ภาษาคน:

```text
scanner มีหน้าที่เก็บหลักฐานและแปลงเป็น feature
ML runtime มีหน้าที่ตัดสินจาก feature
LLM มีหน้าที่อธิบายผลและเลือก next action อย่างปลอดภัย
```

flow:

```text
scanner evidence
  -> feature JSON
  -> scripts/predict_prototype.py
  -> runtime JSON result
  -> LLM/operator decision
```

## Input Contract

หนึ่ง target ต้องส่งเป็น flat JSON object

ขั้นต่ำต้องมี:

```json
{
  "target_id": "example_target",
  "service_port": 8080,
  "is_http_target": 1,
  "is_non_http_service": 0,
  "version_in_vulnerable_range": 1,
  "auth_required": 0,
  "no_auth_required": 1,
  "known_family_signal_count": 1,
  "unknown_family_signal_count": 0
}
```

กฎ:

- `1` แปลว่า พบ/จริง/ใช่
- `0` แปลว่า ไม่พบ/ไม่จริง/ไม่ใช่
- ห้ามส่ง nested object ให้ model โดยตรง
- field ที่ไม่มี runtime จะอ่านเป็น 0
- field ที่เป็น metadata เช่น `cve`, `epss_score`, `in_cisa_kev` ใส่ได้ แต่ runtime model ปัจจุบันยังไม่ใช้ตัดสินโดยตรง

## Required Families

ถ้า scanner คิดว่า target อยู่ใน family ที่ runtime รู้จัก ให้ส่ง family-specific signals ให้ครบที่สุด

| Family | Feature สำคัญ |
| --- | --- |
| Redis | `redis_detected`, `redis_info_accessible`, `lua_available` |
| Grafana | `grafana_detected`, `public_plugin_path_accessible`, `path_traversal_candidate_found` |
| Solr | `solr_detected`, `solr_core_found`, `velocity_enabled`, `config_api_accessible` |
| Tomcat PUT | `method_put_allowed`, `jsp_upload_candidate` |
| Tomcat AJP | `ajp_port_open` |
| CouchDB | `couchdb_detected`, `admin_party_enabled`, `config_accessible`, `users_db_accessible` |

ถ้ามีแค่ generic signal เช่น version หรือ endpoint แต่ไม่มี family-specific signal ให้ตั้ง:

```text
known_family_signal_count = 0
```

เพื่อให้ runtime guard ไม่เชื่อ Ranker ง่ายเกินไป

## Unknown-family Contract

ถ้า scanner เจอ product ที่ Ranker ยังไม่รู้จัก เช่น Drupal, Laravel, Jetty, WordPress, PHP-CGI, JBoss ให้ส่ง:

```json
{
  "unknown_product_detected": 1,
  "unknown_family_signal_count": 2,
  "known_family_signal_count": 0
}
```

ผลที่ควรได้:

```text
final_decision = unknown_family_triage
```

หมายความว่า target อาจมีประเด็น แต่ห้ามฝืนเลือก exploit family จาก 16 family ที่ model รู้จัก

## Output Contract

runtime จะคืน JSON ประมาณนี้:

```json
{
  "target_id": "example_target",
  "gate": {
    "model": "gate_precondition_only",
    "score": 0.93,
    "threshold": 0.15,
    "decision": "likely_exploitable"
  },
  "ranker": {
    "model": "family_ranker",
    "decision": "known_family_ready",
    "confidence": {
      "level": "clear_margin",
      "margin": 2.48
    },
    "family_readiness": {
      "ready": true,
      "specific_positive_signals": ["lua_available"]
    },
    "top_families": []
  },
  "final_decision": "ready_for_safe_verification",
  "recommended_next_action": "run_safe_metasploit_check_or_manual_probe",
  "reason_features": [],
  "schema_warnings": []
}
```

LLM ต้องอ่าน `final_decision` เป็นหลักก่อนอ่าน score

ถ้าต้องการ policy แบบ machine-readable ให้ใช้:

```text
runtime/llm-action-policy.json
```

## Decision Policy

| final_decision | ภาษาคน | action |
| --- | --- | --- |
| `do_not_exploit_now` | ยังไม่ควรตรวจ exploit ต่อ | หยุดหรือเก็บ evidence เพิ่ม |
| `needs_more_evidence` | หลักฐานยังไม่พอ | ให้ scanner probe เพิ่ม |
| `ready_for_safe_verification` | พร้อมตรวจยืนยันแบบปลอดภัย | เสนอ safe check/manual probe หลัง approval |
| `manual_triage_before_exploit` | มีสัญญาณแต่ยังมี blocker/ไม่มั่นใจ | ให้คนตรวจก่อน |
| `unknown_family_triage` | อยู่นอก family ที่ model รู้จัก | ห้ามฝืนเลือก known exploit family |

## Example Cases

| Case | Input | Expected final_decision |
| --- | --- | --- |
| Redis positive | `examples/input/redis_likely_exploitable_features.json` | `ready_for_safe_verification` |
| Redis weak | `examples/input/redis_weak_features.json` | `needs_more_evidence` |
| Grafana blocked | `examples/input/grafana_blocked_features.json` | `needs_more_evidence` |
| Unknown WordPress | `examples/input/unknown_wordpress_features.json` | `unknown_family_triage` |
| Negative control | `examples/input/negative_control_features.json` | `do_not_exploit_now` หรือ `needs_more_evidence` |

## Command

```powershell
$py='C:\Users\rapii\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py scripts\predict_prototype.py `
  --features examples\input\redis_likely_exploitable_features.json `
  --model-dir runtime\models\prototype `
  --top-k 5
```

## Batch Ingestion Contract

ถ้าเป็นข้อมูลจากเครื่องสแกนทั้ง batch ให้ใช้:

```text
scripts/import_scan_batch.py
```

input folder ควรมี:

```text
features.jsonl
targets.jsonl
validation-results.jsonl
cve-enrichment.jsonl
safe-to-merge-targets.txt
quarantined-targets.txt
```

แล้วสคริปต์จะสร้าง:

```text
features.enriched.jsonl
runtime-targets.jsonl
import-audit.json
IMPORT-AUDIT-TH.md
```

หลังจากนั้นค่อย run:

```text
scripts/evaluate_runtime_predictions.py
scripts/run_runtime_regression.py
```

## Train/Promote Checklist

ก่อนเอาข้อมูลเข้า train หรือ promote model ต้องผ่าน checklist นี้:

- batch import สำเร็จ
- `import-audit.json` ไม่มี issue ระดับ error
- runtime evaluation ของ batch ใหม่ไม่เจอ safety failure
- regression baseline ผ่าน 3/3 suites
- ไม่มี postcheck field หลุดเข้า precheck feature
- unknown-family ไม่ถูกฝืนเป็น known-family ready
- weak/noisy ไม่ถูกปล่อยเป็น `ready_for_safe_verification`

## ห้าม

- ห้ามให้ LLM ยิง exploit อัตโนมัติจาก score เดี่ยว ๆ
- ห้ามเอา CISA KEV / EPSS / NVD มาแทน scanner evidence
- ห้ามเอา validation set เข้า train ทันที
- ห้ามใช้ `rce_confirmed`, `msf_check_confirmed`, `tool_metasploit_success` เป็น precheck feature

## Local Files Added For This Contract

```text
docs/11-ml-runtime-integration-contract-th.md
runtime/llm-action-policy.json
examples/input/redis_weak_features.json
examples/input/grafana_blocked_features.json
examples/input/negative_control_features.json
examples/output/redis_weak_prediction.json
examples/output/grafana_blocked_prediction.json
examples/output/negative_control_prediction.json
```
