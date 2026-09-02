# Feature Gap Notes (TH)

## ปัญหาที่พบ

### 1. Gate False Positive: solr_no_velocity_neg_v04
- **ปัญหา**: Solr 9.7.0 ไม่มี vulnerability แต่ gate บอก likely_exploitable
- **สาเหตุ**: version_in_vulnerable_range_false ไม่ได้กด gate score ลงมากพอ
- **แนะนำ**: เพิ่ม negative signal สำหรับ version ที่ patch แล้ว

### 2. Ranker Top-1 Miss: solr_velocity_new_01
- **ปัญหา**: Ranker เลือก nexus #1 แทน solr_velocity
- **สาเหตุ**: solr_velocity มี 2/0 signals แต่ nexus มี 3/0 signals
- **แนะนำ**: เพิ่ม signal สำหรับ solr_detected

### 3. Unknown Guard ไม่ทำงาน
- **ปัญหา**: Unknown-family targets ไม่ได้ถูก force เป็น unknown_family_triage
- **สาเหตุ**: Ranker ยังมี families อื่นที่มี positive signals
- **แนะนำ**: ตรวจสอบ unknown_product_detected flag และ force unknown_family_triage

### 4. Disk Space วิกฤต
- **ปัญหา**: Disk อยู่ที่ 98% (1.8G free) ตลอดการทดสอบ
- **สาเหตุ**: Docker images ขนาดใหญ่
- **แนะนำ**: ลบ images ที่ไม่ใช้ก่อนทดสอบ

## ข้อสังเกต
- Gate model ทำงานได้ดี (TP=8, TN=3, FP=1, FN=0)
- Ranker ยังมีปัญหาเรื่อง family ranking (top-1 accuracy 0.75)
- Unknown guard ไม่ทำงานตามที่คาดหวัง
- Safety flow ทำงานได้ดี (0.9167)
- Strict flow ทำงานได้พอใช้ (0.8333)
