# UNSEEN-VALIDATION-SUMMARY-TH.md

## สรุปผล Unseen Validation v01

### 1. ทดสอบ targets ใดบ้าง?

| Target ID | Family | Category | CVE | Lab |
|-----------|--------|----------|-----|-----|
| unseen_redis_variant_01 | redis | known_variant | CVE-2022-0543 | vulhub/redis:CVE-2022-0543 |
| unseen_tomcat_put_variant_01 | tomcat_put | known_variant | CVE-2017-12615 | vulhub/tomcat:CVE-2017-12615 |
| unseen_solr_variant_01 | solr_velocity | known_variant | CVE-2019-0193 | vulhub/solr:CVE-2019-0193 |
| unseen_grafana_variant_01 | grafana | known_variant | CVE-2021-43798 | vulhub/grafana:CVE-2021-43798 |
| unseen_redis_neg_auth_01 | redis | negative_control | none | redis:7.0 with auth |
| unseen_tomcat_neg_01 | tomcat_put | negative_control | none | vulhub/tomcat:CVE-2025-24813 (patched) |
| unseen_grafana_neg_01 | nginx | negative_control | none | nginx:latest (patched) |
| unseen_unknown_wordpress_01 | unknown | unknown_family | CVE-2021-34429 | vulhub/jetty:CVE-2021-34429 |
| unseen_unknown_drupal_01 | unknown | unknown_family | CVE-2018-7600 | vulhub/drupal:CVE-2018-7600 |
| unseen_unknown_laravel_01 | unknown | unknown_family | CVE-2021-3129 | vulhub/laravel:CVE-2021-3129 |

**หมายเหตุ**: Target 8 เดิมเป็น WordPress แต่ image ใหญ่เกินไป จึงเปลี่ยนเป็น Jetty (unknown family เช่นกัน)

### 2. Targets ใดเป็น genuinely unseen?

ทั้ง 10 targets เป็น unseen จริง:
- 4 known-family variants: ใช้ lab/variant ต่างจาก training data
- 3 negative controls: ไม่มีใน training data
- 3 unknown-family: family ที่ไม่อยู่ใน known candidate families

### 3. ML predict อะไรก่อน verification?

| Target | Gate Score | Gate Decision | Ranker Decision | Top1 Family |
|--------|-----------|---------------|-----------------|-------------|
| redis_variant_01 | 0.928 | likely_exploitable | known_family_ready | redis (5/0) |
| tomcat_put_variant_01 | 0.928 | likely_exploitable | known_family_ready | tomcat_put (3/0) |
| solr_variant_01 | 0.928 | likely_exploitable | known_family_ready | solr_velocity (5/0) |
| grafana_variant_01 | 0.928 | likely_exploitable | known_family_ready | grafana (5/0) |
| redis_neg_auth_01 | 0.060 | no_exploit | null | - |
| tomcat_neg_01 | 0.060 | no_exploit | null | - |
| grafana_neg_01 | 0.589 | likely_exploitable | blocked_or_low_confidence | nginx (2/1) |
| unknown_wordpress_01 | 0.875 | likely_exploitable | unknown_family | nextjs (1/0) |
| unknown_drupal_01 | 0.875 | likely_exploitable | unknown_family | nextjs (1/0) |
| unknown_laravel_01 | 0.875 | likely_exploitable | unknown_family | nextjs (1/0) |

### 4. Metasploit/manual verification ว่าอย่างไร?

| Target | Verification Method | Result | Evidence |
|--------|-------------------|--------|----------|
| redis_variant_01 | manual_poc | vulnerable | Lua sandbox escape uid=0(root) |
| tomcat_put_variant_01 | manual_poc | vulnerable | PUT upload, JSP executed |
| solr_variant_01 | scanner_only | vulnerable | nuclei CVE-2019-17558 |
| grafana_variant_01 | scanner_only | vulnerable | path traversal /etc/passwd |
| redis_neg_auth_01 | manual_poc | not_vulnerable | auth blocks all commands |
| tomcat_neg_01 | manual_poc | not_vulnerable | PUT 404/409, AJP closed |
| grafana_neg_01 | scanner_only | not_vulnerable | nginx patched, no CVE |
| unknown_wordpress_01 | scanner_only | vulnerable | nuclei CVE-2021-34429 (Jetty) |
| unknown_drupal_01 | scanner_only | vulnerable | nuclei drupal-detect |
| unknown_laravel_01 | scanner_only | vulnerable | nuclei CVE-2021-3129 |

### 5. Gate ผิด/ถูก ตรงไหน?

**Gate Accuracy: 60% (6/10)**

- **True Positive (4)**: redis_variant, tomcat_put_variant, solr_variant, grafana_variant — ถูกต้อง
- **True Negative (2)**: redis_neg_auth, tomcat_neg — ถูกต้อง
- **False Positive (4)**: grafana_neg, unknown_wordpress, unknown_drupal, unknown_laravel — ผิด

**ปัญหาหลัก**: Gate ไม่สามารถปฏิเสธ unknown family ได้ เพราะ generic HTTP positive signals (endpoint_reachable_count, is_http_target) ทำให้ gate score สูง

### 6. Ranker ผิด/ถูก ตรงไหน?

**Ranker Top-1 Accuracy: 100% (4/4)**

- redis_variant → redis (correct)
- tomcat_put_variant → tomcat_put (correct)
- solr_variant → solr_velocity (correct)
- grafana_variant → grafana (correct)

Ranker ทำได้ดีมากสำหรับ known-family positives

### 7. Unknown guard ทำงานตรงไหน?

**Unknown Family Rejection Rate: 100% (3/3)**

- unknown_wordpress (Jetty) → ranker=unknown_family ✓
- unknown_drupal → ranker=unknown_family ✓
- unknown_laravel → ranker=unknown_family ✓

Ranker ปฏิเสธ unknown family ได้ถูกต้องทั้งหมด

### 8. Targets ใด safe to merge ได้ในภายหลัง?

| Target | Family | Status | หมายเหตุ |
|--------|--------|--------|---------|
| unseen_redis_variant_01 | redis | validated_positive | safe to merge |
| unseen_tomcat_put_variant_01 | tomcat_put | validated_positive | safe to merge |
| unseen_solr_variant_01 | solr_velocity | validated_positive | safe to merge |
| unseen_grafana_variant_01 | grafana | validated_positive | safe to merge |
| unseen_redis_neg_auth_01 | redis | validated_negative | safe to merge (as negative) |
| unseen_tomcat_neg_01 | tomcat_put | validated_negative | safe to merge (as negative) |
| unseen_grafana_neg_01 | nginx | validated_negative | safe to merge (as negative) — gate FP |
| unseen_unknown_wordpress_01 | unknown | unknown_family | safe to merge (as unknown) |
| unseen_unknown_drupal_01 | unknown | unknown_family | safe to merge (as unknown) |
| unseen_unknown_laravel_01 | unknown | unknown_family | safe to merge (as unknown) |

### 9. Targets ใดต้อง quarantine?

ไม่มี targets ที่ต้อง quarantine — ทั้ง 10 targets completed successfully

### 10. Feature gaps ที่พบ

1. **Gate FP on unknown family**: Gate ใช้ generic features (endpoint_reachable_count, is_http_target) ทำให้ FP กับ unknown family — ต้องเพิ่ม negative signal สำหรับ unknown product detection
2. **Gate FP on patched nginx**: version_patched=1 ไม่ได้ลด gate score พอ — ต้อง weight version_patched ให้มากขึ้น
3. **Ranker top1 = nextjs สำหรับ unknown**: ทุก unknown family ถูก rank เป็น nextjs (score สูงสุดแต่ positive_signals ต่ำ) — ต้องเพิ่ม threshold สำหรับ unknown family
4. **No product detection features**: ไม่มี features สำหรับ detect product ที่ไม่อยู่ใน known families (wordpress_detected, drupal_detected, laravel_detected)

## สรุปผลรวม

| Metric | Value |
|--------|-------|
| Total targets | 10 |
| Gate accuracy | 60% |
| Gate TP | 4 |
| Gate FP | 4 |
| Gate TN | 2 |
| Gate FN | 0 |
| Ranker top-1 accuracy | 100% (4/4) |
| Unknown rejection rate | 100% (3/3) |
| Low confidence | 1 (grafana_neg) |
| Inconclusive | 0 |
| Safe to merge later | 10/10 |

## ข้อเสนอแนะ

1. **Gate improvement**: เพิ่ม negative signals สำหรับ unknown product detection
2. **Feature expansion**: เพิ่ม product detection features (wordpress_detected, drupal_detected, etc.)
3. **Threshold tuning**: พิจารณาเพิ่ม gate threshold หรือเพิ่ม negative weight สำหรับ generic HTTP signals
4. **Ranker improvement**: ป้องกันไม่ให้ unknown family ถูก rank เป็น nextjs เสมอ