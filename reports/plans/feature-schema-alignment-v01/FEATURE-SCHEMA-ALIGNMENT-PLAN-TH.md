# Feature Schema Alignment Plan v01

## เป้าหมาย

ทำให้ output จาก OpenCode/feature extractor ตรงกับ schema ที่ runtime ML ใช้จริง เพื่อไม่ให้โมเดลพลาดเพราะชื่อ feature ไม่ตรงหรือ evidence สำคัญหายไป

รอบ Unseen v02 แสดงให้เห็นว่า Gate เริ่มดี แต่ Ranker พลาดเพราะ feature ที่ส่งเข้า runtime ยังไม่ครบ family-specific signal

## กติกาหลัก

1. ทุก target ต้องมี canonical feature names ตาม runtime
2. alias เก่าใช้ได้ชั่วคราว แต่ต้อง normalize ก่อน predict
3. known-family target ต้องมี feature เฉพาะ family ไม่ใช่มีแค่ generic HTTP signal
4. unknown-family target ต้องมี `unknown_product_detected=1`
5. ถ้า evidence ไม่พอ ให้ตอบ `unknown_family` หรือ `low_confidence` ไม่ใช่เดา family

## Canonical Features ที่ต้องใช้

### Common

```text
target_id
is_http_target
is_non_http_service
open_port_count
http_port_count
service_count
endpoint_reachable_count
endpoint_missing_count
version_in_vulnerable_range
version_in_vulnerable_range_true
version_in_vulnerable_range_false
version_patched
version_not_affected
auth_required
no_auth_required
anonymous_access
```

ห้ามใช้เป็นชื่อหลัก:

```text
is_non_http_target
```

ให้เปลี่ยนเป็น:

```text
is_non_http_service
```

### Redis

```text
redis_detected
redis_info_accessible
lua_available
no_auth_required
auth_required
version_in_vulnerable_range
version_patched
```

### Grafana

```text
grafana_detected
plugin_path_candidate_found
public_plugin_path_accessible
path_traversal_candidate_found
path_traversal_blocked
version_in_vulnerable_range
version_patched
auth_required
```

### Solr Velocity

```text
solr_detected
solr_core_found
velocity_enabled
velocity_disabled
config_api_accessible
config_api_blocked
version_in_vulnerable_range
version_patched
```

### Tomcat PUT

```text
method_put_allowed
method_put_rejected
jsp_upload_candidate
upload_blocked
wrong_context_path
version_in_vulnerable_range
version_patched
```

### Tomcat AJP

```text
ajp_port_open
ajp_port_closed
ajp_not_exposed
version_in_vulnerable_range
version_patched
```

### CouchDB Auth/Admin Party

```text
couchdb_detected
admin_party_enabled
auth_required
no_auth_required
config_accessible
config_blocked
users_db_accessible
version_in_vulnerable_range
version_patched
```

### Shiro Key

```text
rememberme_deleteMe_seen
default_key_likely
default_key_unlikely
version_patched
```

### Unknown Family

```text
unknown_product_detected
unknown_family_signal_count
known_family_signal_count
drupal_detected
laravel_detected
jetty_detected
php_cgi_detected
jboss_detected
wordpress_detected
```

## วิธีทำงานรอบถัดไป

1. ใช้ output จาก `dec-unseen-validation-v02-2026-09-01`
2. ตรวจ target ที่ Ranker พลาดก่อน:
   - `unseen_redis_variant_01`
   - `unseen_grafana_variant_01`
3. เติม feature เฉพาะ family ให้ครบ
4. รัน `scripts/predict_prototype.py` ด้วย runtime ล่าสุด
5. ถ้าผลดีขึ้น ค่อย merge เข้า training dataset
6. ถ้าผลยังพลาด ให้เก็บ raw evidence เพิ่มเฉพาะ family นั้น

## เกณฑ์ผ่าน

```text
Unknown-family final_decision ต้องเป็น unknown_family_triage
Negative controls ต้องเป็น do_not_exploit_now
Known-positive variants ต้องเป็น ready_for_safe_verification หรือ manual_triage_before_exploit
Ranker known-positive Top-1 ต้องดีขึ้นจาก 33.3%
```

## ข้อควรจำ

อย่า retrain ทันทีถ้า feature schema ยังไม่ตรง เพราะโมเดลจะเรียนรู้ noise และทำให้ผลดูดีใน test เดิม แต่พังเมื่อลอง target ใหม่
