# Feature Gap Notes - Unseen Validation v02

## สรุปปัญหาที่พบ

### 1. Gate ทำงานถูกต้อง 100%
- TP: 8 (all known-positive variants and unknown-family targets correctly flagged)
- FP: 0 (all negative controls correctly rejected)
- TN: 4 (all negative controls)
- FN: 0 (no missed vulnerabilities)
- Accuracy: 100%

### 2. Ranker มีปัญหาเรื่อง Family Ranking
- Top-1 accuracy: 33.3% (1/3 known-positive variants)
- solr_velocity: CORRECT (4/0 signals)
- redis: WRONG (predicted couchdb_auth instead)
- grafana: WRONG (predicted redis instead, grafana not in top 5)

### 3. Unknown Guard ทำงานถูกต้อง 100%
- 5 unknown-family targets correctly rejected
- All targets with unknown products (Drupal, Laravel, Jetty, PHP-CGI, JBoss) correctly identified

### 4. Feature Gaps ที่พบ

#### 4.1 Product Detection Features
- ต้องเพิ่ม features สำหรับ detect product ที่ไม่อยู่ใน known families:
  - drupal_detected
  - laravel_detected
  - jetty_detected
  - wordpress_detected
  - php_cgi_detected
  - apache_detected
  - jboss_detected
  - coldfusion_detected

#### 4.2 Family-Specific Features
- ต้องเพิ่ม features สำหรับ grafana family:
  - grafana_path_traversal_signal
  - grafana_plugin_access
  - grafana_metrics_exposure
- ต้องเพิ่ม features สำหรับ redis family:
  - redis_lua_sandbox_signal
  - redis_auth_required
  - redis_anonymous_access

#### 4.3 Gate v02 Training Suggestions
- เพิ่ม product_detection_confidence score
- เพิ่ม known_family_signal_ratio
- เพิ่ม unknown_family_signal_ratio
- เพิ่ม version_confidence_score
- เพิ่ม auth_strength_score

### 5. Ranker Improvements
- เพิ่ม product-specific features ใน FAMILY_FEATURES
- ปรับปรุง family ranking สำหรับ HTTP targets
- เพิ่ม more family-specific positive signals
-  рассмотреть adding grafana to known candidate families (already there but ranker doesn't pick it)

## สรุปผลรวม
- Gate: สมบูรณ์แบบ (100% accuracy)
- Ranker: ต้องปรับปรุง (33% top-1 accuracy)
- Unknown Guard: สมบูรณ์แบบ (100% rejection rate)
- Final Flow: สมบูรณ์แบบ (100% accuracy)
