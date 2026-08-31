# Targeted Precondition Probe Plan v0.2

เอกสารนี้เป็นเวอร์ชันที่เกลาใหม่จาก v0.1 ให้สั้นและใช้ทำงานจริงง่ายขึ้น จุดประสงค์คือเก็บ feature ที่ช่วยแก้ปัญหา `strict_precheck` false positive ไม่ใช่สแกนกว้าง ๆ เพิ่มอีก

## ปัญหาที่ต้องแก้

ตอนนี้ `strict_precheck` ยังทาย `exploit` ให้ negative ทุกตัว:

```text
FP = 20
FN = 0
```

แปลว่าโมเดลยังไม่มีหลักฐานก่อนยิง exploit ที่แข็งพอจะบอกว่า “ตัวนี้ไม่ควรยิง”

รอบ `whatweb + curl + ffuf` ช่วยให้ข้อมูลสะอาดขึ้น แต่ยังไม่พอ เพราะมันบอกแค่ว่าเว็บมีอะไร ไม่ได้ตอบว่าเงื่อนไขของ exploit ผ่านไหม

## หลักการรอบนี้

รอบนี้ไม่เก็บทุกอย่างแล้ว ให้เก็บเฉพาะ `targeted precondition` คือหลักฐานก่อนยิง exploit ที่ตอบคำถามชัด ๆ ว่า exploit family นั้นใช้ได้ไหม

ตัวอย่าง:

- Tomcat PUT exploit ต้องรู้ว่า `PUT` ได้หรือถูก reject
- Tomcat Ghostcat ต้องรู้ว่า AJP 8009 เปิดหรือปิด
- Redis exploit ต้องรู้ว่า auth block ไหม และ Lua/config ใช้ได้ไหม
- ThinkPHP RCE ต้องรู้ว่า `invokefunction` endpoint มีจริงไหม
- Solr RCE ต้องรู้ว่า Velocity เปิดจริงไหม

## ตัดอะไรออกจาก v0.1

| สิ่งที่ตัด | เหตุผล |
| --- | --- |
| probe แบบ `generic_*` | กว้างเกินไป ไม่ผูกกับ CVE/exploit จริง |
| default path discovery ทั่วไป | รอบ ffuf ทำไปแล้ว แต่ยังไม่ลด FP |
| version hint ที่ไม่แปลงเป็น affected/patched | เอาเข้า ML แล้วตีความยาก |
| target ที่ไม่มี lab ตรง | เสี่ยงทำ label ปน ถ้าเอา vulnerable lab มาแทน negative |
| probe ที่ไม่ให้ feature binary ชัด | ML ใช้ยากและอ่านผลยาก |

## Scope ที่ควรทำก่อน

ทำแค่ target ที่มีผลต่อ false positive และมี lab/หลักฐานที่ควบคุมได้ก่อน

| กลุ่ม | target | ทำไมต้องทำ |
| --- | --- | --- |
| Tomcat | `tomcat_non_vulnerable` | โมเดลต้องเรียนว่า PUT/AJP ไม่ผ่าน = ไม่ควรยิง |
| Redis | `redis_non_vulnerable`, `redis_auth_non_vulnerable` | โมเดลต้องเรียนว่า auth/version/Lua condition มีผล |
| ThinkPHP | `thinkphp_non_vulnerable` | โมเดลต้องเรียนว่าไม่มี endpoint = ไม่ควรยิง |
| CouchDB | `couchdb_non_vulnerable`, `couchdb_v3_non_vulnerable` | โมเดลต้องเรียนว่า auth/config/admin party block มีผล |
| Nginx | `nginx_121_non_vulnerable`, `nginx_non_vulnerable` | โมเดลต้องเรียนว่า version/range behavior ปลอดภัยมีผล |
| Spring | `spring_non_vulnerable` | โมเดลต้องเรียนว่าไม่ใช่ Spring fingerprint/actuator ไม่เปิด = ไม่พอ |
| Shiro | `shiro_non_vulnerable` | โมเดลต้องเรียนจาก rememberMe behavior |
| Solr | `solr_non_vulnerable` | โมเดลต้องเรียนว่า Velocity/core behavior ไม่ผ่าน |

ถ้า target ไหนไม่มี lab ตรง ให้ skip และเขียนเหตุผล อย่าเอา vulnerable lab มาแทน

## Probe ที่ต้องเก็บจริง

| target/family | probe | feature ที่ต้องออกมา |
| --- | --- | --- |
| Tomcat | เช็ค `OPTIONS` และลอง `PUT` ไฟล์ harmless ชั่วคราว | `method_put_allowed`, `method_put_rejected` |
| Tomcat | เช็ค TCP connect ไป AJP 8009 | `ajp_port_open`, `ajp_port_closed` |
| Tomcat | ตรวจ version จาก header/title/docs | `version_patched`, `version_in_vulnerable_range_true` |
| Redis | `PING`, `INFO server` แบบ timeout สั้น | `auth_required`, `no_auth_required`, `redis_version_detected` |
| Redis | safe Lua probe ที่ไม่เขียนข้อมูล | `lua_available`, `lua_blocked` |
| Redis | ตรวจ version ว่า affected หรือ patched | `version_patched`, `version_in_vulnerable_range_true` |
| ThinkPHP | curl endpoint `invokefunction` แบบ harmless | `invokefunction_reachable`, `invokefunction_not_found` |
| ThinkPHP | curl route แปลกเพื่อดู framework error | `thinkphp_detected`, `wrong_software_type` |
| CouchDB | curl `/` เพื่ออ่าน version | `couchdb_version_detected`, `version_patched` |
| CouchDB | curl `/_config`, `/_users`, `/_membership` | `admin_party_enabled`, `config_accessible`, `config_blocked`, `auth_required` |
| Nginx | curl header แล้ว parse version | `nginx_version_detected`, `version_patched` |
| Nginx | safe Range header probe | `range_behavior_vulnerable`, `range_behavior_safe` |
| Spring | curl `/actuator`, `/actuator/env`, error page | `spring_detected`, `spring_not_detected`, `actuator_path_found`, `actuator_path_missing` |
| Shiro | curl rememberMe probe แล้วดู cookie behavior | `rememberme_deleteMe_seen`, `rememberme_not_seen` |
| Solr | curl `/solr/admin/cores` | `solr_core_found`, `solr_core_missing`, `auth_required` |
| Solr | เช็ค Velocity config/API แบบ safe | `velocity_enabled`, `velocity_disabled` |

## Output ที่ต้องการ

ให้สร้าง output ใหม่:

```text
/home/kali/reports/dec-targeted-precondition-v02-2026-08-31/
```

และ sync ไป:

```text
/media/sf_kali-share/dataset/dec-targeted-precondition-v02-2026-08-31/
```

โครงสร้างต่อ target:

```text
raw-curated/{target_id}/
  targeted_precheck/
    probe.txt
  targeted-precheck-features.jsonl
  targeted-tool-applicability.jsonl
  TARGETED-NOTES-TH.md
```

ไฟล์รวม root:

```text
merged-targeted-precheck-features.jsonl
merged-targeted-tool-applicability.jsonl
TARGETED-PRECHECK-SUMMARY-TH.md
targeted-summary.json
```

## Schema ของ feature

หนึ่งบรรทัดต่อหนึ่ง feature:

```json
{
  "target_id": "tomcat_non_vulnerable",
  "phase": "targeted_precheck",
  "feature_name": "method_put_rejected",
  "feature_value": 1,
  "source_tool": "curl",
  "source_file": "raw-curated/tomcat_non_vulnerable/targeted_precheck/probe.txt",
  "missing": false,
  "reason": "PUT request returned 403/405, so Tomcat PUT upload precondition failed"
}
```

## กฎสำคัญ

- ห้ามใช้ Metasploit ในรอบนี้
- ห้ามใช้ manual exploit PoC เป็น precheck feature
- ห้ามสร้าง `negative_evidence_count`
- ห้ามแก้ label เดิม
- ถ้า probe ไม่ได้รัน ต้องมี `*_missing=1`
- ถ้า probe timeout ต้องมี `*_timeout=1`
- ถ้า target ไม่มี lab ตรง ให้ skip ไม่ใช่เอา lab CVE vulnerable มาแทน
- ทุก target ต้องปิด Docker หลังทำเสร็จ

## เป้าหมายที่วัดหลังรอบนี้

หลังได้ targeted features แล้ว ฝั่ง Codex จะ merge แล้ว train ใหม่:

```text
strict_precheck_with_targeted
scanner_only_with_targeted
```

เป้าหมายรอบแรกไม่ต้อง perfect ขอแค่:

```text
FP ลดจาก 20 ลงมาให้เห็น
FN ไม่เพิ่มเกิน 3-5
```

ถ้า FP ลดแต่ FN เพิ่มมาก แปลว่า feature เริ่มมีสัญญาณ แต่ต้องเก็บ positive precondition เพิ่มให้สมดุล
