# UNSEEN VALIDATION V04 HONEST - SUMMARY (TH)

## คำถามที่ต้องตอบ

### 1. นี่คือ honest unseen หรือ post-hoc?
**ตอบ**: นี่คือ honest unseen validation ไม่ใช่ post-hoc
- ไม่ได้แก้ไข runtime ระหว่างทดสอบ
- ไม่ได้ retrain model
- ไม่ได้แก้ features หลัง prediction
- ทำนายก่อน verification เสมอ

### 2. เป้าหมายไหนที่สำเร็จ?
**ตอบ**: 12/12 targets สำเร็จทั้งหมด
- Known-positive: 4 targets (redis_lua, tomcat_put, solr_velocity, grafana_path)
- Negative controls: 4 targets (redis_auth, grafana_patched, solr_no_velocity, tomcat_standard)
- Unknown-family: 4 targets (laravel, jboss, jetty, thinkphp)

### 3. ML ทำนายอะไรก่อน verification?
**ตอบ**:
- Gate: likely_exploitable (11 targets), no_exploit (1 target), low_confidence (0 targets)
- Ranker: known_family_ready (8 targets), known_family_but_blocked_or_low_confidence (2 targets), null (2 targets)

### 4. Verification ยืนยันอะไร?
**ตอบ**:
- Known-positive: 4/4 validated_positive
- Negative controls: 3/4 validated_negative, 1/4 gate_fp (solr_no_velocity)
- Unknown-family: 4/4 validated_positive

### 5. Gate ผิดพลาดตรงไหน?
**ตอบ**:
- FP: 1 target (solr_no_velocity_neg_v04) - Solr 9.7.0 ไม่มี vulnerability แต่ gate บอก likely_exploitable
- FN: 0 targets

### 6. Ranker ผิดพลาดตรงไหน?
**ตอบ**:
- Top-1 miss: 1 target (solr_velocity_new_01) - ranker เลือก nexus #1 แทน solr_velocity
- Top-1 accuracy: 0.75 (3/4)

### 7. Unknown guard ทำงานไหม?
**ตอบ**: ไม่ทำงานตามที่คาดหวัง
- Unknown-family targets ไม่ได้ถูก force เป็น unknown_family_triage
- แต่ ranker ไม่มี family ที่ตรงกับ targets เหล่านี้

### 8. บันทึกไหน safe to merge ภายหลัง?
**ตอบ**: ทั้งหมด 12 targets safe to merge
- redis_lua_new_01
- tomcat_put_new_02
- solr_velocity_new_01
- grafana_path_new_01
- redis_auth_neg_v04
- grafana_patched_neg_v04
- solr_no_velocity_neg_v04 (FP แต่ verified negative)
- tomcat_standard_neg_v04
- laravel_unknown_v04
- jboss_unknown_v04
- jetty_unknown_v04
- thinkphp_unknown_v04

### 9. บันทึกไหน quarantine?
**ตอบ**: ไม่มีบันทึกที่ต้อง quarantine

### 10. Codex ควรแก้ไขอะไรต่อไป?
**ตอบ**:
1. **แก้ Gate FP**: เพิ่ม negative signal สำหรับ version ที่ patch แล้ว
2. **แก้ Ranker Top-1**: เพิ่ม signal สำหรับ solr_detected
3. **แก้ Unknown Guard**: ตรวจสอบ unknown_product_detected flag และ force unknown_family_triage
4. **ลด Disk Usage**: ลบ images ที่ไม่ใช้ก่อนทดสอบ

## ผลรวม

### Gate Metrics
- TP: 8, TN: 3, FP: 1, FN: 0
- Accuracy: 0.9167
- Precision: 0.8889
- Recall: 1.0
- F1: 0.9412

### Ranker Metrics (Known-Positive)
- Top-1 Accuracy: 0.75 (3/4)

### Unknown Guard Metrics
- Accuracy: 0.0 (0/4 correct rejection)

### Safety Flow Metrics
- Accuracy: 0.9167 (11/12)

### Strict Flow Metrics
- Accuracy: 0.8333 (10/12)
