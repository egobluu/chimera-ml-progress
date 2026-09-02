# Priority Report

รายงานนี้สร้างจาก runtime prediction ที่มีอยู่แล้วบนเครื่อง 2 ไม่ได้สแกน target ใหม่

## Summary

| กลุ่ม | จำนวน | ความหมาย |
| --- | ---: | --- |
| ready_for_safe_verification | 17 | มีหลักฐานพอสำหรับ safe verification หลังคนอนุมัติ |
| manual_triage_before_exploit | 2 | มีสัญญาณบวกแต่ยังต้องให้คนตรวจ |
| unknown_family_triage | 9 | น่าตรวจต่อแต่ family ไม่อยู่ใน model หรือ guard ไม่ให้เชื่อ Ranker |
| needs_more_evidence | 6 | ยังต้องเก็บ precheck เพิ่ม |
| do_not_exploit_now | 22 | ตอนนี้ไม่ควรตรวจ exploit path นี้ |

## Top Ready Targets

| target | decision | top family | CVE candidates | next action |
| --- | --- | --- | --- | --- |
| `redis_positive_unseen_01` | `ready_for_safe_verification` | `redis` | `CVE-2022-0543` | `run_safe_metasploit_check_or_manual_probe` |
| `grafana_positive_unseen_01` | `ready_for_safe_verification` | `grafana` | `CVE-2021-43798` | `run_safe_metasploit_check_or_manual_probe` |
| `tomcat_put_positive_unseen_01` | `ready_for_safe_verification` | `tomcat_put` | `CVE-2017-12615` | `run_safe_metasploit_check_or_manual_probe` |
| `tomcat_ajp_positive_unseen_01` | `ready_for_safe_verification` | `tomcat_ajp` | `CVE-2020-1938` | `run_safe_metasploit_check_or_manual_probe` |
| `couchdb_positive_unseen_01` | `ready_for_safe_verification` | `couchdb_auth` | `CVE-2017-12635` | `run_safe_metasploit_check_or_manual_probe` |
| `redis_positive_unseen_02` | `ready_for_safe_verification` | `redis` | `CVE-2022-0543` | `run_safe_metasploit_check_or_manual_probe` |
| `grafana_positive_unseen_02` | `ready_for_safe_verification` | `grafana` | `CVE-2021-43798` | `run_safe_metasploit_check_or_manual_probe` |
| `tomcat_put_positive_unseen_02` | `ready_for_safe_verification` | `tomcat_put` | `CVE-2017-12615` | `run_safe_metasploit_check_or_manual_probe` |
| `tomcat_ajp_positive_unseen_02` | `ready_for_safe_verification` | `tomcat_ajp` | `CVE-2020-1938` | `run_safe_metasploit_check_or_manual_probe` |
| `couchdb_positive_unseen_02` | `ready_for_safe_verification` | `couchdb_auth` | `CVE-2017-12635` | `run_safe_metasploit_check_or_manual_probe` |
| `solr_positive_unseen_03` | `ready_for_safe_verification` | `solr_velocity` | `CVE-2019-17558;CVE-2017-12629` | `run_safe_metasploit_check_or_manual_probe` |
| `redis_positive_guard_01` | `ready_for_safe_verification` | `redis` | `CVE-2022-0543` | `run_safe_metasploit_check_or_manual_probe` |
| `grafana_positive_guard_01` | `ready_for_safe_verification` | `grafana` | `CVE-2021-43798` | `run_safe_metasploit_check_or_manual_probe` |
| `solr_positive_guard_01` | `ready_for_safe_verification` | `solr_velocity` | `CVE-2019-17558;CVE-2017-12629` | `run_safe_metasploit_check_or_manual_probe` |
| `tomcat_put_positive_guard_01` | `ready_for_safe_verification` | `tomcat_put` | `CVE-2017-12615` | `run_safe_metasploit_check_or_manual_probe` |
| `tomcat_ajp_positive_guard_01` | `ready_for_safe_verification` | `tomcat_ajp` | `CVE-2020-1938` | `run_safe_metasploit_check_or_manual_probe` |
| `couchdb_positive_guard_01` | `ready_for_safe_verification` | `couchdb_auth` | `CVE-2017-12635` | `run_safe_metasploit_check_or_manual_probe` |

## Unknown-family Queue

| target | decision | top family | CVE candidates | next action |
| --- | --- | --- | --- | --- |
| `drupal_unknown_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `jboss_unknown_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `jetty_unknown_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `drupal_guard_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `laravel_guard_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `jetty_guard_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `wordpress_guard_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `php_cgi_guard_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |
| `jboss_guard_01` | `unknown_family_triage` | `nextjs` | `none` | `unknown_family_scan_more_or_manual_triage` |

## Manual/More Evidence Queue

| target | decision | top family | CVE candidates | next action |
| --- | --- | --- | --- | --- |
| `jenkins_unknown_01` | `manual_triage_before_exploit` | `jenkins` | `none` | `manual_triage_before_exploit` |
| `elasticsearch_unknown_01` | `manual_triage_before_exploit` | `elasticsearch` | `none` | `manual_triage_before_exploit` |
| `redis_weak_guard_01` | `needs_more_evidence` | `none` | `none` | `stop_or_collect_more_evidence` |
| `redis_negative_unseen_01` | `needs_more_evidence` | `none` | `none` | `stop_or_collect_more_evidence` |
| `redis_negative_unseen_02` | `needs_more_evidence` | `none` | `none` | `stop_or_collect_more_evidence` |
| `redis_negative_guard_01` | `needs_more_evidence` | `none` | `none` | `stop_or_collect_more_evidence` |
| `couchdb_negative_unseen_01` | `needs_more_evidence` | `none` | `none` | `stop_or_collect_more_evidence` |
| `grafana_weak_guard_01` | `needs_more_evidence` | `none` | `none` | `stop_or_collect_more_evidence` |

## Safety Note

`ready_for_safe_verification` ไม่ได้แปลว่ายิง exploit ได้ทันที ต้องใช้เฉพาะ safe check/manual non-destructive probe และต้องมี human approval
