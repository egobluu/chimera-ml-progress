# Imported Scan Batch Curation

เอกสารนี้แยกข้อมูลหลัง import ว่า target ไหนพร้อมเข้า train จริง และ target ไหนควรใช้เป็น validation/recheck ก่อน

## Summary

| Item | Count |
| --- | ---: |
| Total rows | 51 |
| train_ready_strict | 30 |
| validation_only | 14 |
| needs_recheck | 7 |
| raw evidence folders | 34 |

## Runtime Categories

```json
{
  "known_positive": 15,
  "negative_control": 28,
  "unknown_family": 8
}
```

## แปลแบบง่าย

- `train_ready_strict`: มี raw evidence จริง, label ไม่พัง, runtime strict ผ่าน ใช้ train/validation ได้หลังคนตรวจ raw
- `validation_only`: runtime ผ่าน แต่ raw evidence ยังไม่ครบ ใช้ทดสอบ regression ได้ก่อน อย่าเพิ่ง train
- `needs_recheck`: ข้อมูลหายหรือ runtime ไม่ผ่าน ต้องกลับไปสแกน/แก้ label

## Targets

| Target | Split | Category | Runtime family | Reasons |
| --- | --- | --- | --- | --- |
| `grafana_cve_2021_43798_positive_001` | `needs_recheck` | `known_positive` | `grafana` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; runtime strict flow failed; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `grafana_negative_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `redis_lua_positive_001` | `needs_recheck` | `known_positive` | `redis` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; runtime strict flow failed; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `redis_negative_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `tomcat_put_positive_001` | `needs_recheck` | `known_positive` | `tomcat_put` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; runtime strict flow failed; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `tomcat_put_negative_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `tomcat_ajp_positive_001` | `needs_recheck` | `known_positive` | `tomcat_ajp` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; runtime strict flow failed; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `tomcat_ajp_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `couchdb_positive_001` | `needs_recheck` | `known_positive` | `couchdb_auth` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; runtime strict flow failed; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `couchdb_negative_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `solr_velocity_positive_001` | `needs_recheck` | `known_positive` | `solr_velocity` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; runtime strict flow failed; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `solr_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `shiro_positive_001` | `needs_recheck` | `known_positive` | `shiro_key` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; runtime strict flow failed; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `shiro_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `thinkphp_positive_001` | `train_ready_strict` | `known_positive` | `thinkphp_rce` | raw evidence present and runtime strict flow passed |
| `thinkphp_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `jenkins_positive_001` | `train_ready_strict` | `known_positive` | `jenkins` | raw evidence present and runtime strict flow passed |
| `jenkins_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `elasticsearch_positive_001` | `train_ready_strict` | `known_positive` | `elasticsearch` | raw evidence present and runtime strict flow passed |
| `elasticsearch_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `drupal_positive_001` | `train_ready_strict` | `unknown_family` | `unknown` | raw evidence present and runtime strict flow passed |
| `jboss_positive_001` | `train_ready_strict` | `unknown_family` | `unknown` | raw evidence present and runtime strict flow passed |
| `jetty_positive_001` | `train_ready_strict` | `unknown_family` | `unknown` | raw evidence present and runtime strict flow passed |
| `laravel_positive_001` | `validation_only` | `unknown_family` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive |
| `wordpress_positive_001` | `train_ready_strict` | `unknown_family` | `unknown` | raw evidence present and runtime strict flow passed |
| `php_cgi_positive_001` | `train_ready_strict` | `unknown_family` | `unknown` | raw evidence present and runtime strict flow passed |
| `flask_positive_001` | `validation_only` | `known_positive` | `flask` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive |
| `struts2_positive_001` | `train_ready_strict` | `known_positive` | `struts2` | raw evidence present and runtime strict flow passed |
| `nexus_positive_001` | `train_ready_strict` | `known_positive` | `nexus` | raw evidence present and runtime strict flow passed |
| `joomla_positive_001` | `validation_only` | `known_positive` | `joomla` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive |
| `nextjs_positive_001` | `validation_only` | `known_positive` | `nextjs` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `nginx_negative_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `mysql_negative_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `phpmyadmin_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `aria2_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `nacos_positive_001` | `validation_only` | `unknown_family` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `spring_positive_001` | `validation_only` | `unknown_family` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `redis_weak_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive |
| `grafana_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `tomcat_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `couchdb_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `solr_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `shiro_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `jenkins_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `elasticsearch_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `flask_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `nginx_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `mysql_weak_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `redis_auth_negative_001` | `validation_only` | `negative_control` | `unknown` | not listed in safe-to-merge-targets.txt; non-standard validation status: inconclusive; missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `grafana_auth_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `tomcat_auth_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
