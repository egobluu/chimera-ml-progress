# Runtime Prototype สำหรับส่งต่อฝั่ง LLM/Agentic

## อ่านไฟล์นี้ก่อน

โฟลเดอร์นี้คือชุดที่ควรใช้จริงระดับ prototype ไม่ใช่กองรายงานทดลองทั้งหมด

```text
runtime/
├── README-TH.md
└── models/prototype/
    ├── gate_precondition_only.json
    ├── family_ranker.json
    └── prototype_manifest.json
```

สรุปสั้น:

```text
ตัวใช้จริง = runtime/models/prototype + scripts/predict_prototype.py
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

## ข้อจำกัด

- ยังเป็น prototype ไม่ใช่ production
- ยังต้องให้ Metasploit/manual PoC ยืนยันหลัง ML แนะนำ
- Ranker ตอบได้เฉพาะ family ที่มีใน `prototype_manifest.json`
- ถ้า evidence ไม่พอควรตอบ `unknown_family` หรือ `low_confidence`
