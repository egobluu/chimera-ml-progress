# Feature Catalog ทั้งหมดของ ML Gate v0.2

ไฟล์นี้สรุป feature ที่อยู่ใน `target-exploitability-dataset.csv` ของ `dec-ml-only-gate-v02-2026-08-31` จำนวน 44 features โดยแยกว่า feature ไหนใช้ได้ก่อนยิง exploit, feature ไหนใช้ได้แบบมีเงื่อนไข, และ feature ไหนเสี่ยงเป็น data leak

## วิธีอ่าน phase

| phase | ความหมาย | ใช้ train/inference ก่อนยิงได้ไหม |
| --- | --- | --- |
| `safe_basic_precheck` | ข้อมูลพื้นฐานจาก scanner/recon ที่รู้ได้ก่อน exploit | ใช้ได้ |
| `conditional_precheck` | ใช้ได้ถ้า probe รันก่อน model ตัดสินใจ และเก็บเหมือนกันทุก target | ใช้ได้แบบมีเงื่อนไข |
| `postcheck_or_leak_risk` | ข้อมูลหลัง Metasploit/manual PoC หรือข้อมูลที่ใกล้ label เกินไป | ห้ามใช้เป็น precheck |

## สรุปผล audit

| รายการ | จำนวน |
| --- | ---: |
| validated_positive | 20 |
| validated_negative | 20 |
| features ทั้งหมด | 44 |
| `safe_basic_precheck` | 7 |
| `conditional_precheck` | 31 |
| `postcheck_or_leak_risk` | 6 |

## Feature ทั้งหมด

| feature | phase | ใช้ทำอะไร | ข้อควรระวัง |
| --- | --- | --- | --- |
| `service_port` | `safe_basic_precheck` | port หลักของ service | อาจเป็น shortcut ของ lab ถ้า port fix เกินไป |
| `is_http_target` | `safe_basic_precheck` | บอกว่า target เป็น HTTP/Web หรือไม่ | ใช้เป็น context ไม่ควรเป็นตัวตัดสินหลัก |
| `is_non_http_service` | `safe_basic_precheck` | บอกว่าเป็น service non-HTTP เช่น Redis | ใช้แยก tool ที่เหมาะกับ target |
| `raw_file_count` | `safe_basic_precheck` | จำนวนไฟล์ evidence/raw ที่มี | ใน v0.2 ยังไม่ค่อยมีประโยชน์ เพราะค่าเป็น 0 |
| `tool_httpx_success` | `safe_basic_precheck` | httpx probe สำเร็จหรือไม่ | ถ้าไม่ได้รันต้องแยก `missing` ไม่ใช่ใส่ 0 เฉย ๆ |
| `tool_nuclei_success` | `safe_basic_precheck` | nuclei scan สำเร็จหรือไม่ | บอกคุณภาพ evidence ไม่ใช่ label โดยตรง |
| `metasploit_module_found` | `safe_basic_precheck` | มี Metasploit module ที่เกี่ยวข้องหรือไม่ | ใช้ได้ถ้าเป็นแค่ search module แต่ไม่ใช่ผล check/run |
| `version_in_vulnerable_range_true` | `conditional_precheck` | version อยู่ในช่วงที่ CVE กระทบ | ต้องมาจาก version detection ก่อนยิง |
| `version_in_vulnerable_range_false` | `conditional_precheck` | version ไม่อยู่ในช่วงที่ CVE กระทบ | ใน v0.2 ยังไม่ถูกใช้จริง |
| `version_not_affected` | `conditional_precheck` | version/product ไม่ได้รับผลกระทบ | เป็น negative signal ที่ดี ถ้าตรวจจาก source/probe ซ้ำได้ |
| `version_patched` | `conditional_precheck` | version ถูก patch แล้ว | ดีสำหรับลด false positive |
| `precondition_pass_count` | `conditional_precheck` | จำนวนเงื่อนไข exploit ที่ผ่าน เช่น endpoint/auth/port | ใน v0.2 พบเฉพาะ positive จึงแรงมาก ต้องเก็บให้สมดุล |
| `precondition_fail_count` | `conditional_precheck` | จำนวนเงื่อนไข exploit ที่ไม่ผ่าน | ใน v0.2 ยังเป็น 0 ควรเก็บเพิ่ม |
| `auth_required` | `conditional_precheck` | target ต้อง auth ก่อนเข้าจุด exploit | negative signal สำหรับ exploit ที่ต้อง anonymous |
| `no_auth_required` | `conditional_precheck` | target เปิดให้เข้าถึงโดยไม่ต้อง auth | positive signal แต่ต้องระวัง false positive |
| `endpoint_reachable_count` | `conditional_precheck` | จำนวน endpoint สำคัญที่เข้าถึงได้ | ต้อง backfill ด้วย katana/ffuf/curl |
| `endpoint_missing_count` | `conditional_precheck` | จำนวน endpoint สำคัญที่ไม่พบ | ช่วยลด false positive ถ้าเก็บจริงทุก target |
| `method_put_allowed` | `conditional_precheck` | HTTP PUT เปิดใช้งาน | สำคัญกับ Tomcat PUT upload |
| `method_put_rejected` | `conditional_precheck` | HTTP PUT ถูกปฏิเสธ | negative signal สำหรับ Tomcat PUT upload |
| `ajp_port_open` | `conditional_precheck` | AJP port 8009 เปิด | สำคัญกับ Tomcat Ghostcat |
| `ajp_port_closed` | `conditional_precheck` | AJP port ปิด | negative signal สำหรับ Ghostcat |
| `anonymous_access` | `conditional_precheck` | เข้าถึง endpoint สำคัญได้โดยไม่ต้อง login | ใช้กับ CouchDB/Nexus/Solr บางเคส |
| `velocity_enabled` | `conditional_precheck` | Solr Velocity เปิดใช้งาน | positive signal สำหรับ Solr Velocity RCE |
| `invokefunction_reachable` | `conditional_precheck` | ThinkPHP invokefunction endpoint ใช้ได้ | positive signal สำหรับ ThinkPHP RCE |
| `invokefunction_not_found` | `conditional_precheck` | ไม่พบ endpoint ThinkPHP invokefunction | negative signal สำหรับ ThinkPHP RCE |
| `admin_party_enabled` | `conditional_precheck` | CouchDB admin party เปิด | positive signal สำหรับ CouchDB auth bypass/admin creation |
| `spring_detected` | `conditional_precheck` | ตรวจพบ Spring-specific fingerprint | ใน v0.2 ยังไม่เด่น ต้องเก็บ Spring fingerprint เพิ่ม |
| `spring_not_detected` | `conditional_precheck` | ไม่พบ Spring fingerprint | negative signal สำหรับ Spring-only exploit |
| `wrong_software_type` | `conditional_precheck` | software ที่พบไม่ตรงกับ exploit family | สำคัญมากสำหรับลดการยิง exploit ผิด product |
| `nuclei_cve_confirmed` | `conditional_precheck` | nuclei พบ CVE match | ใช้ได้ถ้าเป็นผล scanner ก่อน exploit แต่ไม่ควรเชื่อเดี่ยว ๆ |
| `nuclei_fingerprint_only` | `conditional_precheck` | nuclei เห็นแค่ fingerprint/product | บอกว่า evidence ยังไม่พอ |
| `nuclei_no_vuln_found` | `conditional_precheck` | nuclei ไม่พบ vuln | negative signal แบบอ่อน ไม่ใช่หลักฐานว่าไม่ vuln เสมอ |
| `painless_sandbox_blocks` | `conditional_precheck` | Elasticsearch Painless sandbox/blocking behavior | ใช้แยก Elasticsearch exploitability |
| `path_traversal_blocked` | `conditional_precheck` | path traversal ถูก block | negative signal สำหรับ traversal CVE |
| `auth_blocks_exploit` | `conditional_precheck` | auth ปิดทาง exploit | ใน v0.2 ยังไม่ถูกเติมมากพอ |
| `endpoint_not_found` | `conditional_precheck` | endpoint exploit ไม่พบ | ควรเก็บให้ชัดจาก curl/katana/ffuf |
| `wrong_version` | `conditional_precheck` | version ไม่ตรงกับ exploit | คล้าย `version_not_affected` แต่ควร normalize ให้ชัด |
| `no_msf_module` | `conditional_precheck` | ไม่มี Metasploit module | ใช้เป็น context ได้ แต่ไม่ควรแปลว่า exploit ไม่ได้เสมอ |
| `tool_metasploit_success` | `postcheck_or_leak_risk` | Metasploit ทำงานสำเร็จ | ห้ามใช้ก่อนตัดสินใจ เพราะเป็นข้อมูลหลังยิง |
| `negative_evidence_count` | `postcheck_or_leak_risk` | จำนวน evidence เชิงลบแบบรวมก้อน | เสี่ยงที่สุดใน v0.2 เพราะแยก negative 20/20 ได้พอดี |
| `rce_confirmed` | `postcheck_or_leak_risk` | ยืนยัน RCE แล้ว | เป็น label/feedback ไม่ใช่ input precheck |
| `msf_check_confirmed` | `postcheck_or_leak_risk` | Metasploit check บอก vulnerable | เป็น postcheck validation ห้ามใช้เป็น precheck |
| `msf_check_not_vulnerable` | `postcheck_or_leak_risk` | Metasploit check บอก not vulnerable | ใช้เป็น label/feedback ได้ แต่ห้ามใช้ก่อนยิง |
| `manual_poc_failed` | `postcheck_or_leak_risk` | manual PoC ล้มเหลว | เป็นผลหลังตรวจ ไม่ใช่ feature ก่อนตัดสินใจ |

## Feature ที่ควรใช้ในโมเดลจริงตอนนี้

สำหรับ `strict_precheck` ควรใช้เฉพาะ feature ก่อน exploit หรือ feature ที่ probe ได้ก่อนตัดสินใจ เช่น:

- basic service: `service_port`, `is_http_target`, `is_non_http_service`
- version: `version_in_vulnerable_range_true`, `version_not_affected`, `version_patched`, `wrong_version`
- precondition: `auth_required`, `no_auth_required`, `endpoint_reachable_count`, `endpoint_missing_count`, `method_put_allowed`, `method_put_rejected`, `ajp_port_open`, `ajp_port_closed`
- product/behavior: `wrong_software_type`, `spring_detected`, `spring_not_detected`, `anonymous_access`, `velocity_enabled`, `admin_party_enabled`
- scanner: `nuclei_cve_confirmed`, `nuclei_fingerprint_only`, `nuclei_no_vuln_found`

## Feature ที่ควรแยกออกจาก precheck

กลุ่มนี้ยังเก็บไว้ใน dataset ได้ แต่ใช้เป็น postcheck/feedback เท่านั้น:

- `tool_metasploit_success`
- `negative_evidence_count`
- `rce_confirmed`
- `msf_check_confirmed`
- `msf_check_not_vulnerable`
- `manual_poc_failed`

## Feature ใหม่ที่ควรเพิ่มหลัง backfill

เมื่อ OpenCode รัน `whatweb`, `katana`, `ffuf` หรือ `feroxbuster` ให้เพิ่ม feature ใหม่เหล่านี้:

| feature ใหม่ | มาจากเครื่องมือ | ใช้ทำอะไร |
| --- | --- | --- |
| `whatweb_was_run` | whatweb | บอกว่าเครื่องมือนี้ถูกรันจริง |
| `whatweb_missing` | whatweb | บอกว่าไม่มีผลเพราะไม่ได้รัน/รันไม่ได้ |
| `whatweb_tech_detected` | whatweb | ตรวจพบ technology |
| `whatweb_version_detected` | whatweb | ตรวจพบ version |
| `katana_was_run` | katana | บอกว่า crawler ถูกรันจริง |
| `katana_missing` | katana | บอกว่า crawler ไม่ได้รัน/รันไม่ได้ |
| `katana_endpoint_count` | katana | จำนวน endpoint ที่ crawl เจอ |
| `content_discovery_was_run` | ffuf/feroxbuster | บอกว่า content discovery ถูกรันจริง |
| `content_discovery_missing` | ffuf/feroxbuster | บอกว่า content discovery ไม่ได้รัน/รันไม่ได้ |
| `discovered_path_count` | ffuf/feroxbuster | จำนวน path ที่ค้นพบ |
| `admin_path_found` | katana/ffuf/curl | เจอ path กลุ่ม admin |
| `api_path_found` | katana/ffuf/curl | เจอ path API |
| `actuator_path_found` | katana/ffuf/curl | เจอ Spring actuator |
| `manager_path_found` | katana/ffuf/curl | เจอ Tomcat manager |
| `login_path_found` | katana/ffuf/curl | เจอ login page |
| `upload_path_found` | katana/ffuf/curl | เจอ upload endpoint |
| `config_path_found` | katana/ffuf/curl | เจอ config endpoint |
| `rpc_path_found` | katana/ffuf/curl | เจอ RPC endpoint |

## กฎสำคัญสำหรับข้อมูลเก่า

- ถ้า target เก่าไม่ได้รัน tool ใหม่ ห้ามใส่ค่าเหมือนว่า tool รันแล้วไม่เจอ
- ต้องมี `*_was_run` และ `*_missing`
- `tool_not_run` ไม่เท่ากับ `tool_run_no_finding`
- ข้อมูลเก่าใช้ต่อได้ แต่ต้อง mark missing ให้ถูก

## ข้อสรุป

feature catalog นี้ทำให้เราเห็นว่า v0.2 มี feature พร้อมใช้ระดับหนึ่งแล้ว แต่จุดที่ต้องแก้คือการแยก `precheck` กับ `postcheck` ให้เด็ดขาด และเพิ่ม evidence จากเครื่องมือใหม่เพื่อให้ `strict_precheck` ลด false positive ได้จริง
