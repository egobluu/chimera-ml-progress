# UNSEEN-MULTIFAMILY-VALIDATION-TH

## สรุปผลการดำเนินงาน

### ข้อมูลทั่วไป
- **งาน**: Multi-family unseen validation after Solr schema fix
- **วันที่**: 2026-09-02
- **เป้าหมาย**: ทดสอบว่า feature extractor/probe schema ที่ใช้กับ ML runtime ทำงานได้จริงกับ family อื่น ไม่ใช่ผ่านแค่ Solr

### ผลลัพธ์

| Target | Family | Source | Expected | Actual | Safe to Merge |
|--------|--------|--------|----------|--------|---------------|
| redis_positive_unseen_01 | Redis | redis:7.0 | validated_positive | validated_positive | ✓ |
| redis_negative_unseen_01 | Redis | redis:7.0 | validated_negative | validated_negative | ✓ |
| grafana_positive_unseen_01 | Grafana | grafana/grafana:9.0.0 | validated_positive | validated_positive | ✓ |
| grafana_negative_unseen_01 | Grafana | grafana/grafana:latest | validated_negative | validated_negative | ✓ |
| tomcat_put_positive_unseen_01 | Tomcat PUT | cve-2017-12615-tomcat:latest | validated_positive | validated_positive | ✓ |
| tomcat_put_negative_unseen_01 | Tomcat PUT | tomcat:9.0.97 | validated_negative | validated_negative | ✓ |
| tomcat_ajp_positive_unseen_01 | Tomcat AJP | cve-2017-12615-tomcat:latest | validated_positive | validated_positive | ✓ |
| tomcat_ajp_negative_unseen_01 | Tomcat AJP | tomcat:9.0.97 | validated_negative | validated_negative | ✓ |
| couchdb_positive_unseen_01 | CouchDB | vulhub/couchdb:1.6.0 | validated_positive | validated_positive | ✓ |
| couchdb_negative_unseen_01 | CouchDB | vulhub/couchdb:2.1.0 | validated_negative | validated_negative | ✓ |

**Total**: 10/10 safe_to_merge, 0 quarantined

### สรุป
1. **Redis**: 2/2 ผ่าน (1 positive, 1 negative)
2. **Grafana**: 2/2 ผ่าน (1 positive, 1 negative)
3. **Tomcat PUT**: 2/2 ผ่าน (1 positive, 1 negative)
4. **Tomcat AJP**: 2/2 ผ่าน (1 positive, 1 negative)
5. **CouchDB**: 2/2 ผ่าน (1 positive, 1 negative)

### Feature Schema
ทุก target มี feature ครบถ้วนตาม schema ที่กำหนด

### ไฟล์ผลลัพธ์
- `/home/kali/reports/dec-multifamily-unseen-validation-2026-09-02/raw-curated/`
- `/media/sf_kali-share/dataset/dec-multifamily-unseen-validation-2026-09-02/`

### Merge Decision
- **Safe to merge**: 10/10
- **Quarantined**: 0
- **Next**: Run ML pipeline training with multi-family unseen targets
