# RANKER-GUARD-UNKNOWN-VALIDATION-TH

## สรุปผลการดำเนินงาน

**วันที่**: 2026-09-02
**งาน**: Unknown-family + Ranker Guard Validation v01

## ผลลัพธ์

### Known Family Targets (12 targets)

| Target | Family | Source | Expected | Actual | Safe to Merge |
|--------|--------|--------|----------|--------|---------------|
| redis_positive_guard_01 | Redis | redis:7.0 | validated_positive | validated_positive | ✓ |
| redis_negative_guard_01 | Redis | redis:7.0 | validated_negative | validated_negative | ✓ |
| grafana_positive_guard_01 | Grafana | grafana/grafana:9.0.0 | validated_positive | validated_positive | ✓ |
| grafana_negative_guard_01 | Grafana | grafana/grafana:latest | validated_negative | validated_negative | ✓ |
| solr_positive_guard_01 | Solr | vulhub/solr:8.1.1 | validated_positive | validated_positive | ✓ |
| solr_negative_guard_01 | Solr | solr:9.7.0 | validated_negative | validated_negative | ✓ |
| tomcat_put_positive_guard_01 | Tomcat PUT | cve-2017-12615-tomcat:latest | validated_positive | validated_positive | ✓ |
| tomcat_put_negative_guard_01 | Tomcat PUT | tomcat:9.0.97 | validated_negative | validated_negative | ✓ |
| tomcat_ajp_positive_guard_01 | Tomcat AJP | cve-2017-12615-tomcat:latest | validated_positive | validated_positive | ✓ |
| tomcat_ajp_negative_guard_01 | Tomcat AJP | tomcat:9.0.97 | validated_negative | validated_negative | ✓ |
| couchdb_positive_guard_01 | CouchDB | vulhub/couchdb:1.6.0 | validated_positive | validated_positive | ✓ |
| couchdb_negative_guard_01 | CouchDB | vulhub/couchdb:2.1.0 | validated_negative | validated_negative | ✓ |

### Unknown Family Targets (6 targets)

| Target | Family | Source | Expected | Actual | Safe to Merge |
|--------|--------|--------|----------|--------|---------------|
| drupal_guard_01 | Drupal | vulhub/drupal:8.5.0 | validated_positive | validated_positive | ✓ |
| laravel_guard_01 | Laravel | vulhub/laravel:8.4.2 | validated_positive | validated_positive | ✓ |
| jetty_guard_01 | Jetty | vulhub/jetty:9.4.37 | validated_positive | validated_positive | ✓ |
| wordpress_guard_01 | WordPress | wordpress:5.0.0 | validated_positive | validated_positive | ✓ |
| php_cgi_guard_01 | PHP-CGI | vulhub/php:5.4.1-cgi | validated_positive | validated_positive | ✓ |
| jboss_guard_01 | JBoss | vulhub/jboss:as-6.1.0 | validated_positive | validated_positive | ✓ |

### Weak/Noisy Cases (6 targets)

| Target | Family | Source | Expected | Actual | Safe to Merge |
|--------|--------|--------|----------|--------|---------------|
| redis_weak_guard_01 | Redis (weak) | redis:7.0 | no_exploit | weak_no_exploit | ✓ |
| grafana_weak_guard_01 | Grafana (weak) | grafana/grafana:9.0.0 | no_exploit | weak_no_exploit | ✓ |
| solr_weak_guard_01 | Solr (weak) | solr:9.7.0 | no_exploit | weak_no_exploit | ✓ |
| tomcat_weak_guard_01 | Tomcat (weak) | tomcat:9.0.97 | no_exploit | weak_no_exploit | ✓ |
| couchdb_weak_guard_01 | CouchDB (weak) | vulhub/couchdb:2.1.0 | no_exploit | weak_no_exploit | ✓ |
| nginx_weak_guard_01 | nginx (weak) | nginx:latest | no_exploit | weak_no_exploit | ✓ |

## สรุปผล

- **Known family**: 12/12 ผ่าน (6 positive, 6 negative)
- **Unknown family**: 6/6 ผ่าน (6 positive, 0 negative)
- **Weak/noisy cases**: 6/6 ผ่าน (0 positive, 6 weak_no_exploit)
- **Total**: 24/24 ผ่าน

## Feature Schema

ทุก target มี feature ครบถ้วนตาม schema ที่กำหนด

## ไฟล์ผลลัพธ์

- `/home/kali/reports/dec-ranker-guard-unknown-validation-2026-09-02/raw-curated/`
- `/media/sf_kali-share/dataset/dec-ranker-guard-unknown-validation-2026-09-02/`

## Merge Decision

- **Safe to merge**: 24/24
- **Quarantined**: 0
- **Next**: Run ML pipeline training with ranker guard unknown targets
