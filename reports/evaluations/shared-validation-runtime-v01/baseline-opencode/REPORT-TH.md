# REPORT-TH: Shared Validation Runtime Evaluation v01

## 1. Dataset Sources

### 1.1 Dataset ที่ใช้ในการ evaluation

| Dataset | Path | Targets | Description |
|---------|------|---------|-------------|
| dec-multifamily-unseen-validation-2026-09-02 | `/media/sf_kali-share/dataset/` | 10 | Multi-family unseen validation (Redis, Grafana, Tomcat PUT, Tomcat AJP, CouchDB) |
| dec-unknown-multifamily-unseen-validation-2026-09-02 | `/media/sf_kali-share/dataset/` | 22 | Unknown-family + multi-family unseen (Redis, Grafana, Tomcat, CouchDB, Solr, Drupal, Jenkins, Elasticsearch, JBoss, Jetty, nginx, MySQL, phpMyAdmin, Shiro, ThinkPHP) |
| dec-ranker-guard-unknown-validation-2026-09-02 | `/media/sf_kali-share/dataset/` | 24 | Ranker guard validation (Known family 12, Unknown family 6, Weak/noisy 6) |

### 1.2 Total targets
- **Total**: 56 targets
- **Known positive**: 19 targets
- **Unknown family positive**: 9 targets
- **Negative control**: 28 targets

## 2. Scan Evidence -> Feature -> ML Runtime Flow

### 2.1 Scan Evidence
- ใช้เครื่องมือสแกน เช่น naabu, nmap, httpx, nuclei, curl, redis-cli
- เก็บ raw evidence ไว้ใน raw/ folder ของแต่ละ target

### 2.2 Feature Extraction
- แปลง raw evidence เป็น feature JSON ตาม schema ที่กำหนด
- แต่ละ family มี feature set เฉพาะของตัวเอง
- ไม่ใช้ Metasploit/manual exploit result เป็น feature

### 2.3 ML Runtime
- **Gate Model**: XGBClassifier ตัดสินใจว่า target ควรลอง exploit ต่อไหม
- **Family Ranker**: XGBRanker จัดอันดับ exploit family ที่เหมาะสม
- **Unknown-family Guard**: ป้องกันไม่ให้ unknown family ผ่านเป็น known_family_ready
- **CVE/Module Resolver**: Mapping table จาก family -> CVE/module/manual PoC

## 3. Gate Model

### 3.1 คืออะไร
Gate คือ binary classifier ที่ตัดสินใจว่า target นี้ควรลอง exploit ต่อไหม

### 3.2 Decision Logic
- `likely_exploitable`: ผ่าน gate ไปยัง family ranker
- `low_confidence`: ต้องการ evidence เพิ่ม
- `no_exploit`: ไม่ควร exploit ตอนนี้

### 3.3 Metrics
| Metric | Value | Description |
|--------|-------|-------------|
| TP | 19 | known_positive correctly passed |
| FP | 4 | negative_control incorrectly passed |
| TN | 24 | negative_control correctly blocked |
| FN | 0 | known_positive incorrectly blocked |
| Accuracy | 0.9149 | ความแม่นรวม |
| Precision | 0.8261 | ความแม่นเมื่อทำนาย positive |
| Recall | 1.0000 | ความครอบคลุม positive ทั้งหมด |
| F1 | 0.9048 | harmonic mean ของ precision และ recall |

## 4. Family Ranker

### 4.1 คืออะไร
Family Ranker คือ XGBRanker ที่จัดอันดับ exploit family ที่เหมาะสมกับ target

### 4.2 Decision Logic
- `known_family_ready`: มี known-family signal พอ ไม่มี negative signal
- `known_family_but_blocked_or_low_confidence`: มี signal แต่ไม่พอหรือมี blocking
- `unknown_family`: ไม่รู้จัก family นี้

### 4.3 Metrics
| Metric | Value | Description |
|--------|-------|-------------|
| Total known positive | 19 | known positive ที่ผ่าน gate |
| Top-1 accuracy | 1.0000 | family ที่ทำนายอันดับ 1 ถูกต้อง |
| Top-3 accuracy | 1.0000 | family ที่ทำนายอยู่ใน top 3 ถูกต้อง |

**หมายเหตุ**: ผล 1.0000 เป็น subset/sanity check เนื่องจากทุก known positive ผ่าน gate ทั้งหมด ไม่ใช่ production accuracy

## 5. Unknown-family Guard

### 5.1 คืออะไร
Unknown-family guard ป้องกันไม่ให้ unknown family ผ่านเป็น known_family_ready

### 5.2 Metrics
| Metric | Value | Description |
|--------|-------|-------------|
| Total unknown-family positive | 9 | unknown family ทั้งหมด |
| Blocked (unknown_family_triage) | 9/9 = 1.0000 | ถูกกันเป็น unknown_family_triage |
| Leaked (ready_for_safe_verification) | 0/9 = 0.0000 | หลุดเป็น known_family_ready |

### 5.3 Summary
- ไม่มี unknown family หลุดเป็น known_family_ready
- ทุก unknown family ถูกกันเป็น unknown_family_triage

## 6. Weak/Noisy Guard

### 6.1 คืออะไร
Weak/noisy guard ป้องกันไม่ให้ negative control ผ่านเป็น ready_for_safe_verification

### 6.2 Metrics
| Metric | Value | Description |
|--------|-------|-------------|
| Total negative_control | 28 | negative control ทั้งหมด |
| Blocked | 27/28 = 0.9643 | ถูกกันไม่ให้ exploit |
| Leaked | 1/28 = 0.0357 | หลุดเป็น ready_for_safe_verification |

### 6.3 Leaked Target
- `redis_weak_guard_01`: Redis with EVAL command disabled (partial features)

## 7. Resolver Readiness

### 7.1 สถานะปัจจุบัน
Resolver ควรเป็น mapping table ไม่ใช่ ML model

### 7.2 Known Families with Mapping
| Family | CVE | Module | Status |
|--------|-----|--------|--------|
| redis | CVE-2022-0543 | redis_lua_sandbox_escape | mapped |
| grafana | CVE-2021-43798 | grafana_path_traversal | mapped |
| couchdb_auth | CVE-2017-12635 | couchdb_auth_bypass | mapped |
| solr_velocity | CVE-2019-17558 | solr_velocity_rce | mapped |
| tomcat_put | CVE-2017-12615 | tomcat_put_upload | mapped |
| tomcat_ajp | CVE-2020-1938 | tomcat_ajp_ghostcat | mapped |
| jenkins | CVE-2019-1003000 | jenkins_script_console | mapped |
| elasticsearch | CVE-2015-1427 | elasticsearch_rce | mapped |
| shiro_key | CVE-2016-4437 | shiro_deserialize | mapped |
| thinkphp_rce | CVE-2018-20062 | thinkphp_rce | mapped |
| joomla | CVE-2017-8917 | joomla_sql_injection | mapped |
| nextjs | CVE-2024-34351 | nextjs_ssrf | mapped |
| nexus | CVE-2019-7238 | nexus_rce | mapped |
| struts2 | CVE-2017-5638 | struts2_rce | mapped |
| flask | N/A | flask_ssti | needs_research |
| nginx | CVE-2021-23017 | nginx_dns_rebinding | needs_research |

### 7.3 Unknown Families (Needs Integration)
| Family | CVE | Module | Status |
|--------|-----|--------|--------|
| drupal_rce | CVE-2018-7600 | drupal_rce | needs_integration |
| jboss_rce | CVE-2017-12149 | jboss_deserialize | needs_integration |
| jetty_rce | CVE-2017-9793 | jetty_admin_handler | needs_integration |
| laravel_rce | CVE-2021-3129 | laravel_ignition | needs_integration |
| wordpress_rce | CVE-2019-6977 | wordpress_xmlrpc | needs_integration |
| php_cgi_rce | CVE-2012-1823 | php_cgi_arg_injection | needs_integration |

### 7.4 Resolver Coverage
- Known families mapped: 14/16
- Known families needs research: 2/16
- Unknown families needs integration: 6
- Total resolver coverage: 14/22 = 63.64%

## 8. ปัญหาที่ยังเหลือ

### 8.1 Gate Issues
- FP: 4 negative_control หลุดเป็น likely_exploitable
- ต้องปรับปรุง negative precondition features

### 8.2 Weak/Noisy Guard Issues
- 1 negative_control หลุดเป็น ready_for_safe_verification
- redis_weak_guard_01: Redis with EVAL command disabled

### 8.3 Resolver Issues
- 2 known families ยัง needs_research (flask, nginx)
- 6 unknown families ยัง needs_integration
- Resolver coverage 仅 63.64%

## 9. คำแนะนำ

### 9.1 Merge/Retrain
- **Merge**: ได้ 56 targets ใหม่เข้า training set
- **Retrain**: ควร retrain gate model ด้วย negative precondition features ที่ปรับปรุงแล้ว

### 9.2 Validation-only
- เก็บผล evaluation นี้เป็น validation-only
- ไม่ควรใช้ผลนี้เป็น production accuracy เนื่องจากเป็น subset/sanity check

### 9.3 Next Steps
1. ปรับปรุง negative precondition features เพื่อลด FP
2. ปรับปรุง weak/noisy guard เพื่อลด leakage
3. เพิ่ม resolver coverage สำหรับ unknown families
4. Re-evaluate หลัง retrain
