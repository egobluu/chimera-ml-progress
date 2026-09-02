# UNSEEN-SOLR-SCHEMA-VALIDATION-TH

## สรุปผลการดำเนินงาน

### ข้อมูลทั่วไป
- **งาน**: Unseen Solr validation after schema fix
- **วันที่**: 2026-09-02
- **เป้าหมาย**: ทดสอบว่า Solr feature extractor/probe ที่แก้แล้วสามารถสร้าง evidence ถูกต้องกับ target ใหม่ที่ไม่ใช่ชุด train/backfill เดิมหรือไม่

### ผลลัพธ์

| Target | Source | Expected | Actual | Safe to Merge |
|--------|--------|----------|--------|---------------|
| solr_positive_unseen_01 | vulhub/solr:8.1.1 | validated_positive | validated_positive | ✓ |
| solr_positive_unseen_02 | vulhub/solr:8.2.0 | validated_positive | validated_positive | ✓ |
| solr_negative_unseen_01 | vulhub/solr:8.2.0 | validated_negative | validated_negative | ✓ |
| solr_negative_unseen_02 | vulhub/solr:8.1.1 | validated_negative | validated_negative | ✓ |

**Total**: 4/4 safe_to_merge, 0 quarantined

### สรุป
1. **positive ใหม่ผ่านกี่ตัว**: 2/2
2. **negative ใหม่ผ่านกี่ตัว**: 2/2
3. **target ไหน quarantine**: ไม่มี
4. **extractor ยังส่ง field ผิดไหม**: ไม่ผิด - ทุก target มี field ครบถ้วนตาม schema
5. **ถ้าให้ Codex เอาไปรัน ML ต่อ ควรใช้ไฟล์ไหน**: `unseen-solr-features.jsonl`

### Feature Schema (22 features)
- target_id, category, expected_family, expected_status
- solr_detected, solr_core_found
- velocity_enabled, velocity_disabled, velocity_endpoint_found, velocity_template_accessible, velocity_rce_candidate
- config_api_accessible, config_api_blocked
- version_in_vulnerable_range, version_not_affected, version_patched
- auth_required, no_auth_required, anonymous_access
- known_family_signal_count, unknown_family_signal_count, unknown_product_detected

### Probe Logic
1. เช็ค /solr/
2. เช็ค /solr/admin/cores?action=STATUS&wt=json
3. เช็ค /solr/{core}/config?wt=json
4. ตรวจว่า solrconfig มี VelocityResponseWriter หรือไม่
5. test wt=velocity ว่าตอบเป็น Velocity template จริงหรือ fallback เป็น JSON

### Validation Rules
- **positive safe_to_merge**: solr_detected=1, solr_core_found=1, velocity_enabled=1, config_api_accessible=1
- **negative safe_to_merge**: solr_detected=1, velocity_disabled=1, velocity_enabled=0

### ไฟล์ผลลัพธ์
- `/home/kali/reports/dec-unseen-solr-schema-validation-2026-09-02/raw-curated/`
- `/media/sf_kali-share/dataset/dec-unseen-solr-schema-validation-2026-09-02/`

### Merge Decision
- **Safe to merge**: 4/4
- **Quarantined**: 0
- **Next**: Run ML pipeline training with unseen Solr targets
