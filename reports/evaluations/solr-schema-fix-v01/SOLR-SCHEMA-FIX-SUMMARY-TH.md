# SOLR-SCHEMA-FIX-SUMMARY-TH

## สรุปผลการดำเนินงาน

### ข้อมูลทั่วไป
- **งาน**: Fix Solr feature extractor/probe schema แล้ว rerun Solr-only validation
- **วันที่**: 2026-09-02
- **เป้าหมาย**: ทำให้ Solr ทุก target สร้าง feature schema เดียวกัน และใช้เป็นข้อมูล train ML ได้จริง

### ผลลัพธ์

| Target | Source | Expected | Actual | Safe to Merge |
|--------|--------|----------|--------|---------------|
| solr_velocity_positive_v04_fix | vulhub/solr:8.2.0 | validated_positive | validated_positive | ✓ |
| solr_velocity_positive_alt | vulhub/solr:7.0.1 | validated_positive | validated_positive | ✓ |
| solr_negative_v04_1 | solr:9.7.0 | validated_negative | validated_negative | ✓ |
| solr_negative_v04_2 | vulhub/solr:8.2.0 | validated_negative | validated_negative | ✓ |
| solr_velocity_negative_disabled | solr:9.7.0 | validated_negative | validated_negative | ✓ |

**Total**: 5/5 safe_to_merge, 0 quarantined

### Feature Schema
- target_id
- expected_family
- expected_status
- solr_detected
- solr_core_found
- velocity_enabled
- velocity_disabled
- velocity_endpoint_found
- velocity_template_accessible
- velocity_rce_candidate
- config_api_accessible
- config_api_blocked
- version_in_vulnerable_range
- version_not_affected
- version_patched
- auth_required
- no_auth_required
- anonymous_access
- known_family_signal_count
- unknown_family_signal_count
- unknown_product_detected

### Probe Logic
1. เช็ค /solr/
2. เช็ค /solr/admin/cores?action=STATUS&wt=json
3. เช็ค /solr/{core}/config?wt=json
4. ตรวจว่า solrconfig มี VelocityResponseWriter หรือไม่
5. test wt=velocity ว่าตอบเป็น Velocity template จริงหรือ fallback เป็น JSON
6. ถ้า VelocityResponseWriter มีและ wt=velocity ทำงาน ให้ velocity_enabled=1
7. ถ้าไม่มี VelocityResponseWriter หรือ wt=velocity fallback เป็น JSON ให้ velocity_disabled=1
8. ถ้า config API เข้าไม่ได้ ให้ config_api_blocked=1

### Validation Rules
- **positive safe_to_merge**: solr_detected=1, solr_core_found=1, velocity_enabled=1, config_api_accessible=1
- **negative safe_to_merge**: solr_detected=1, solr_core_found=1, velocity_disabled=1, expected_status=validated_negative
- **quarantine**: velocity_enabled กับ velocity_disabled เป็น 1 พร้อมกัน, หรือ expected negative แต่ velocity_enabled=1, หรือ expected positive แต่ velocity_enabled=0

### ไฟล์ผลลัพธ์
- `/home/kali/reports/dec-solr-schema-fix-2026-09-02/raw-curated/`
- `/media/sf_kali-share/dataset/dec-solr-schema-fix-2026-09-02/`

### Merge Decision
- **Safe to merge**: 5/5
- **Quarantined**: 0
- **Next**: Run ML pipeline training with Solr schema-fixed targets
