# Safe Verification Plan v01

แผนนี้สร้างจากคิว `ready_for_safe_verification` บนเครื่อง 2 ฝั่ง Host Codex

กติกาหลัก:

```text
read-only/safe check เท่านั้น
ห้าม run exploit
ห้ามเอา shell
ห้ามเขียนไฟล์ลง target
ห้าม brute force
ต้องมี human approval ก่อน safe verification
```

## Top 5 Targets

| priority | target | family | CVE candidates | safe probe |
| ---: | --- | --- | --- | --- |
| 1 | `redis_positive_unseen_01` | `redis` | `CVE-2022-0543` | ยืนยัน Redis, INFO access, Lua availability และ distribution/version ก่อนตรวจต่อ |
| 2 | `grafana_positive_unseen_01` | `grafana` | `CVE-2021-43798` | ตรวจ public plugin path และ path traversal candidate แบบอ่านไฟล์ harmless เท่านั้น |
| 3 | `tomcat_put_positive_unseen_01` | `tomcat_put` | `CVE-2017-12615` | ตรวจว่า PUT allowed และ upload path candidate มีอยู่ก่อน หลีกเลี่ยงการเขียนไฟล์จริงถ้าไม่ได้อนุมัติ |
| 4 | `tomcat_ajp_positive_unseen_01` | `tomcat_ajp` | `CVE-2020-1938` | ตรวจว่า AJP port เปิดและ exposed จริง แล้วใช้ read-only probe เท่านั้น |
| 5 | `couchdb_positive_unseen_01` | `couchdb_auth` | `CVE-2017-12635` | ตรวจ admin party/config/users DB exposure แบบ read-only ก่อน |

## Prompt สำหรับ Kali VM OpenCode

```text
คุณอยู่ใน Kali VM บนเครื่อง 2 และรับงานจาก Host Codex ผ่าน shared folder

ทำเฉพาะ safe verification plan นี้เท่านั้น

Rules:
- ตรวจเฉพาะ target ที่อยู่ใน verification-plan.jsonl
- read-only/safe check เท่านั้น
- ห้าม run exploit
- ห้ามเอา shell
- ห้ามเขียนไฟล์ลง target
- ห้าม brute force
- ห้าม destructive fuzzing
- ถ้า tool ใดจะ execute payload หรือเปลี่ยน state ให้หยุดและรายงานก่อน

Output ที่ต้องเขียนกลับ:
verification-results.jsonl
verification-tool-log.jsonl
VERIFICATION-RESULT-TH.md

สำหรับแต่ละ target ให้รายงาน:
target_id
family
safe_probe_status
observed_evidence
blocked_by
recommended_feedback_features
should_feed_back_to_dataset
notes_th
```
