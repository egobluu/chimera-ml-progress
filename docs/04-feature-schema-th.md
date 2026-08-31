# Feature Schema และเหตุผลที่ใช้

## หลักการเลือก feature

feature ต้องมาจากหลักฐานที่ scanner หรือ probe สร้างได้จริง ไม่ควรเป็นคำตอบที่เขียนย้อนกลับหลังรู้ label

feature ที่ดีควรตอบคำถาม:

- target เป็น software อะไร
- version อยู่ในช่วง vulnerable หรือไม่
- exploit precondition ผ่านไหม
- scanner เห็น CVE หรือเห็นแค่ fingerprint
- Metasploit มี module/check หรือไม่
- มี negative evidence ว่าไม่ควร exploit ไหม

## กลุ่ม feature หลัก

### 1. Basic service features

- `service_port`
- `is_http_target`
- `is_non_http_service`
- `raw_file_count`

ใช้เพื่อบอกลักษณะพื้นฐานของ target

### 2. Tool success features

- `tool_httpx_success`
- `tool_nuclei_success`
- `tool_metasploit_success`
- `tool_manual_poc_success`

ใช้เพื่อบอกว่าเครื่องมือไหนให้ evidence ได้บ้าง แต่ต้องระวังไม่ให้กลายเป็น shortcut เช่นแค่ Metasploit success แล้วทาย exploit

### 3. Version features

- `detected_product`
- `detected_version`
- `version_in_vulnerable_range`
- `version_not_affected`
- `version_patched`

สำคัญมาก เพราะ product เดียวกันอาจ vulnerable หรือไม่ vulnerable ตาม version

### 4. Precondition features

- `auth_required`
- `no_auth_required`
- `endpoint_reachable`
- `endpoint_missing`
- `method_put_allowed`
- `method_put_rejected`
- `ajp_port_open`
- `ajp_port_closed`
- `anonymous_access`
- `velocity_enabled`
- `invokefunction_reachable`
- `invokefunction_not_found`
- `admin_party_enabled`
- `spring_detected`
- `spring_not_detected`

กลุ่มนี้สำคัญที่สุดสำหรับการแยก positive/negative ใน product เดียวกัน

ตัวอย่าง:

- Tomcat version เหมือนอยู่ในช่วงเสี่ยง แต่ถ้า PUT ถูก reject ก็ exploit CVE-2017-12615 ไม่ได้
- Tomcat Ghostcat ต้องมี AJP port 8009
- Redis RCE ต้องมีเงื่อนไข auth/config/lua ที่เหมาะ

### 5. Scanner confirmation features

- `nuclei_cve_confirmed`
- `nuclei_fingerprint_only`
- `nuclei_no_vuln_found`
- `httpx_product_detected`

ใช้แยกว่า scanner เจอช่องโหว่จริงหรือแค่ระบุ product/version

### 6. Negative evidence features

- `negative_evidence_count`
- `wrong_software_type`
- `wrong_version`
- `precondition_failed`
- `auth_blocks_exploit`
- `endpoint_not_found`
- `scanner_only_fingerprint`
- `manual_poc_failed`

ช่วยลด false positive เพราะบอกเหตุผลว่าไม่ควร exploit

## Feature ที่ห้ามใช้ใน precheck

ห้ามใช้ feature ที่เป็น label leak:

- `validation_status`
- `target_id`
- folder path
- CVE string ตรง ๆ
- `expected_family`
- `metasploit_run_validated`
- exploit success หลังรู้คำตอบ

สำหรับ `metasploit_check_vulnerable` ต้องระวังมาก เพราะถ้าใช้ก่อนตัดสิน exploit จะกลายเป็น postcheck evidence ไม่ใช่ precheck

