# Runtime Prototype สำหรับส่งต่อฝั่ง LLM/Agentic

## อ่านไฟล์นี้ก่อน

โฟลเดอร์นี้คือชุดที่ควรใช้จริงระดับ prototype ไม่ใช่กองรายงานทดลองทั้งหมด

```text
runtime/
├── README-TH.md
├── resolver/
│   └── cve-ranking-rules.json
└── models/prototype/
    ├── gate_precondition_only.json
    ├── family_ranker.json
    └── prototype_manifest.json
```

รุ่นปัจจุบัน train จาก dataset 67 targets หลังเพิ่ม Redis/Grafana schema backfill แล้ว รายละเอียดอยู่ที่:

```text
reports/evaluations/ranker-schema-backfill-redis-grafana-v01/RUNTIME-RETRAIN-RESULTS-TH.md
```

สรุปสั้น:

```text
ตัวใช้จริง = runtime/models/prototype + runtime/resolver/cve-ranking-rules.json + scripts/predict_prototype.py
ตัว train/test = scripts/train_*.py + reports/evaluations/*
ตัวอธิบาย/หลักฐาน = docs/* + reports/*
```

## ฝั่ง LLM ต้องเรียกอะไร

ให้เรียก:

```bash
python scripts/predict_prototype.py --features examples/input/redis_likely_exploitable_features.json
```

input คือ JSON feature ที่ feature extractor สร้างจากผล scan

output เป็น JSON เช่น:

```json
{
  "target_id": "example_redis_likely_exploitable",
  "gate": {
    "model": "gate_precondition_only",
    "score": 0.91,
    "threshold": 0.15,
    "decision": "likely_exploitable"
  },
  "ranker": {
    "model": "family_ranker",
    "decision": "known_family_ready",
    "top_families": [
      {
        "family": "redis",
        "score": 1.23,
        "positive_signals": 4,
        "negative_signals": 0
      }
    ]
  },
  "resolver": {
    "model": "rule_cve_ranker_v01",
    "family": "redis",
    "candidate_count": 1,
    "top_cves": [
      {
        "cve": "CVE-2022-0543",
        "score": 0.87,
        "recommendation": "safe_check_candidate",
        "modules": ["exploit/linux/redis/redis_debian_sandbox_escape"]
      }
    ]
  },
  "final_decision": "ready_for_safe_verification",
  "recommended_next_action": "run_safe_metasploit_check_or_manual_probe"
}
```

## ลำดับการทำงานจริง

```text
target
-> scanner
-> feature extractor
-> scripts/predict_prototype.py
-> LLM/agentic อธิบายผลและเลือก action ถัดไป
-> Metasploit check/manual PoC หลัง user ยืนยัน
-> feedback กลับ dataset
```

## แต่ละส่วนทำหน้าที่อะไร

### 1. Gate

ไฟล์:

```text
runtime/models/prototype/gate_precondition_only.json
```

หน้าที่:

```text
ตอบว่า target น่าลอง exploit ต่อไหม
```

output:

```text
likely_exploitable
no_exploit
low_confidence
```

Gate ใช้ feature ก่อนยิง exploit เท่านั้น เช่น:

```text
version_in_vulnerable_range
auth_required
no_auth_required
endpoint_reachable_count
method_put_allowed
ajp_port_open
lua_available
velocity_enabled
config_accessible
```

### 2. Family Ranker

ไฟล์:

```text
runtime/models/prototype/family_ranker.json
```

หน้าที่:

```text
ถ้า Gate บอกว่าน่าลอง exploit ให้จัดอันดับ exploit family ที่ควรลองก่อน
```

ตัวอย่าง family:

```text
redis
grafana
solr_velocity
tomcat_put
tomcat_ajp
couchdb_auth
thinkphp_rce
```

### 3. Unknown Guard

อยู่ใน:

```text
scripts/predict_prototype.py
```

หน้าที่:

```text
กัน Ranker มั่วตอบ family ที่รู้จัก ทั้งที่ evidence ไม่พอหรือ target อยู่นอกขอบเขต
```

output:

```text
known_family_ready
known_family_but_blocked_or_low_confidence
unknown_family
```

### 4. CVE/Module Resolver

ไฟล์:

```text
runtime/resolver/cve-ranking-rules.json
scripts/rank_cve_candidates.py
```

หน้าที่:

```text
หลัง Ranker เลือก family แล้ว resolver จะจัดอันดับ CVE/module/manual-check candidate ภายใน family นั้น
```

ตัวอย่าง:

```text
Family Ranker: solr_velocity
CVE Resolver:
1. CVE-2019-17558
2. CVE-2017-12629
```

Resolver ไม่ใช่ ML model หลัก แต่เป็น rule-scoring layer ที่อ่าน:

```text
family ที่ Ranker ทาย
feature ที่ scanner ส่งมา
CVE enrichment เช่น in_cisa_kev, epss_score, cvss_base_score
mapping table ใน runtime/resolver/cve-ranking-rules.json
```

เหตุผลที่ทำแบบนี้:

```text
ไม่ให้ ML ทาย CVE ตรง ๆ ตั้งแต่แรก เพราะ CVE เยอะกว่า target มาก และเสี่ยง overfit กับชื่อ/alias
ให้ ML ทาย exploitability + family ก่อน แล้วค่อย map family -> CVE/module ด้วย resolver ที่ audit ได้
```

## แล้วต้องส่งอะไรให้ฝั่ง LLM

ควรส่ง:

```text
runtime/models/prototype/
scripts/predict_prototype.py
scripts/train_runtime_models.py
docs/04-feature-schema-th.md
docs/07-feature-catalog-th.md
docs/08-workflow-responsibilities-th.md
examples/input/
examples/output/
reports/progress/current-status-th.md
```

ไม่ต้องส่ง:

```text
prompts/
raw scan ทั้งก้อน
cache/runtime dependency
reports/evaluations เก่าทุกอัน ถ้าอีกฝ่ายไม่ได้จะตรวจ metric ย้อนหลัง
```

## เราส่งแค่ feature กับโค้ด train/test พอไหม

ไม่พอ ถ้าจะให้ฝั่ง LLM ใช้งานง่าย ต้องมี 4 อย่าง:

1. feature schema - บอกว่าต้องส่ง field อะไร
2. runtime model - model ที่ใช้ predict จริง
3. inference script - entrypoint ที่เรียกแล้วได้ JSON
4. sample input/output - ตัวอย่างให้ต่อระบบไม่เพี้ยน

ส่วน train/test code เอาไว้ให้ทีม ML retrain หรือ verify รอบหลัง ไม่ใช่สิ่งที่ LLM ต้องเรียกทุกครั้ง

## Integration contract

ถ้าจะต่อ scanner/LLM จริง ให้อ่าน contract นี้:

```text
docs/11-ml-runtime-integration-contract-th.md
docs/12-llm-decision-explainer-th.md
runtime/llm-action-policy.json
```

ภาษาคน:

```text
contract บอกว่า scanner ต้องส่ง field อะไร runtime จะคืนอะไร และ LLM ควรทำอะไรกับ final_decision แต่ละแบบ
decision explainer แปลง JSON prediction เป็น report ที่คนอ่านเข้าใจได้
```

## ข้อจำกัด

- ยังเป็น prototype ไม่ใช่ production
- ยังต้องให้ Metasploit/manual PoC ยืนยันหลัง ML แนะนำ
- Ranker ตอบได้เฉพาะ family ที่มีใน `prototype_manifest.json`
- ถ้า evidence ไม่พอควรตอบ `unknown_family` หรือ `low_confidence`
- หลัง unseen validation v01 พบว่า Gate ยัง false positive กับ unknown family ได้ จึงต้องดู `final_decision` ร่วมกับ Ranker/Unknown Guard เสมอ
- หลัง unseen validation v02 เพิ่ม guard แล้ว ถ้า input มี `unknown_product_detected=1` และ signal ของ unknown มากกว่าหรือเท่ากับ known family ระบบจะบังคับ `final_decision=unknown_family_triage`

## Feature schema ที่ต้องระวัง

feature extractor ควรส่งชื่อหลักให้ตรง runtime:

```text
is_non_http_service
```

ถ้ายังส่งชื่อเก่า:

```text
is_non_http_target
```

runtime จะ normalize ให้ชั่วคราว แต่ควรแก้ฝั่ง scanner/feature extractor ให้ตรง schema เพื่อไม่ให้ train รอบต่อไปเพี้ยน

ถ้าเจอ product ที่ยังไม่มีใน ranker เช่น Drupal, Laravel, Jetty, PHP-CGI หรือ JBoss ให้ส่ง:

```text
unknown_product_detected=1
unknown_family_signal_count>=1
known_family_signal_count=0
```

เพื่อให้ระบบตอบ `unknown_family_triage` แทนการเดา family ที่รู้จักอยู่แล้ว

## Runtime guard หลัง Unseen v03

runtime เพิ่ม guard เพื่อกัน failure ที่เจอใน v03:

- derive `unknown_product_detected=1` จาก fingerprint ของ product นอก family เช่น Drupal/PHP-CGI
- normalize alias สำคัญ เช่น `admin_party -> admin_party_enabled`
- downgrade เป็น `low_confidence` เมื่อมี blocking negative evidence แต่ไม่มี strong positive precondition
- rerank โดยให้ family-specific signal สำคัญกว่า generic signal

ผลคือ runtime จะ conservative ขึ้น: ถ้าหลักฐานไม่ชัด จะไม่รีบส่งไป `ready_for_safe_verification`
