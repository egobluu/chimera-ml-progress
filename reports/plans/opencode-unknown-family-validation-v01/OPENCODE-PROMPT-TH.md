# Prompt สำหรับ OpenCode/Kali: Unknown-family + Ranker Guard Validation v01

งาน: ทดสอบ ML runtime หลังเพิ่ม Ranker confidence/readiness guard

## เป้าหมาย

เก็บ validation set ใหม่ที่ยังไม่เคยเข้า training เพื่อพิสูจน์ว่า:

1. ถ้า target อยู่ใน known family และ feature เฉพาะครบ ระบบควรเลือก family ถูก
2. ถ้า target มี feature บางหรือ generic เกินไป ระบบไม่ควรมั่นใจเกินจริง
3. ถ้า target เป็น unknown family ระบบควรส่งไป unknown-family triage ไม่เดาเป็น Redis/Tomcat/Grafana แบบมั่ว
4. negative target ที่มี service จริงแต่ติด blocker ต้องไม่ถูกปล่อยไป verification อัตโนมัติ

## Output Path

เขียนผลไปที่:

```text
/media/sf_kali-share/dataset/dec-ranker-guard-unknown-validation-2026-09-02
```

## Required Top-level Files

ต้องมีไฟล์ชั้นบน:

```text
features.jsonl
targets.jsonl
validation-results.jsonl
safe-to-merge-targets.txt
quarantined-targets.txt
RANKER-GUARD-UNKNOWN-VALIDATION-TH.md
```

raw evidence ใส่ใน folder ราย target ได้ แต่ไม่ต้องอัปเข้า GitHub

## Target Plan

Known-family positive/negative เพิ่ม:

- Redis positive 1, negative 1
- Grafana positive 1, negative 1
- Solr Velocity positive 1, negative 1
- Tomcat PUT positive 1, negative 1
- Tomcat AJP positive 1, negative 1
- CouchDB positive 1, negative 1

Unknown-family targets อย่างน้อย 6 ตัว:

- Drupal
- Laravel
- Jetty
- WordPress
- PHP-CGI
- JBoss

Noisy/weak-feature cases อย่างน้อย 6 ตัว:

- มี version ดูน่าสนใจ แต่ endpoint หาย
- service เปิดจริง แต่ auth block
- มี no_auth_required แต่ไม่มี family-specific proof
- port เปิด แต่ product fingerprint ไม่ชัด
- มี generic HTTP signal แต่ไม่มี exploit precondition
- มี candidate path แต่ถูก block

## Feature Rules

ใช้ precheck feature เท่านั้น

ห้ามใช้เป็น feature:

```text
tool_metasploit_success
msf_check_confirmed
msf_check_not_vulnerable
rce_confirmed
manual_poc_failed
shell_obtained
flag_found
```

พวกนี้ใช้ได้เฉพาะเป็น validation label หลังตรวจแล้ว ไม่ใช่ input ของ ML

## Required Feature Style

ทุก target ต้องเป็น flat JSON object

ค่าควรเป็น:

```text
1 = พบ/จริง/ใช่
0 = ไม่พบ/ไม่จริง/ไม่ใช่
```

ควรอิง schema จาก branch scanner:

```text
ml-runtime/feature-schema/runtime_feature_schema.json
ml-runtime/sample-features/full_feature_template.json
```

## Probe-completed Fields ที่อยากให้เพิ่ม

เพิ่ม field เหล่านี้ด้วยถ้าทำได้:

```text
redis_probe_completed
grafana_probe_completed
solr_probe_completed
tomcat_put_probe_completed
tomcat_ajp_probe_completed
couchdb_probe_completed
unknown_family_probe_completed
```

เหตุผล: เพื่อแยกว่า feature เป็น 0 เพราะ probe แล้วไม่พบ หรือเป็น 0 เพราะยังไม่ได้ probe

## Target JSONL Format

`targets.jsonl`:

```json
{"target_id":"redis_positive_guard_01","category":"positive","expected_family":"redis","expected_status":"validated_positive"}
{"target_id":"drupal_unknown_guard_01","category":"unknown_family","expected_family":"unknown","expected_status":"validated_positive"}
{"target_id":"tomcat_put_negative_guard_01","category":"negative","expected_family":"none","expected_status":"validated_negative"}
```

## Expected Validation

สำหรับ known positive:

```text
expected ML behavior:
Gate = likely_exploitable
Ranker top family = expected family
Final = ready_for_safe_verification หรือ manual_triage_before_exploit ถ้า feature ยังบาง
```

สำหรับ negative:

```text
expected ML behavior:
Final ต้องไม่ใช่ ready_for_safe_verification
```

สำหรับ unknown-family:

```text
expected ML behavior:
Final = unknown_family_triage
```

## Summary ที่ต้องเขียน

ใน `RANKER-GUARD-UNKNOWN-VALIDATION-TH.md` ขอให้สรุป:

- target ทั้งหมดกี่ตัว
- safe_to_merge กี่ตัว
- quarantine กี่ตัว
- family ไหนผ่าน/พลาด
- unknown-family ได้ unknown signal ครบไหม
- weak/noisy cases มี feature อะไรบ้าง
- มี target ไหนที่ label กับ evidence ขัดกันไหม

