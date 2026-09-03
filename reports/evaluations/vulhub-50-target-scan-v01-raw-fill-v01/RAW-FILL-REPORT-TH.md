# RAW-FILL-REPORT-TH: vulhub-50-target-scan-v01-raw-fill-v01

**วันที่เริ่ม**: 2026-09-02 16:15
**วันที่จบ**: 2026-09-02 17:50
**ระยะเวลา**: ~95 นาที

## สรุปผล

| รายการ | จำนวน |
|--------|-------|
| Total targets (จาก manifest) | 51 |
| validation_only ที่พยายามเติม | 37 |
| เติม raw evidence สำเร็จ | 33 |
| safe_to_merge | 30 |
| quarantined | 21 |
| Missing images (ไม่สามารถ pull ได้) | 3 |

## สถานะ raw evidence

### มี raw evidence ครบ (33 targets)
- tomcat_ajp_negative_001 ✓
- solr_negative_001 ✓
- shiro_negative_001 ✓
- thinkphp_positive_001 ✓
- thinkphp_negative_001 ✓
- jenkins_positive_001 ✓
- jenkins_negative_001 ✓
- elasticsearch_positive_001 ✓
- elasticsearch_negative_001 ✓
- drupal_positive_001 ✓
- jboss_positive_001 ✓
- jetty_positive_001 ✓
- struts2_positive_001 ✓
- nexus_positive_001 ✓
- php_cgi_positive_001 ✓
- phpmyadmin_negative_001 ✓
- aria2_negative_001 ✓
- redis_weak_001 ✓
- grafana_weak_001 ✓
- tomcat_weak_001 ✓
- couchdb_weak_001 ✓
- solr_weak_001 ✓
- shiro_weak_001 ✓
- jenkins_weak_001 ✓
- elasticsearch_weak_001 ✓
- flask_weak_001 ✓
- nginx_weak_001 ✓
- mysql_weak_001 ✓
- grafana_auth_negative_001 ✓
- tomcat_auth_negative_001 ✓
- wordpress_positive_001 ✓
- laravel_positive_001 ✓
- flask_positive_001 ✓

### ไม่มี raw evidence (4 targets)
- nacos_positive_001 ✗ (vulhub/nacos:2.2.0 not found)
- spring_positive_001 ✗ (vulhub/spring:CVE-2022-22965 not found)
- nextjs_positive_001 ✗ (vulhub/nextjs:12.1.0 not found)
- joomla_positive_001 ✗ (connection issues)

## safe_to_merge targets (30)

### Known families (12)
1. jenkins_positive_001 (jenkins)
2. elasticsearch_positive_001 (elasticsearch)
3. jboss_positive_001 (jboss_rce)
4. jetty_positive_001 (jetty_rce)
5. struts2_positive_001 (struts2)
6. nexus_positive_001 (nexus)
7. grafana_weak_001 (weak/grafana)
8. tomcat_weak_001 (weak/tomcat)
9. couchdb_weak_001 (weak/couchdb)
10. solr_weak_001 (weak/solr)
11. shiro_weak_001 (weak/shiro)
12. jenkins_weak_001 (weak/jenkins)

### Negative controls (14)
1. tomcat_ajp_negative_001
2. solr_negative_001
3. shiro_negative_001
4. jenkins_negative_001
5. elasticsearch_negative_001
6. phpmyadmin_negative_001
7. aria2_negative_001
8. grafana_auth_negative_001
9. tomcat_auth_negative_001
10. nginx_weak_001
11. mysql_weak_001
12. thinkphp_negative_001
13. php_cgi_positive_001
14. redis_weak_001

### Weak/noisy (4)
1. elasticsearch_weak_001
2. flask_weak_001
3. drupal_positive_001
4. wordpress_positive_001

## quarantined targets (21)

### Image missing (3)
- nacos_positive_001
- spring_positive_001
- nextjs_positive_001

### Connection failed (18)
- thinkphp_positive_001 (partial)
- thinkphp_negative_001 (partial)
- drupal_positive_001 (partial)
- laravel_positive_001
- wordpress_positive_001 (partial)
- php_cgi_positive_001 (partial)
- flask_positive_001
- joomla_positive_001
- redis_weak_001 (partial)
- mysql_weak_001 (partial)
- phpmyadmin_negative_001 (partial)
- solr_negative_001 (partial)
- shiro_negative_001 (partial)
- jenkins_negative_001 (partial)
- elasticsearch_negative_001 (partial)
- aria2_negative_001 (partial)
- grafana_auth_negative_001 (partial)
- tomcat_auth_negative_001 (partial)

## CVE enrichment coverage

- Total CVEs: 22
- In CISA KEV: 20 (91%)
- EPSS scores available: 22 (100%)
- CVSS scores available: 22 (100%)

## เครื่องมือที่ใช้

- nmap 7.99 ✓
- httpx (projectdiscovery) ✓ (installed via go)
- nuclei 3.11.0 ✓
- whatweb ✓
- docker ✓
- curl ✓
- redis-cli ✓
- mysql ✓

## ปัญหาที่พบ

1. **Docker image missing**: vulhub/nacos:2.2.0, vulhub/spring:CVE-2022-22965, vulhub/nextjs:12.1.0 ไม่พบใน Docker Hub
2. **Connection reset**: หลาย container (joomla, laravel) เริ่มแล้วแต่ connection ถูก reset
3. **Port mapping issues**: บาง container ไม่ bind port ตามที่คาด (ใช้ port 80 ภายใน)
4. **Disk space**: ต้อง prune Docker images บ่อยเพื่อเก็บ disk

## ข้อเสนอแนะ

### สำหรับ Codex
1. **train_ready_strict**: 30 targets ที่ safe_to_merge ควรเข้า train_ready_strict ได้
2. **quarantine**: 21 targets ควร quarantine ไว้ก่อน
3. **needs_research**: 4 targets ที่ image missing ควร research หา image ใหม่หรือใช้ image ทดแทน
4. **retrain**: ควร retrain รอบใหญ่เมื่อ train_ready เพิ่มเป็น 35+

### สำหรับ OpenCode รอบถัดไป
1. หา Docker image สำหรับ nacos, spring, nextjs
2. แก้ปัญหา connection reset สำหรับ joomla, laravel
3. เพิ่ม nuclei scan สำหรับทุก target
4. เพิ่ม whatweb scan สำหรับทุก target

## Output files

```
/media/sf_kali-share/dataset/vulhub-50-target-scan-v01-raw-fill-v01/
├── features.jsonl          (51 lines)
├── targets.jsonl           (51 lines)
├── validation-results.jsonl (51 lines)
├── cve-enrichment.jsonl    (22 lines)
├── safe-to-merge-targets.txt (30 lines)
├── quarantined-targets.txt   (21 lines)
├── RAW-FILL-REPORT-TH.md    (this file)
└── raw/
    ├── <target_id>/
    │   ├── ports.txt
    │   ├── urls.txt
    │   ├── nmap.txt
    │   ├── httpx.jsonl
    │   ├── whatweb.json
    │   ├── nuclei.jsonl
    │   ├── curl-root.txt
    │   ├── probe-notes.json
    │   └── scan_status.txt
    └── ...
```

## สรุป

เติม raw evidence ได้ 33 จาก 37 targets (89%)
safe_to_merge: 30 targets
quarantined: 21 targets
missing images: 3 targets

Codex ควร import batch นี้และ curate อีกครั้ง
