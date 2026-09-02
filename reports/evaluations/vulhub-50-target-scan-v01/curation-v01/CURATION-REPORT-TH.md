# Imported Scan Batch Curation

เอกสารนี้แยกข้อมูลหลัง import ว่า target ไหนพร้อมเข้า train จริง และ target ไหนควรใช้เป็น validation/recheck ก่อน

## Summary

| Item | Count |
| --- | ---: |
| Total rows | 51 |
| train_ready_strict | 14 |
| validation_only | 37 |
| needs_recheck | 0 |
| raw evidence folders | 14 |

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
| `grafana_cve_2021_43798_positive_001` | `train_ready_strict` | `known_positive` | `grafana` | raw evidence present and runtime strict flow passed |
| `grafana_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `redis_lua_positive_001` | `train_ready_strict` | `known_positive` | `redis` | raw evidence present and runtime strict flow passed |
| `redis_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `tomcat_put_positive_001` | `train_ready_strict` | `known_positive` | `tomcat_put` | raw evidence present and runtime strict flow passed |
| `tomcat_put_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `tomcat_ajp_positive_001` | `train_ready_strict` | `known_positive` | `tomcat_ajp` | raw evidence present and runtime strict flow passed |
| `tomcat_ajp_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `couchdb_positive_001` | `train_ready_strict` | `known_positive` | `couchdb_auth` | raw evidence present and runtime strict flow passed |
| `couchdb_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `solr_velocity_positive_001` | `train_ready_strict` | `known_positive` | `solr_velocity` | raw evidence present and runtime strict flow passed |
| `solr_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `shiro_positive_001` | `train_ready_strict` | `known_positive` | `shiro_key` | raw evidence present and runtime strict flow passed |
| `shiro_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `thinkphp_positive_001` | `validation_only` | `known_positive` | `thinkphp_rce` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `thinkphp_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `jenkins_positive_001` | `validation_only` | `known_positive` | `jenkins` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `jenkins_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `elasticsearch_positive_001` | `validation_only` | `known_positive` | `elasticsearch` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `elasticsearch_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `drupal_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `jboss_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `jetty_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `laravel_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `wordpress_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `php_cgi_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `flask_positive_001` | `validation_only` | `known_positive` | `flask` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `struts2_positive_001` | `validation_only` | `known_positive` | `struts2` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `nexus_positive_001` | `validation_only` | `known_positive` | `nexus` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `joomla_positive_001` | `validation_only` | `known_positive` | `joomla` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `nextjs_positive_001` | `validation_only` | `known_positive` | `nextjs` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `nginx_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `mysql_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `phpmyadmin_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `aria2_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `nacos_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `spring_positive_001` | `validation_only` | `unknown_family` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `redis_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `grafana_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `tomcat_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `couchdb_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `solr_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `shiro_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `jenkins_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `elasticsearch_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `flask_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `nginx_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `mysql_weak_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `redis_auth_negative_001` | `train_ready_strict` | `negative_control` | `unknown` | raw evidence present and runtime strict flow passed |
| `grafana_auth_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
| `tomcat_auth_negative_001` | `validation_only` | `negative_control` | `unknown` | missing raw evidence folder; scanner report mentioned missing images; raw evidence required before train |
