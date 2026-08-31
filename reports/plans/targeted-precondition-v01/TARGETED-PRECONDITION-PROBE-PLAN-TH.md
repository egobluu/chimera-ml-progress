# Targeted Precondition Probe Plan

- threshold used: 0.1
- probe tasks: 60
- false positive targets: 20
- false negative targets: 0
- families covered: aria2, couchdb, elasticsearch, generic, grafana, jenkins, nexus, nginx, phpmyadmin, redis, shiro, solr, spring, thinkphp, tomcat

## ทำไมต้องทำรอบนี้

Light backfill รอบก่อนเพิ่มข้อมูลจาก `whatweb`, `curl`, และ `ffuf` แล้ว แต่ `strict_precheck` ยัง false positive 20 ตัวเมื่อเลือก threshold แบบไม่ยอมให้ false negative เกิด แปลว่า generic scan ยังไม่พอ ต้องเก็บ precondition ที่ผูกกับ exploit family โดยตรง

## Target ที่ควรเริ่มก่อน

- `aria2_non_vulnerable`
- `couchdb_non_vulnerable`
- `couchdb_v3_non_vulnerable`
- `elasticsearch_non_vulnerable`
- `generic_php_non_vulnerable`
- `grafana_non_vulnerable`
- `grafana_v9_non_vulnerable`
- `jenkins_non_vulnerable`
- `jetty_non_vulnerable`
- `nexus_non_vulnerable`
- `nginx_121_non_vulnerable`
- `nginx_non_vulnerable`

## Probe ที่ต้องเก็บ

| priority | target | family | failure | probe | expected feature |
| ---: | --- | --- | --- | --- | --- |
| 1 | `aria2_non_vulnerable` | `aria2` | `false_positive` | aria2_version_probe | `version_patched/version_in_vulnerable_range_true` |
| 2 | `aria2_non_vulnerable` | `aria2` | `false_positive` | aria2_auth_probe | `auth_required/no_auth_required` |
| 3 | `aria2_non_vulnerable` | `aria2` | `false_positive` | aria2_endpoint_probe | `endpoint_reachable_count/endpoint_missing_count` |
| 4 | `couchdb_non_vulnerable` | `couchdb` | `false_positive` | couchdb_root_info | `version_patched/version_in_vulnerable_range_true` |
| 5 | `couchdb_non_vulnerable` | `couchdb` | `false_positive` | couchdb_admin_party | `admin_party_enabled/auth_required` |
| 6 | `couchdb_non_vulnerable` | `couchdb` | `false_positive` | couchdb_config_access | `config_accessible/config_blocked` |
| 7 | `couchdb_v3_non_vulnerable` | `couchdb` | `false_positive` | couchdb_root_info | `version_patched/version_in_vulnerable_range_true` |
| 8 | `couchdb_v3_non_vulnerable` | `couchdb` | `false_positive` | couchdb_admin_party | `admin_party_enabled/auth_required` |
| 9 | `couchdb_v3_non_vulnerable` | `couchdb` | `false_positive` | couchdb_config_access | `config_accessible/config_blocked` |
| 10 | `elasticsearch_non_vulnerable` | `elasticsearch` | `false_positive` | es_version | `version_patched/version_in_vulnerable_range_true` |
| 11 | `elasticsearch_non_vulnerable` | `elasticsearch` | `false_positive` | es_script_behavior | `painless_sandbox_blocks/script_enabled` |
| 12 | `elasticsearch_non_vulnerable` | `elasticsearch` | `false_positive` | es_auth_behavior | `auth_required/no_auth_required` |
| 13 | `generic_php_non_vulnerable` | `generic` | `false_positive` | generic_version_probe | `version_patched/version_in_vulnerable_range_true` |
| 14 | `generic_php_non_vulnerable` | `generic` | `false_positive` | generic_auth_probe | `auth_required/no_auth_required` |
| 15 | `generic_php_non_vulnerable` | `generic` | `false_positive` | generic_endpoint_probe | `endpoint_reachable_count/endpoint_missing_count` |
| 16 | `grafana_non_vulnerable` | `grafana` | `false_positive` | grafana_health_version | `grafana_version_detected/version_patched` |
| 17 | `grafana_non_vulnerable` | `grafana` | `false_positive` | grafana_traversal_probe | `path_traversal_blocked/path_traversal_possible` |
| 18 | `grafana_non_vulnerable` | `grafana` | `false_positive` | grafana_auth_behavior | `auth_required/no_auth_required` |
| 19 | `grafana_v9_non_vulnerable` | `grafana` | `false_positive` | grafana_health_version | `grafana_version_detected/version_patched` |
| 20 | `grafana_v9_non_vulnerable` | `grafana` | `false_positive` | grafana_traversal_probe | `path_traversal_blocked/path_traversal_possible` |
| 21 | `grafana_v9_non_vulnerable` | `grafana` | `false_positive` | grafana_auth_behavior | `auth_required/no_auth_required` |
| 22 | `jenkins_non_vulnerable` | `jenkins` | `false_positive` | jenkins_version | `version_patched/version_in_vulnerable_range_true` |
| 23 | `jenkins_non_vulnerable` | `jenkins` | `false_positive` | jenkins_cli_or_script | `endpoint_reachable_count/auth_required` |
| 24 | `jenkins_non_vulnerable` | `jenkins` | `false_positive` | jenkins_auth_behavior | `auth_required/no_auth_required` |
| 25 | `jetty_non_vulnerable` | `generic` | `false_positive` | generic_version_probe | `version_patched/version_in_vulnerable_range_true` |
| 26 | `jetty_non_vulnerable` | `generic` | `false_positive` | generic_auth_probe | `auth_required/no_auth_required` |
| 27 | `jetty_non_vulnerable` | `generic` | `false_positive` | generic_endpoint_probe | `endpoint_reachable_count/endpoint_missing_count` |
| 28 | `nexus_non_vulnerable` | `nexus` | `false_positive` | nexus_version | `version_patched/version_in_vulnerable_range_true` |
| 29 | `nexus_non_vulnerable` | `nexus` | `false_positive` | nexus_anonymous_access | `anonymous_access/auth_required` |
| 30 | `nexus_non_vulnerable` | `nexus` | `false_positive` | nexus_endpoint_behavior | `endpoint_reachable_count/endpoint_missing_count` |
| 31 | `nginx_121_non_vulnerable` | `nginx` | `false_positive` | nginx_version | `version_patched/version_in_vulnerable_range_true` |
| 32 | `nginx_121_non_vulnerable` | `nginx` | `false_positive` | nginx_range_probe | `range_behavior_vulnerable/range_behavior_safe` |
| 33 | `nginx_121_non_vulnerable` | `nginx` | `false_positive` | nginx_default_paths | `endpoint_reachable_count/endpoint_missing_count` |
| 34 | `nginx_non_vulnerable` | `nginx` | `false_positive` | nginx_version | `version_patched/version_in_vulnerable_range_true` |
| 35 | `nginx_non_vulnerable` | `nginx` | `false_positive` | nginx_range_probe | `range_behavior_vulnerable/range_behavior_safe` |
| 36 | `nginx_non_vulnerable` | `nginx` | `false_positive` | nginx_default_paths | `endpoint_reachable_count/endpoint_missing_count` |
| 37 | `phpmyadmin_non_vulnerable` | `phpmyadmin` | `false_positive` | phpmyadmin_version | `version_patched/version_in_vulnerable_range_true` |
| 38 | `phpmyadmin_non_vulnerable` | `phpmyadmin` | `false_positive` | phpmyadmin_auth_behavior | `auth_required/no_auth_required` |
| 39 | `phpmyadmin_non_vulnerable` | `phpmyadmin` | `false_positive` | phpmyadmin_endpoint_presence | `endpoint_reachable_count/endpoint_missing_count` |
| 40 | `redis_auth_non_vulnerable` | `redis` | `false_positive` | redis_auth_required | `auth_required/no_auth_required` |
| 41 | `redis_auth_non_vulnerable` | `redis` | `false_positive` | redis_lua_available | `lua_available/lua_blocked` |
| 42 | `redis_auth_non_vulnerable` | `redis` | `false_positive` | redis_version | `version_patched/version_in_vulnerable_range_true` |
| 43 | `redis_non_vulnerable` | `redis` | `false_positive` | redis_auth_required | `auth_required/no_auth_required` |
| 44 | `redis_non_vulnerable` | `redis` | `false_positive` | redis_lua_available | `lua_available/lua_blocked` |
| 45 | `redis_non_vulnerable` | `redis` | `false_positive` | redis_version | `version_patched/version_in_vulnerable_range_true` |
| 46 | `shiro_non_vulnerable` | `shiro` | `false_positive` | shiro_rememberme_cookie | `rememberme_cookie_behavior` |
| 47 | `shiro_non_vulnerable` | `shiro` | `false_positive` | shiro_auth_page | `auth_required/no_auth_required` |
| 48 | `shiro_non_vulnerable` | `shiro` | `false_positive` | shiro_version_hint | `version_or_product_hint` |
| 49 | `solr_non_vulnerable` | `solr` | `false_positive` | solr_admin_reachable | `admin_path_found/admin_access_blocked` |
| 50 | `solr_non_vulnerable` | `solr` | `false_positive` | solr_velocity_enabled | `velocity_enabled/velocity_disabled` |
| 51 | `solr_non_vulnerable` | `solr` | `false_positive` | solr_core_discovered | `solr_core_found/solr_core_missing` |
| 52 | `spring_non_vulnerable` | `spring` | `false_positive` | spring_fingerprint | `spring_detected/spring_not_detected` |
| 53 | `spring_non_vulnerable` | `spring` | `false_positive` | spring_actuator | `actuator_path_found/actuator_path_missing` |
| 54 | `spring_non_vulnerable` | `spring` | `false_positive` | spring_classloader_probe | `spring_precondition_pass/spring_precondition_fail` |
| 55 | `thinkphp_non_vulnerable` | `thinkphp` | `false_positive` | thinkphp_invokefunction | `invokefunction_reachable/invokefunction_not_found` |
| 56 | `thinkphp_non_vulnerable` | `thinkphp` | `false_positive` | thinkphp_error_fingerprint | `thinkphp_detected/wrong_software_type` |
| 57 | `thinkphp_non_vulnerable` | `thinkphp` | `false_positive` | thinkphp_version_hint | `version_or_product_hint` |
| 58 | `tomcat_non_vulnerable` | `tomcat` | `false_positive` | tomcat_put_allowed | `method_put_allowed/method_put_rejected` |
| 59 | `tomcat_non_vulnerable` | `tomcat` | `false_positive` | tomcat_ajp_open | `ajp_port_open/ajp_port_closed` |
| 60 | `tomcat_non_vulnerable` | `tomcat` | `false_positive` | tomcat_version | `version_patched/version_in_vulnerable_range_true` |

## กฎสำคัญ

- ใช้เฉพาะ precheck probe ก่อนยิง exploit
- ห้ามใช้ Metasploit/manual PoC result เป็น input
- ห้ามรวมเป็น `negative_evidence_count` ก้อนเดียว
- ทุก probe ต้องมี `was_run`, `worked`, `timeout`, `missing`
- ผลที่ต้องการคือ feature ย่อย เช่น `method_put_rejected`, `auth_required`, `endpoint_missing`, `version_patched`
