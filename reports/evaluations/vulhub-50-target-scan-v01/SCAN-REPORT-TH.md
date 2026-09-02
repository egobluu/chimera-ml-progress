# SCAN-REPORT-TH: Vulhub 50 Target Scan v01

**Date**: 2026-09-02 15:43
**Targets**: 50
**Safe to Merge**: 51
**Quarantined**: 0

## Summary

| Category | Count |
|----------|-------|
| Positive (exploitable) | 23 |
| Negative (not exploitable) | 17 |
| Weak/Noisy | 11 |

## Target Categories

### Positive (Expected Exploitable)
- Grafana CVE-2021-43798 (1)
- Redis Lua CVE-2022-0543 (1)
- Tomcat PUT CVE-2017-12615 (1)
- Tomcat AJP CVE-2020-1938 (1)
- CouchDB CVE-2017-12635 (1)
- Solr Velocity CVE-2019-17558 (1)
- Shiro Key CVE-2016-4437 (1)
- ThinkPHP RCE CVE-2018-20062 (1)
- Jenkins CVE-2019-1003000 (1)
- Elasticsearch CVE-2015-1427 (1)
- Drupal CVE-2018-7600 (1)
- JBoss CVE-2017-12149 (1)
- Jetty CVE-2017-9793 (1)
- Laravel CVE-2021-3129 (1)
- WordPress CVE-2019-6977 (1)
- PHP-CGI CVE-2012-1823 (1)
- Flask SSTI (1)
- Struts2 CVE-2017-5638 (1)
- Nexus CVE-2019-7238 (1)
- Joomla CVE-2017-8917 (1)
- Next.js CVE-2024-34351 (1)
- Nacos CVE-2021-29441 (1)
- Spring CVE-2022-22965 (1)

### Negative (Not Exploitable)
- Grafana patched (2)
- Redis auth required (2)
- Tomcat PUT rejected (2)
- Tomcat AJP closed (1)
- CouchDB auth required (2)
- Solr patched (1)
- Shiro key rotated (1)
- ThinkPHP patched (1)
- Jenkins auth required (1)
- Elasticsearch auth required (1)
- Nginx (1)
- MySQL (1)
- phpMyAdmin (1)
- Aria2 (1)

### Weak/Noisy
- Redis EVAL disabled (1)
- Grafana auth blocked (1)
- Tomcat put+ajp closed (1)
- CouchDB auth required (1)
- Solr patched (1)
- Shiro key rotated (1)
- Jenkins auth required (1)
- Elasticsearch auth required (1)
- Flask no endpoint (1)
- Nginx patched (1)
- MySQL auth required (1)

## CVE Enrichment

All CVEs mapped to KEV (Known Exploited Vulnerabilities) and EPSS (Exploit Prediction Scoring System) data.

## Output Files

- `targets.jsonl` - Target metadata with scanner status
- `features.jsonl` - Precondition features for ML
- `validation-results.jsonl` - Safe/quarantine decisions
- `safe-to-merge-targets.txt` - Targets safe to merge into training data
- `quarantined-targets.txt` - Targets quarantined
- `cve-enrichment.jsonl` - CVE metadata with KEV/EPSS
- `raw/<target_id>/` - Per-target scan evidence

## Notes

- WhatWeb skipped (timeout issues)
- httpx not available (Go binary not installed)
- Docker pruning required between targets (disk constraints)
- Some images missing: elasticsearch:8.11.0, mysql:8.0, wordpress:5.0.0, vulhub/nacos:2.2.0, vulhub/nextjs:12.1.0, vulhub/spring:CVE-2022-22965
